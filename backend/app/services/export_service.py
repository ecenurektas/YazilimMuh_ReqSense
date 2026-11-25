"""Analiz oturumlarını Markdown (.md), CSV (.csv) ve JSON (.json) formatlarına dönüştüren motor."""

import csv
import io
import json
import re

from app.models.analysis import AnalysisSession, Requirement
from app.schemas.analysis import AnalysisSessionDetail, ExportFormat

_TURKISH_CHAR_MAP = str.maketrans(
    {
        "ç": "c",
        "Ç": "C",
        "ğ": "g",
        "Ğ": "G",
        "ı": "i",
        "İ": "I",
        "ö": "o",
        "Ö": "O",
        "ş": "s",
        "Ş": "S",
        "ü": "u",
        "Ü": "U",
    }
)

_CSV_HEADERS = [
    "Tip",
    "Kod",
    "İlişkili Kod",
    "Kategori / Rol",
    "Başlık / Özet",
    "Açıklama",
    "MoSCoW Önceliği",
    "Belirsizlik Uyarısı",
    "Kabul Kriterleri (Given-When-Then)",
]


def slugify_filename(title: str, session_id: int, ext: str) -> str:
    """Türkçe karakterleri ASCII'ye çevirerek HTTP Content-Disposition uyumlu dosya adı üretir."""
    ascii_title = title.translate(_TURKISH_CHAR_MAP).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title).strip("-")[:48].strip("-")
    if not slug:
        slug = "analiz"
    clean_ext = ext.lstrip(".")
    return f"reqsense-{session_id}-{slug}.{clean_ext}"


def _escape_md_cell(value: str | None) -> str:
    """Markdown tablo hücresi için pipe ve satır sonlarını güvenli biçimde temizler."""
    if not value:
        return "-"
    return value.replace("\r\n", " ").replace("\n", " ").replace("|", "\\|").strip()


def _format_requirement_table(requirements: list[Requirement]) -> list[str]:
    """Gereksinim listesini Markdown tablosu satırlarına dönüştürür."""
    if not requirements:
        return ["_Bu kategoride kayıtlı gereksinim bulunmamaktadır._", ""]

    lines = [
        "| Kod | Kategori | Başlık | Açıklama | MoSCoW | Belirsizlik Uyarısı |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for req in requirements:
        lines.append(
            "| "
            + " | ".join(
                [
                    _escape_md_cell(req.code),
                    _escape_md_cell(req.category),
                    _escape_md_cell(req.title),
                    _escape_md_cell(req.description),
                    _escape_md_cell(req.moscow_priority),
                    _escape_md_cell(req.ambiguity_warning),
                ]
            )
            + " |"
        )
    lines.append("")
    return lines


def export_to_markdown(session: AnalysisSession) -> str:
    """Oturumu SRS (Software Requirements Specification) taslağı biçiminde Markdown'a dönüştürür."""
    created_str = session.created_at.strftime("%Y-%m-%d %H:%M UTC")
    source_label = "Demo Modu (Çevrimdışı)" if session.source_mode == "demo" else "Gemini Yapay Zekâ"

    functional_reqs = [r for r in session.requirements if r.req_type == "functional"]
    non_functional_reqs = [r for r in session.requirements if r.req_type == "non_functional"]
    ambiguous_reqs = [r for r in session.requirements if r.ambiguity_warning]

    lines = [
        f"# {session.title} — Yazılım Gereksinim Spesifikasyonu (SRS)",
        "",
        f"- **Oturum No:** #{session.id}",
        f"- **Oluşturulma Tarihi:** {created_str}",
        f"- **Analiz Kaynağı:** {source_label}",
        "",
        "## 1. Proje Özeti",
        "",
        session.summary or "Özet belirtilmemiş.",
        "",
        "## 2. Fonksiyonel Gereksinimler (FR)",
        "",
        *_format_requirement_table(functional_reqs),
        "## 3. Fonksiyonel Olmayan Gereksinimler (NFR)",
        "",
        *_format_requirement_table(non_functional_reqs),
        "## 4. Belirsizlik ve Kalite Uyarıları",
        "",
    ]

    if ambiguous_reqs:
        for req in ambiguous_reqs:
            lines.append(f"- **{req.code} ({req.title}):** {req.ambiguity_warning}")
    else:
        lines.append("_Belirsizlik uyarısı tespit edilen gereksinim bulunmamaktadır._")
    lines.append("")

    lines.extend(["## 5. Kullanıcı Hikâyeleri ve Kabul Kriterleri (Given-When-Then)", ""])
    if not session.user_stories:
        lines.append("_Kayıtlı kullanıcı hikâyesi bulunmamaktadır._")
    else:
        for story in session.user_stories:
            related_suffix = (
                f" *(İlişkili: {story.related_requirement_code})*"
                if story.related_requirement_code
                else ""
            )
            lines.append(f"### {story.code}{related_suffix}")
            lines.append("")
            lines.append(
                f"> **Bir** {story.role} **olarak**, {story.goal} **istiyorum**; "
                f"**böylece** {story.benefit}."
            )
            lines.append("")
            if story.acceptance_criteria:
                for ac in story.acceptance_criteria:
                    lines.append(f"- **{ac.code}:**")
                    lines.append(f"  - **Given** {ac.given_clause}")
                    lines.append(f"  - **When** {ac.when_clause}")
                    lines.append(f"  - **Then** {ac.then_clause}")
            else:
                lines.append("- _Kabul kriteri eklenmemiş._")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def export_to_csv(session: AnalysisSession) -> str:
    """Oturumdaki gereksinim ve kullanıcı hikâyelerini RFC 4180 uyumlu UTF-8 CSV'ye dönüştürür."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(_CSV_HEADERS)

    for req in session.requirements:
        req_label = "FR" if req.req_type == "functional" else "NFR"
        writer.writerow(
            [
                req_label,
                req.code,
                "",
                req.category or "",
                req.title,
                req.description,
                req.moscow_priority,
                req.ambiguity_warning or "",
                "",
            ]
        )

    for story in session.user_stories:
        criteria_lines = [
            f"{ac.code}: Given {ac.given_clause} | When {ac.when_clause} | Then {ac.then_clause}"
            for ac in story.acceptance_criteria
        ]
        writer.writerow(
            [
                "User Story",
                story.code,
                story.related_requirement_code or "",
                story.role,
                f"Bir {story.role} olarak {story.goal}",
                f"Böylece {story.benefit}",
                "",
                "",
                "\n".join(criteria_lines),
            ]
        )

    return buffer.getvalue()


def export_to_json(session: AnalysisSession) -> str:
    """Oturum detaylarını yapılandırılmış UTF-8 JSON metnine dönüştürür."""
    detail = AnalysisSessionDetail.model_validate(session)
    return json.dumps(detail.model_dump(mode="json"), ensure_ascii=False, indent=2)


def build_export_payload(
    session: AnalysisSession,
    export_format: ExportFormat,
) -> tuple[bytes, str, str]:
    """İstenen format için (bytes, media_type, ascii_filename) üçlüsünü üretir."""
    if export_format == "md":
        content = export_to_markdown(session)
        media_type = "text/markdown; charset=utf-8"
    elif export_format == "csv":
        content = export_to_csv(session)
        media_type = "text/csv; charset=utf-8"
    elif export_format == "json":
        content = export_to_json(session)
        media_type = "application/json; charset=utf-8"
    else:
        raise ValueError(f"Desteklenmeyen dışa aktarma formatı: {export_format}")

    filename = slugify_filename(session.title, session.id, export_format)
    return content.encode("utf-8"), media_type, filename
