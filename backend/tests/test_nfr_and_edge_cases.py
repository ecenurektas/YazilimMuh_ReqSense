"""NFR (Performans, Güvenilirlik, Taşınabilirlik, Güvenlik) ve uç durum testleri."""

import csv
import io
import json
import time
from collections.abc import Generator
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import Session, sessionmaker

import app.database as app_database
from app.config import Settings
from app.database import create_db_engine, get_db, init_db
from app.main import app
from app.routers.analyze import get_nlp_service
from app.services.nlp_service import NLPService


class _FailingNetworkInteractions:
    def create(self, **_kwargs: object) -> object:
        raise httpx.ConnectError("Bağlantı reddedildi")


class _FailingNetworkClient:
    def __init__(self) -> None:
        self.interactions = _FailingNetworkInteractions()


@pytest.fixture()
def isolated_client() -> Generator[tuple[TestClient, dict[str, object]], None, None]:
    """Bellek içi SQLite kullanan izole TestClient sağlar."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    state: dict[str, object] = {
        "nlp_service": NLPService(settings_obj=Settings(demo_mode=True, gemini_api_key=""))
    }

    def _override_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    def _override_nlp() -> NLPService:
        return state["nlp_service"]  # type: ignore[return-value]

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_nlp_service] = _override_nlp

    client = TestClient(app)
    try:
        yield client, state
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_lifespan_creates_sqlite_tables_and_persists_across_restarts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """NFR-04: Dosya tabanlı SQLite üzerinde lifespan tablo oluşturma ve kalıcılığı doğrular."""
    db_path = tmp_path / "portable_test.db"
    disk_engine = create_db_engine(f"sqlite:///{db_path.as_posix()}")
    disk_session_local = sessionmaker(autocommit=False, autoflush=False, bind=disk_engine)

    monkeypatch.setattr(app_database, "engine", disk_engine)
    monkeypatch.setattr(app_database, "SessionLocal", disk_session_local)
    app.dependency_overrides[get_nlp_service] = lambda: NLPService(
        settings_obj=Settings(demo_mode=True, gemini_api_key="")
    )

    try:
        with TestClient(app) as client:
            tables = set(inspect(disk_engine).get_table_names())
            assert {
                "analysis_sessions",
                "requirements",
                "user_stories",
                "acceptance_criteria",
            }.issubset(tables)

            created = client.post(
                "/api/analyze",
                json={
                    "title": "Taşınabilirlik Testi",
                    "raw_input": "Kullanıcılar verilerini yerel SQLite veritabanında güvenle saklayabilmelidir.",
                    "use_demo": True,
                },
            )
            assert created.status_code == 201
            session_id = created.json()["id"]

        # İkinci başlatmada (init_db idempotency) mevcut kayıt korunmalı
        with TestClient(app) as client_restarted:
            fetched = client_restarted.get(f"/api/sessions/{session_id}")
            assert fetched.status_code == 200
            assert fetched.json()["title"] == "Taşınabilirlik Testi"
    finally:
        app.dependency_overrides.clear()
        disk_engine.dispose()


def test_input_boundary_lengths_and_empty_body(
    isolated_client: tuple[TestClient, dict[str, object]],
) -> None:
    """FR-01 / NFR-03: 19/20 karakter raw_input ve 255/256 karakter title sınırlarını doğrular."""
    client, _state = isolated_client

    assert client.post("/api/analyze", json={}).status_code == 422
    assert (
        client.post("/api/analyze", json={"raw_input": "a" * 19, "use_demo": True}).status_code
        == 422
    )

    ok_min = client.post(
        "/api/analyze",
        json={"title": "A" * 255, "raw_input": "a" * 20, "use_demo": True},
    )
    assert ok_min.status_code == 201
    assert len(ok_min.json()["title"]) == 255

    too_long_title = client.post(
        "/api/analyze",
        json={"title": "A" * 256, "raw_input": "a" * 25, "use_demo": True},
    )
    assert too_long_title.status_code == 422


def test_partial_update_rename_and_empty_collections_export(
    isolated_client: tuple[TestClient, dict[str, object]],
) -> None:
    """Kısmi güncelleme, kod yeniden adlandırma ve boş koleksiyon dışa aktarımını doğrular."""
    client, _state = isolated_client

    created = client.post(
        "/api/analyze",
        json={
            "title": "Kısmi Güncelleme Projesi",
            "raw_input": "Sistem hızlı çalışsın ve kullanıcılar kolayca dışa aktarma yapabilsin.",
            "use_demo": True,
        },
    ).json()
    session_id = created["id"]

    # Yalnızca başlık güncellemesi mevcut alt kayıtları korumalı
    patch_title = client.put(
        f"/api/sessions/{session_id}",
        json={"title": "Sadece Başlık Güncellendi"},
    )
    assert patch_title.status_code == 200
    body = patch_title.json()
    assert body["title"] == "Sadece Başlık Güncellendi"
    assert len(body["requirements"]) == len(created["requirements"])
    assert len(body["user_stories"]) == len(created["user_stories"])

    # Boş summary temizlenmeli (None)
    clear_summary = client.put(
        f"/api/sessions/{session_id}",
        json={"summary": "   "},
    )
    assert clear_summary.status_code == 200
    assert clear_summary.json()["summary"] is None

    # Gereksinim kodu yeniden adlandırma (FR-01 -> FR-99) ve FK bağlantısı
    renamed_reqs = [
        {**req, "code": "FR-99"} if req["code"] == "FR-01" else req
        for req in body["requirements"]
    ]
    renamed_stories = [
        {**story, "related_requirement_code": "FR-99"}
        if story["related_requirement_code"] == "FR-01"
        else story
        for story in body["user_stories"]
    ]
    relink_resp = client.put(
        f"/api/sessions/{session_id}",
        json={"requirements": renamed_reqs, "user_stories": renamed_stories},
    )
    assert relink_resp.status_code == 200
    relinked = relink_resp.json()
    fr99 = next(r for r in relinked["requirements"] if r["code"] == "FR-99")
    us01 = next(s for s in relinked["user_stories"] if s["code"] == "US-01")
    assert us01["requirement_id"] == fr99["id"]

    # Boş gereksinim/hikâye listesiyle dışa aktarma çökmemeli
    cleared_resp = client.put(
        f"/api/sessions/{session_id}",
        json={"requirements": [], "user_stories": []},
    )
    assert cleared_resp.status_code == 200

    md_resp = client.get(f"/api/sessions/{session_id}/export?format=md")
    assert md_resp.status_code == 200
    assert "kayıtlı gereksinim bulunmamaktadır" in md_resp.text.lower()

    csv_resp = client.get(f"/api/sessions/{session_id}/export?format=csv")
    assert csv_resp.status_code == 200
    assert list(csv.DictReader(io.StringIO(csv_resp.text))) == []

    json_resp = client.get(f"/api/sessions/{session_id}/export?format=json")
    assert json_resp.status_code == 200
    assert json.loads(json_resp.text)["requirements"] == []


def test_local_crud_and_export_meet_500ms_performance_nfr(
    isolated_client: tuple[TestClient, dict[str, object]],
) -> None:
    """NFR-01: Yerel listeleme, güncelleme ve dışa aktarma işlemlerinin 500 ms altında sürdüğünü doğrular."""
    client, _state = isolated_client

    created = client.post(
        "/api/analyze",
        json={
            "title": "Performans Ölçüm Oturumu",
            "raw_input": "Kullanıcılar belgeleri listeleyip hızlıca güncelleyebilmeli ve indirebilmelidir.",
            "use_demo": True,
        },
    ).json()
    session_id = created["id"]

    start = time.perf_counter()
    assert client.get("/api/sessions").status_code == 200
    assert (time.perf_counter() - start) < 0.5

    start = time.perf_counter()
    assert (
        client.put(f"/api/sessions/{session_id}", json={"title": "Hızlı Güncelleme"}).status_code
        == 200
    )
    assert (time.perf_counter() - start) < 0.5

    for fmt in ("md", "csv", "json"):
        start = time.perf_counter()
        assert client.get(f"/api/sessions/{session_id}/export?format={fmt}").status_code == 200
        assert (time.perf_counter() - start) < 0.5


def test_api_key_is_never_exposed_in_health_or_error_responses(
    isolated_client: tuple[TestClient, dict[str, object]],
) -> None:
    """NFR-05: Hassas API anahtarının /api/health veya 503 hata yanıtlarında sızmadığını doğrular."""
    client, state = isolated_client
    secret_key = "AIzaSy-SECRET-TEST-KEY-999"

    state["nlp_service"] = NLPService(
        settings_obj=Settings(demo_mode=False, gemini_api_key=secret_key),
        client=_FailingNetworkClient(),
    )

    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    assert secret_key not in health_resp.text
    assert "gemini_api_key" not in health_resp.text

    err_resp = client.post(
        "/api/analyze",
        json={"raw_input": "Güvenlik testi için yeterince uzun örnek gereksinim cümlesi."},
    )
    assert err_resp.status_code == 503
    assert secret_key not in err_resp.text
