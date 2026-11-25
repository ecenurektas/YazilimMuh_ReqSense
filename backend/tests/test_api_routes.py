"""FastAPI REST API uç noktaları, hata yönetimi ve uçtan uca entegrasyon testleri."""

import csv
import io
import json
from collections.abc import Generator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.database import create_db_engine, get_db, init_db
from app.main import app
from app.routers.analyze import get_nlp_service
from app.services.exceptions import (
    LLMConfigurationError,
    LLMOutputParseError,
    LLMProviderError,
)
from app.services.nlp_service import NLPService


class _FakeInteractionsAPI:
    def __init__(self, output_text: str) -> None:
        self._output_text = output_text

    def create(self, **_kwargs: object) -> object:
        return SimpleNamespace(output_text=self._output_text)


class _FakeGeminiClient:
    def __init__(self, output_text: str) -> None:
        self.interactions = _FakeInteractionsAPI(output_text)


def _mock_llm_payload() -> dict[str, object]:
    return {
        "project_title": "Akıllı Randevu ve Takip Sistemi",
        "summary": "Randevu oluşturma, düzenleme ve bildirim süreçlerini yöneten web uygulaması.",
        "requirements": [
            {
                "code": "FR-01",
                "req_type": "functional",
                "category": "Randevu Yönetimi",
                "title": "Çevrimiçi Randevu Oluşturma",
                "description": "Kullanıcılar uygun tarih ve saat seçerek yeni randevu oluşturabilmelidir.",
                "moscow_priority": "Must",
                "ambiguity_warning": None,
            },
            {
                "code": "NFR-01",
                "req_type": "non_functional",
                "category": "Performans",
                "title": "Hızlı Yanıt Süresi",
                "description": "Randevu listeleme sorguları 500 ms altında yanıt vermelidir.",
                "moscow_priority": "Should",
                "ambiguity_warning": "Muğlak ifade ('hızlı'): Beklenen eşzamanlı kullanıcı sayısı belirtilmelidir.",
            },
        ],
        "user_stories": [
            {
                "code": "US-01",
                "related_requirement_code": "FR-01",
                "role": "Danışan",
                "goal": "uygun bir saat dilimi seçerek randevu alabilmek",
                "benefit": "telefonla aramadan işlemlerimi tamamlayabilirim",
                "acceptance_criteria": [
                    {
                        "code": "AC-01.1",
                        "given_clause": "Danışan sisteme giriş yapmıştır ve müsait bir tarih seçmiştir",
                        "when_clause": "Randevuyu Onayla butonuna tıklandığında",
                        "then_clause": "Randevu kaydedilir ve onay mesajı görüntülenir",
                    }
                ],
            }
        ],
    }


