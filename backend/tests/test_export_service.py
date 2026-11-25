"""Çoklu format dışa aktarma motoru (Markdown, CSV, JSON) birim testleri."""

import csv
import io
import json
from datetime import datetime, timezone

from app.models.analysis import (
    AcceptanceCriterion,
    AnalysisSession,
    Requirement,
    UserStory,
)
from app.services.export_service import (
    build_export_payload,
    export_to_csv,
    export_to_json,
    export_to_markdown,
    slugify_filename,
)


def _build_sample_session() -> AnalysisSession:
    """Özel karakterler (virgül, tırnak, pipe, Türkçe harfler) içeren örnek oturum oluşturur."""
    now = datetime(2026, 11, 25, 10, 30, tzinfo=timezone.utc)
    session = AnalysisSession(
        id=7,
        title="Öğrenci Staj & İş Akışı Çözümü",
        raw_input="Öğrenciler staj başvurularını hızlı ve güvenli biçimde gönderebilsin.",
        summary="Staj başvuru ve danışman onay süreçlerini yöneten platform.",
        source_mode="llm",
        created_at=now,
        updated_at=now,
    )

    fr = Requirement(
        id=101,
        session_id=7,
        code="FR-01",
        req_type="functional",
        category="Başvuru | Onay",
        title="Başvuru, Düzenleme ve \"Onay\" Akışı",
        description="Öğrenci belge yükler, danışman \"Onay\" veya red verir.\nDurum bildirimle iletilir.",
        moscow_priority="Must",
        ambiguity_warning=None,
    )
    nfr = Requirement(
        id=102,
        session_id=7,
        code="NFR-01",
        req_type="non_functional",
        category="Performans",
        title="Hızlı Yanıt Beklentisi",
        description="Listeleme ekranı en fazla 500 ms içinde açılmalıdır.",
        moscow_priority="Should",
        ambiguity_warning="Muğlak ifade ('hızlı'): Maksimum eşzamanlı kullanıcı sayısı belirtilmelidir.",
    )
    session.requirements = [fr, nfr]

    story = UserStory(
        id=201,
        session_id=7,
        requirement_id=101,
        code="US-01",
        related_requirement_code="FR-01",
        role="Öğrenci",
        goal="staj evraklarını yükleyip durumu izleyebilmek",
        benefit="onay sürecini gecikmeden tamamlayabilirim",
    )
    story.acceptance_criteria = [
        AcceptanceCriterion(
            id=301,
            user_story_id=201,
            code="AC-01.1",
            given_clause="Öğrenci sisteme giriş yapmıştır",
            when_clause="PDF dosyasını yükleyip Gönder'e bastığında",
            then_clause="Başvuru kaydedilir ve danışmana bildirim gider",
        )
    ]
    session.user_stories = [story]
    return session


def test_slugify_filename_produces_ascii_safe_names() -> None:
    """Türkçe ve özel karakterli başlıkların HTTP Header uyumlu ASCII dosya adına dönüştüğünü doğrular."""
    filename = slugify_filename("Öğrenci Staj & İş Akışı Çözümü!", 7, "csv")
    assert filename == "reqsense-7-ogrenci-staj-is-akisi-cozumu.csv"
    filename.encode("latin-1")

    fallback = slugify_filename("!!!???", 3, ".md")
    assert fallback == "reqsense-3-analiz.md"


def test_export_to_markdown_contains_srs_sections_and_escaped_tables() -> None:
    """Markdown çıktısının SRS başlıklarını, kaçışlı tabloları, uyarıları ve BDD kriterlerini içerdiğini doğrular."""
    session = _build_sample_session()
    md = export_to_markdown(session)

    assert "# Öğrenci Staj & İş Akışı Çözümü — Yazılım Gereksinim Spesifikasyonu (SRS)" in md
    assert "## 1. Proje Özeti" in md
    assert "## 2. Fonksiyonel Gereksinimler (FR)" in md
    assert "## 3. Fonksiyonel Olmayan Gereksinimler (NFR)" in md
    assert "## 4. Belirsizlik ve Kalite Uyarıları" in md
    assert "## 5. Kullanıcı Hikâyeleri ve Kabul Kriterleri (Given-When-Then)" in md
    assert "Başvuru \\| Onay" in md
    assert "**NFR-01 (Hızlı Yanıt Beklentisi):**" in md
    assert "**Given** Öğrenci sisteme giriş yapmıştır" in md
    assert "**Then** Başvuru kaydedilir ve danışmana bildirim gider" in md


def test_export_to_csv_preserves_special_characters_rfc4180() -> None:
    """CSV çıktısının virgül, tırnak, satır sonu ve Türkçe karakterleri RFC 4180 uyumlu koruduğunu doğrular."""
    session = _build_sample_session()
    csv_text = export_to_csv(session)

    rows = list(csv.DictReader(io.StringIO(csv_text)))
    assert len(rows) == 3

    fr_row = rows[0]
    assert fr_row["Tip"] == "FR"
    assert fr_row["Kod"] == "FR-01"
    assert fr_row["Başlık / Özet"] == 'Başvuru, Düzenleme ve "Onay" Akışı'
    assert 'danışman "Onay" veya red verir.\nDurum bildirimle iletilir.' in fr_row["Açıklama"]

    us_row = rows[2]
    assert us_row["Tip"] == "User Story"
    assert us_row["İlişkili Kod"] == "FR-01"
    assert "AC-01.1: Given Öğrenci sisteme giriş yapmıştır" in us_row["Kabul Kriterleri (Given-When-Then)"]


def test_export_to_json_and_build_payload() -> None:
    """JSON çıktısının tam yapıyı koruduğunu ve build_export_payload çıktılarının doğru olduğunu doğrular."""
    session = _build_sample_session()
    raw_json = export_to_json(session)
    parsed = json.loads(raw_json)

    assert parsed["id"] == 7
    assert parsed["title"] == "Öğrenci Staj & İş Akışı Çözümü"
    assert len(parsed["requirements"]) == 2
    assert parsed["user_stories"][0]["acceptance_criteria"][0]["code"] == "AC-01.1"

    content_bytes, media_type, filename = build_export_payload(session, "json")
    assert media_type == "application/json; charset=utf-8"
    assert filename.endswith(".json")
    assert json.loads(content_bytes.decode("utf-8"))["id"] == 7
