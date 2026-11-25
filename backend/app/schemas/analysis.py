"""Pydantic istek/yanıt ve Gemini Structured Output şemaları."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

RequirementType = Literal["functional", "non_functional"]
MoscowPriority = Literal["Must", "Should", "Could", "Wont"]
SourceMode = Literal["llm", "demo"]
ExportFormat = Literal["md", "csv", "json"]


def _require_non_empty_text(value: str, field_label: str) -> str:
    """Metin alanlarının boş veya yalnızca boşluklardan oluşmamasını doğrular."""
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_label} boş bırakılamaz.")
    return cleaned


def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
    """Opsiyonel metinlerdeki boş/whitespace değerleri None olarak normalize eder."""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class LLMAcceptanceCriterion(BaseModel):
    """LLM tarafından üretilen Given-When-Then kabul kriteri şeması."""

    code: str = Field(description="Kabul kriteri kodu (ör. AC-01.1).")
    given_clause: str = Field(description="Ön koşul (Given) ifadesi.")
    when_clause: str = Field(description="Tetikleyici olay (When) ifadesi.")
    then_clause: str = Field(description="Beklenen sonuç (Then) ifadesi.")

    @field_validator("code", "given_clause", "when_clause", "then_clause")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:  # type: ignore[no-untyped-def]
        return _require_non_empty_text(value, info.field_name)


class LLMUserStory(BaseModel):
    """LLM tarafından üretilen Agile kullanıcı hikâyesi şeması."""

    code: str = Field(description="Kullanıcı hikâyesi kodu (ör. US-01).")
    related_requirement_code: Optional[str] = Field(
        default=None,
        description="İlişkili gereksinim kodu (ör. FR-01).",
    )
    role: str = Field(description="Kullanıcı rolü (ör. İş Analisti).")
    goal: str = Field(description="Kullanıcının gerçekleştirmek istediği hedef.")
    benefit: str = Field(description="Hedefin sağlayacağı iş değeri veya fayda.")
    acceptance_criteria: list[LLMAcceptanceCriterion] = Field(
        description="Hikâyeye ait Given-When-Then kabul kriterleri listesi."
    )

    @field_validator("code", "role", "goal", "benefit")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:  # type: ignore[no-untyped-def]
        return _require_non_empty_text(value, info.field_name)

    @field_validator("related_requirement_code")
    @classmethod
    def normalize_related_code(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_text(value)

    @field_validator("acceptance_criteria")
    @classmethod
    def validate_criteria_not_empty(
        cls, value: list[LLMAcceptanceCriterion]
    ) -> list[LLMAcceptanceCriterion]:
        if not value:
            raise ValueError("Her kullanıcı hikâyesi en az bir kabul kriteri içermelidir.")
        return value


class LLMRequirement(BaseModel):
    """LLM tarafından üretilen fonksiyonel veya fonksiyonel olmayan gereksinim şeması."""

    code: str = Field(description="Gereksinim kodu (ör. FR-01 veya NFR-01).")
    req_type: RequirementType = Field(
        description="Gereksinim türü: functional veya non_functional."
    )
    category: Optional[str] = Field(
        default=None,
        description="Kategori adı (ör. Güvenlik, Performans, Kimlik Doğrulama).",
    )
    title: str = Field(description="Kısa ve açıklayıcı gereksinim başlığı.")
    description: str = Field(description="Ölçülebilir, açık ve test edilebilir gereksinim tanımı.")
    moscow_priority: MoscowPriority = Field(
        description="MoSCoW öncelik etiketi: Must, Should, Could veya Wont."
    )
    ambiguity_warning: Optional[str] = Field(
        default=None,
        description="Metindeki muğlak ifadeler varsa açıklayıcı uyarı ve somutlaştırma önerisi; yoksa null.",
    )

    @field_validator("code", "title", "description")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:  # type: ignore[no-untyped-def]
        return _require_non_empty_text(value, info.field_name)

    @field_validator("category", "ambiguity_warning")
    @classmethod
    def normalize_optional_fields(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_text(value)


class LLMAnalysisOutput(BaseModel):
    """Gemini Structured Output tarafından döndürülen tam analiz şeması."""

    project_title: str = Field(description="Analiz edilen proje veya modül için kısa başlık.")
    summary: str = Field(description="Sistemin kapsamını ve temel hedeflerini özetleyen kısa paragraf.")
    requirements: list[LLMRequirement] = Field(
        description="Üretilen fonksiyonel ve fonksiyonel olmayan gereksinimler listesi."
    )
    user_stories: list[LLMUserStory] = Field(
        description="Üretilen kullanıcı hikâyeleri ve kabul kriterleri listesi."
    )

    @field_validator("project_title", "summary")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:  # type: ignore[no-untyped-def]
        return _require_non_empty_text(value, info.field_name)

    @field_validator("requirements")
    @classmethod
    def validate_requirements_not_empty(cls, value: list[LLMRequirement]) -> list[LLMRequirement]:
        if not value:
            raise ValueError("Analiz çıktısı en az bir gereksinim içermelidir.")
        return value

    @field_validator("user_stories")
    @classmethod
    def validate_stories_not_empty(cls, value: list[LLMUserStory]) -> list[LLMUserStory]:
        if not value:
            raise ValueError("Analiz çıktısı en az bir kullanıcı hikâyesi içermelidir.")
        return value


class AnalyzeRequest(BaseModel):
    """Analiz başlatma isteği doğrulama şeması."""

    title: Optional[str] = Field(default=None, description="Opsiyonel proje başlığı.")
    raw_input: str = Field(description="Analiz edilecek serbest doğal dil metni.")
    use_demo: bool = Field(
        default=False,
        description="İstek bazında çevrimdışı demo analiz modunu etkinleştirir.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        cleaned = _normalize_optional_text(value)
        if cleaned is not None and len(cleaned) > 255:
            raise ValueError("Proje başlığı en fazla 255 karakter olabilir.")
        return cleaned

    @field_validator("raw_input")
    @classmethod
    def validate_raw_input(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 20:
            raise ValueError("Gereksinim metni en az 20 karakter olmalıdır.")
        return cleaned


class AcceptanceCriterionRead(BaseModel):
    """Veritabanından okunan kabul kriteri yanıt şeması."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_story_id: int
    code: str
    given_clause: str
    when_clause: str
    then_clause: str