@pytest.fixture()
def api_client() -> Generator[tuple[TestClient, dict[str, object]], None, None]:
    """İzole bellek içi SQLite ve değiştirilebilir NLP servisi ile TestClient sağlar."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    mock_json = json.dumps(_mock_llm_payload(), ensure_ascii=False)
    default_nlp = NLPService(
        settings_obj=Settings(
            demo_mode=False,
            gemini_api_key="test-key",
            gemini_model="gemini-4-hydrogen",
        ),
        client=_FakeGeminiClient(mock_json),
    )
    state: dict[str, object] = {"nlp_service": default_nlp}

    def _override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    def _override_get_nlp_service() -> NLPService:
        return state["nlp_service"]  # type: ignore[return-value]

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_nlp_service] = _override_get_nlp_service

    client = TestClient(app)
    try:
        yield client, state
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_post_analyze_creates_session_with_mock_llm_and_demo_mode(
    api_client: tuple[TestClient, dict[str, object]],
) -> None:
    """POST /api/analyze uç noktasının 201 ile kalıcı oturum döndürdüğünü doğrular."""
    client, state = api_client

    response = client.post(
        "/api/analyze",
        json={
            "title": "Randevu MVP",
            "raw_input": "Kullanıcılar çevrimiçi randevu oluşturabilsin ve sistem hızlı çalışsın.",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Randevu MVP"
    assert data["source_mode"] == "llm"
    assert data["requirement_count"] == 2
    assert data["user_story_count"] == 1
    assert data["ambiguity_count"] == 1
    assert data["user_stories"][0]["requirement_id"] == data["requirements"][0]["id"]

    state["nlp_service"] = NLPService(settings_obj=Settings(demo_mode=True, gemini_api_key=""))
    demo_resp = client.post(
        "/api/analyze",
        json={
            "raw_input": "Arayüz kullanıcı dostu olsun, veriler güvenli tutulsun ve CSV çıktısı alınsın.",
        },
    )
    assert demo_resp.status_code == 201
    demo_data = demo_resp.json()
    assert demo_data["source_mode"] == "demo"
    assert demo_data["requirement_count"] == 6
    assert demo_data["user_story_count"] == 3


def test_post_analyze_validation_error_returns_422_without_calling_nlp(
    api_client: tuple[TestClient, dict[str, object]],
) -> None:
    """Boş veya 20 karakterden kısa metinlerde NLP çağrılmadan 422 döndüğünü doğrular."""
    client, state = api_client
    called = False

    class _SpyNLPService:
        def analyze_text(self, *_args: object, **_kwargs: object) -> object:
            nonlocal called
            called = True
            raise AssertionError("Doğrulama hatasında NLP servisi çağrılmamalıdır.")

    state["nlp_service"] = _SpyNLPService()

    for bad_text in ("", "   ", "Kısa metin"):
        resp = client.post("/api/analyze", json={"raw_input": bad_text})
        assert resp.status_code == 422
        body = resp.json()
        assert body["error_code"] == "validation_error"
        assert "en az 20 karakter" in body["detail"]
        assert called is False


@pytest.mark.parametrize(
    ("exc", "expected_status", "expected_code"),
    [
        (LLMConfigurationError(), 503, "llm_not_configured"),
        (LLMProviderError("Zaman aşımı oluştu."), 503, "llm_provider_error"),
        (LLMOutputParseError(), 502, "llm_output_invalid"),
    ],
)
def test_post_analyze_maps_nlp_errors_to_http_status(
    api_client: tuple[TestClient, dict[str, object]],
    exc: Exception,
    expected_status: int,
    expected_code: str,
) -> None:
    """LLM yapılandırma, sağlayıcı ve ayrıştırma hatalarının 503/502 JSON yanıtına dönüştüğünü doğrular."""
    client, state = api_client

    class _FailingNLPService:
        def analyze_text(self, *_args: object, **_kwargs: object) -> object:
            raise exc

    state["nlp_service"] = _FailingNLPService()
    resp = client.post(
        "/api/analyze",
        json={"raw_input": "Bu girdi doğrulamayı geçmek için yeterince uzun bir metindir."},
    )
    assert resp.status_code == expected_status
    body = resp.json()
    assert body["error_code"] == expected_code
    assert body["detail"]


def test_session_list_detail_update_and_delete_lifecycle(
    api_client: tuple[TestClient, dict[str, object]],
) -> None:
    """GET/PUT/DELETE /api/sessions uç noktalarının tam yaşam döngüsünü ve 404 kontrolünü doğrular."""
    client, _state = api_client

    create_resp = client.post(
        "/api/analyze",
        json={
            "title": "İlk Oturum",
            "raw_input": "Kullanıcılar çevrimiçi randevu oluşturabilsin ve düzenleyebilsin.",
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    session_id = created["id"]

    list_resp = client.get("/api/sessions")
    assert list_resp.status_code == 200
    sessions = list_resp.json()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session_id
    assert sessions[0]["requirement_count"] == 2
    assert sessions[0]["user_story_count"] == 1
    assert sessions[0]["ambiguity_count"] == 1

    existing_fr = created["requirements"][0]
    existing_story = created["user_stories"][0]
    existing_ac = existing_story["acceptance_criteria"][0]

    update_payload = {
        "title": "Güncellenmiş Randevu Sistemi",
        "summary": "Güncellenen sistem özeti.",
        "requirements": [
            {
                "id": existing_fr["id"],
                "code": "FR-01",
                "req_type": "functional",
                "category": "Randevu",
                "title": "Güncel Randevu Oluşturma",
                "description": "Kullanıcı tarih ve saat seçerek randevu oluşturup iptal edebilir.",
                "moscow_priority": "Must",
                "ambiguity_warning": None,
            },
            {
                "code": "FR-02",
                "req_type": "functional",
                "category": "Bildirim",
                "title": "E-posta Hatırlatması",
                "description": "Randevudan 24 saat önce kullanıcıya hatırlatma e-postası gönderilir.",
                "moscow_priority": "Could",
                "ambiguity_warning": None,
            },
        ],
        "user_stories": [
            {
                "id": existing_story["id"],
                "code": "US-01",
                "related_requirement_code": "FR-01",
                "role": "Danışan",
                "goal": "randevumu düzenleyip iptal edebilmek",
                "benefit": "program değişikliklerimi kolayca yönetebilirim",
                "acceptance_criteria": [
                    {
                        "id": existing_ac["id"],
                        "code": "AC-01.1",
                        "given_clause": "Danışanın aktif bir randevusu vardır",
                        "when_clause": "İptal Et butonuna tıklandığında",
                        "then_clause": "Randevu iptal edilir ve saat dilimi yeniden açılır",
                    },
                    {
                        "code": "AC-01.2",
                        "given_clause": "Randevuya 1 saatten az süre kalmıştır",
                        "when_clause": "Danışan iptal etmeye çalıştığında",
                        "then_clause": "Sistem kural gereği iptal işlemini engeller",
                    },
                ],
            },
            {
                "code": "US-02",
                "related_requirement_code": "FR-02",
                "role": "Danışan",
                "goal": "randevu öncesi e-posta hatırlatması almak",
                "benefit": "randevularımı kaçırmam",
                "acceptance_criteria": [
                    {
                        "code": "AC-02.1",
                        "given_clause": "Yaklaşan onaylı bir randevu mevcuttur",
                        "when_clause": "Randevu saatine 24 saat kaldığında",
                        "then_clause": "Kayıtlı e-posta adresine hatırlatma gönderilir",
                    }
                ],
            },
        ],
    }

    put_resp = client.put(f"/api/sessions/{session_id}", json=update_payload)
    assert put_resp.status_code == 200
    updated = put_resp.json()
    assert updated["title"] == "Güncellenmiş Randevu Sistemi"
    assert updated["summary"] == "Güncellenen sistem özeti."
    assert len(updated["requirements"]) == 2
    assert updated["requirements"][0]["id"] == existing_fr["id"]
    assert updated["requirements"][1]["code"] == "FR-02"
    assert len(updated["user_stories"]) == 2
    assert len(updated["user_stories"][0]["acceptance_criteria"]) == 2
    assert updated["user_stories"][1]["requirement_id"] == updated["requirements"][1]["id"]

    # Kalıcılığı GET ile tekrar doğrula
    get_resp = client.get(f"/api/sessions/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Güncellenmiş Randevu Sistemi"
    assert get_resp.json()["requirement_count"] == 2
    assert get_resp.json()["user_story_count"] == 2
    assert get_resp.json()["ambiguity_count"] == 0

    # Geçersiz güncelleme (boş başlık -> 422)
    bad_put = client.put(f"/api/sessions/{session_id}", json={"title": "   "})
    assert bad_put.status_code == 422

    # Silme ve 404 kontrolü
    del_resp = client.delete(f"/api/sessions/{session_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    assert client.get(f"/api/sessions/{session_id}").status_code == 404
    assert client.put(f"/api/sessions/{session_id}", json={"title": "X"}).status_code == 404
    assert client.delete(f"/api/sessions/{session_id}").status_code == 404


def test_export_session_endpoints_and_errors(
    api_client: tuple[TestClient, dict[str, object]],
) -> None:
    """GET /api/sessions/{id}/export uç noktasının md/csv/json ve hata senaryolarını doğrular."""
    client, _state = api_client

    create_resp = client.post(
        "/api/analyze",
        json={
            "title": "Öğrenci Bilgi Sistemi Şablonu",
            "raw_input": "Öğrenciler ders kaydı yapabilsin ve transkriptlerini indirebilsin.",
        },
    )
    session_id = create_resp.json()["id"]

    md_resp = client.get(
        f"/api/sessions/{session_id}/export?format=md",
        headers={"Origin": "http://localhost:5173"},
    )
    assert md_resp.status_code == 200
    assert md_resp.headers["content-type"].startswith("text/markdown")
    assert "content-disposition" in md_resp.headers.get("access-control-expose-headers", "").lower()
    assert "attachment; filename=" in md_resp.headers["content-disposition"]
    assert ".md" in md_resp.headers["content-disposition"]
    assert "# Öğrenci Bilgi Sistemi Şablonu" in md_resp.text

    csv_resp = client.get(f"/api/sessions/{session_id}/export?format=csv")
    assert csv_resp.status_code == 200
    assert csv_resp.headers["content-type"].startswith("text/csv")
    assert ".csv" in csv_resp.headers["content-disposition"]
    csv_rows = list(csv.DictReader(io.StringIO(csv_resp.text)))
    assert len(csv_rows) == 3

    json_resp = client.get(f"/api/sessions/{session_id}/export?format=json")
    assert json_resp.status_code == 200
    assert json_resp.headers["content-type"].startswith("application/json")
    assert ".json" in json_resp.headers["content-disposition"]
    parsed_json = json.loads(json_resp.text)
    assert parsed_json["id"] == session_id
    assert parsed_json["title"] == "Öğrenci Bilgi Sistemi Şablonu"

    bad_format_resp = client.get(f"/api/sessions/{session_id}/export?format=xml")
    assert bad_format_resp.status_code == 422

    missing_resp = client.get("/api/sessions/99999/export?format=md")
    assert missing_resp.status_code == 404
    assert missing_resp.json()["error_code"] == "session_not_found"


def test_post_analyze_request_level_use_demo_fallback(
    api_client: tuple[TestClient, dict[str, object]],
) -> None:
    """DEMO_MODE=false ve API anahtarı boşken use_demo=true isteğinin başarılı demo analizi ürettiğini doğrular."""
    client, state = api_client
    state["nlp_service"] = NLPService(settings_obj=Settings(demo_mode=False, gemini_api_key=""))

    raw_text = "Sistem çok hızlı çalışsın, arayüz kullanıcı dostu olsun ve veriler güvenli tutulsun."
    fail_resp = client.post("/api/analyze", json={"raw_input": raw_text, "use_demo": False})
    assert fail_resp.status_code == 503
    assert fail_resp.json()["error_code"] == "llm_not_configured"

    demo_resp = client.post(
        "/api/analyze",
        json={"title": "İstek Bazlı Demo", "raw_input": raw_text, "use_demo": True},
    )
    assert demo_resp.status_code == 201
    body = demo_resp.json()
    assert body["title"] == "İstek Bazlı Demo"
    assert body["source_mode"] == "demo"
    assert body["requirement_count"] == 6
    assert body["user_story_count"] == 3


def test_multiple_sessions_history_ordering_update_and_selective_delete(
    api_client: tuple[TestClient, dict[str, object]],
) -> None:
    """Birden fazla oturumda listeleme sırası, güncelleme yansıması ve seçici silmeyi doğrular."""
    client, _state = api_client

    first = client.post(
        "/api/analyze",
        json={
            "title": "Birinci Proje",
            "raw_input": "Kullanıcılar temel gereksinim analizini başlatıp kaydedebilmelidir.",
            "use_demo": True,
        },
    ).json()
    second = client.post(
        "/api/analyze",
        json={
            "title": "İkinci Proje",
            "raw_input": "Yöneticiler onay bekleyen talepleri listeleyip dışa aktarabilmelidir.",
            "use_demo": True,
        },
    ).json()

    sessions = client.get("/api/sessions").json()
    assert [item["id"] for item in sessions] == [second["id"], first["id"]]

    # İlk oturumu güncelle (belirsizlik uyarısını temizle)
    cleaned_reqs = [
        {**req, "ambiguity_warning": None} for req in first["requirements"]
    ]
    put_resp = client.put(
        f"/api/sessions/{first['id']}",
        json={"title": "Birinci Proje (Revize)", "requirements": cleaned_reqs},
    )
    assert put_resp.status_code == 200

    sessions_after_put = client.get("/api/sessions").json()
    first_summary = next(item for item in sessions_after_put if item["id"] == first["id"])
    assert first_summary["title"] == "Birinci Proje (Revize)"
    assert first_summary["ambiguity_count"] == 0

    # İkinci oturumu sil; birinci oturum etkilenmeden kalmalı
    assert client.delete(f"/api/sessions/{second['id']}").status_code == 200
    remaining = client.get("/api/sessions").json()
    assert [item["id"] for item in remaining] == [first["id"]]
    assert client.get(f"/api/sessions/{first['id']}").status_code == 200