class UserStoryRead(BaseModel):
    """Veritabanından okunan kullanıcı hikâyesi yanıt şeması."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    requirement_id: Optional[int] = None
    code: str
    related_requirement_code: Optional[str] = None
    role: str
    goal: str
    benefit: str
    acceptance_criteria: list[AcceptanceCriterionRead] = []


class RequirementRead(BaseModel):
    """Veritabanından okunan gereksinim yanıt şeması."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    code: str
    req_type: RequirementType
    category: Optional[str] = None
    title: str
    description: str
    moscow_priority: MoscowPriority
    ambiguity_warning: Optional[str] = None


class AnalysisSessionSummary(BaseModel):
    """Geçmiş oturum listeleme için özet yanıt şeması."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: Optional[str] = None
    source_mode: SourceMode
    requirement_count: int = 0
    user_story_count: int = 0
    ambiguity_count: int = 0
    created_at: datetime
    updated_at: datetime


class AnalysisSessionDetail(AnalysisSessionSummary):
    """Tüm alt kayıtlarıyla birlikte analiz oturumu detay şeması."""

    raw_input: str
    requirements: list[RequirementRead] = []
    user_stories: list[UserStoryRead] = []


class AcceptanceCriterionUpsert(BaseModel):
    """Kullanıcı hikâyesi kabul kriteri ekleme/güncelleme şeması."""

    id: Optional[int] = None
    code: str
    given_clause: str
    when_clause: str
    then_clause: str

    @field_validator("code", "given_clause", "when_clause", "then_clause")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:  # type: ignore[no-untyped-def]
        return _require_non_empty_text(value, info.field_name)


class UserStoryUpsert(BaseModel):
    """Kullanıcı hikâyesi ekleme/güncelleme şeması."""

    id: Optional[int] = None
    code: str
    related_requirement_code: Optional[str] = None
    role: str
    goal: str
    benefit: str
    acceptance_criteria: list[AcceptanceCriterionUpsert] = []

    @field_validator("code", "role", "goal", "benefit")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:  # type: ignore[no-untyped-def]
        return _require_non_empty_text(value, info.field_name)

    @field_validator("related_requirement_code")
    @classmethod
    def normalize_related_code(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_text(value)


class RequirementUpsert(BaseModel):
    """Gereksinim ekleme/güncelleme şeması."""

    id: Optional[int] = None
    code: str
    req_type: RequirementType
    category: Optional[str] = None
    title: str
    description: str
    moscow_priority: MoscowPriority
    ambiguity_warning: Optional[str] = None

    @field_validator("code", "title", "description")
    @classmethod
    def validate_non_empty(cls, value: str, info) -> str:  # type: ignore[no-untyped-def]
        return _require_non_empty_text(value, info.field_name)

    @field_validator("category", "ambiguity_warning")
    @classmethod
    def normalize_optional_fields(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_text(value)


class SessionUpdateRequest(BaseModel):
    """Mevcut analiz oturumunu ve alt öğelerini güncelleme isteği."""

    title: Optional[str] = None
    summary: Optional[str] = None
    requirements: Optional[list[RequirementUpsert]] = None
    user_stories: Optional[list[UserStoryUpsert]] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Proje başlığı boş bırakılamaz.")
        if len(cleaned) > 255:
            raise ValueError("Proje başlığı en fazla 255 karakter olabilir.")
        return cleaned

    @field_validator("summary")
    @classmethod
    def normalize_summary(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_optional_text(value)


class DeleteSessionResponse(BaseModel):
    """Oturum silme işlemi yanıt şeması."""

    id: int
    deleted: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Standart JSON hata yanıt şeması."""

    detail: str
    error_code: str
