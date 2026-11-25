"""Pydantic şema doğrulama, DEMO_MODE fallback ve mock Gemini NLP servisi testleri."""

import json
from types import SimpleNamespace

import httpx
import pytest
from google.genai import _interactions_errors as interactions_errors
from google.genai import errors as genai_errors
from pydantic import ValidationError

from app.config import Settings
from app.schemas.analysis import (
    AnalyzeRequest,
    LLMAcceptanceCriterion,
    LLMAnalysisOutput,
    LLMRequirement,
    LLMUserStory,
)
from app.services.exceptions import (
    LLMConfigurationError,
    LLMOutputParseError,
    LLMProviderError,
)
from app.services.nlp_service import NLPService, SYSTEM_PROMPT


class _FakeInteractionsAPI:
    def __init__(self, *, response: object | None = None, exc: Exception | None = None) -> None:
        self._response = response
        self._exc = exc
        self.last_kwargs: dict[str, object] | None = None

    def create(self, **kwargs: object) -> object:
        self.last_kwargs = kwargs
        if self._exc is not None:
            raise self._exc
        return self._response


class _FakeGeminiClient:
    def __init__(self, *, response: object | None = None, exc: Exception | None = None) -> None:
        self.interactions = _FakeInteractionsAPI(response=response, exc=exc)


def _valid_payload_dict() -> dict[str, object]:
    return {
        "project_title": "Staj Takip Portalı",
        "summary": "Öğrenci staj başvurularını ve onay süreçlerini yöneten web uygulaması.",
        "requirements": [
            {
                "code": "FR-01",
                "req_type": "functional",
                "category": "Başvuru Yönetimi",
                "title": "Staj Başvuru Formu",
                "description": "Öğrenciler staj yeri ve tarih bilgilerini girerek başvuru oluşturabilmelidir.",
                "moscow_priority": "Must",
                "ambiguity_warning": None,
            },
            {
                "code": "NFR-01",
                "req_type": "non_functional",
                "category": "Güvenlik",
                "title": "Yetkilendirme Koruması",
                "description": "Tüm başvuru uç noktaları kimlik doğrulaması gerektirmelidir.",
                "moscow_priority": "Must",
                "ambiguity_warning": "Oturum süresi (dakika) sayısal olarak netleştirilmelidir.",
            },
        ],
        "user_stories": [
            {
                "code": "US-01",
                "related_requirement_code": "FR-01",
                "role": "Öğrenci",
                "goal": "staj başvurumu çevrimiçi gönderebilmek",
                "benefit": "evrak teslim sürecini hızlandırabilirim",
                "acceptance_criteria": [
                    {
                        "code": "AC-01.1",
                        "given_clause": "Öğrenci zorunlu başvuru alanlarını doldurmuştur",
                        "when_clause": "Başvuruyu Gönder butonuna tıklandığında",
                        "then_clause": "Başvuru kaydedilir ve takip numarası görüntülenir",
                    }
                ],
            }
        ],
    }


@pytest.mark.parametrize(
    "bad_input",
    [
        "",
        "     \n\t   ",
        "Çok kısa metin.",
        "1234567890123456789",
    ],
)
def test_analyze_request_rejects_short_or_empty_input(bad_input: str) -> None:
    """Boş veya 20 karakterden kısa raw_input değerlerinin Türkçe hata mesajıyla reddedildiğini doğrular."""
    with pytest.raises(ValidationError) as exc_info:
        AnalyzeRequest(raw_input=bad_input)

    assert "en az 20 karakter" in str(exc_info.value)


def test_analyze_request_normalizes_title_and_validates_length() -> None:
    """Başlık trim/None normalizasyonunu ve 255 karakter üst sınırını doğrular."""
    req = AnalyzeRequest(
        title="   ",
        raw_input="   Kullanıcılar sisteme giriş yapıp proje gereksinimlerini analiz edebilmelidir.   ",
    )
    assert req.title is None
    assert req.raw_input.startswith("Kullanıcılar")

    with pytest.raises(ValidationError):
        AnalyzeRequest(
            title="A" * 256,
            raw_input="Kullanıcılar sisteme giriş yapıp proje gereksinimlerini analiz edebilmelidir.",
        )


def test_llm_output_schema_normalizes_and_validates() -> None:
    """LLMAnalysisOutput şemasının geçerli çıktıyı kabul edip geçersiz alanları reddettiğini doğrular."""
    payload = _valid_payload_dict()
    payload["requirements"][0]["ambiguity_warning"] = "   "  # type: ignore[index]
    payload["requirements"][0]["category"] = ""  # type: ignore[index]

    parsed = LLMAnalysisOutput.model_validate(payload)
    assert parsed.requirements[0].ambiguity_warning is None
    assert parsed.requirements[0].category is None

    invalid_moscow = _valid_payload_dict()
    invalid_moscow["requirements"][0]["moscow_priority"] = "Critical"  # type: ignore[index]
    with pytest.raises(ValidationError):
        LLMAnalysisOutput.model_validate(invalid_moscow)

    empty_reqs = _valid_payload_dict()
    empty_reqs["requirements"] = []
    with pytest.raises(ValidationError):
        LLMAnalysisOutput.model_validate(empty_reqs)

    with pytest.raises(ValidationError):
        LLMUserStory(
            code="US-01",
            role="Kullanıcı",
            goal="giriş yapmak",
            benefit="işlem yapabilmek",
            acceptance_criteria=[],
        )

    with pytest.raises(ValidationError):
        LLMAcceptanceCriterion(
            code="AC-01",
            given_clause="   ",
            when_clause="Butona basıldığında",
            then_clause="Sonuç gösterilir",
        )


def test_demo_mode_detects_ambiguities_and_skips_remote_client() -> None:
    """DEMO_MODE=true iken harici API çağrılmadan muğlak ifadelerin işaretlendiğini doğrular."""
    failing_client = _FakeGeminiClient(exc=AssertionError("Demo modda API çağrılmamalıdır!"))
    service = NLPService(
        settings_obj=Settings(demo_mode=True, gemini_api_key=""),
        client=failing_client,
    )

    output, mode = service.analyze_text(
        raw_input="Sistem çok hızlı çalışsın, arayüz kullanıcı dostu olsun ve tüm veriler güvenli saklansın.",
        title="E-Ticaret MVP",
    )

    assert mode == "demo"
    assert output.project_title == "E-Ticaret MVP"
    assert len(output.requirements) == 6
    assert {req.moscow_priority for req in output.requirements} == {"Must", "Should", "Could", "Wont"}

    warnings_by_code = {req.code: req.ambiguity_warning for req in output.requirements}
    assert warnings_by_code["NFR-01"] and "hızlı" in warnings_by_code["NFR-01"]
    assert warnings_by_code["NFR-02"] and "kullanıcı dostu" in warnings_by_code["NFR-02"]
    assert warnings_by_code["FR-02"] and "güvenli" in warnings_by_code["FR-02"]


def test_nlp_service_calls_interactions_api_with_structured_output() -> None:
    """DEMO_MODE=false iken mock Gemini Interactions API çağrısının doğru parametrelerle yapıldığını doğrular."""
    raw_json = json.dumps(_valid_payload_dict(), ensure_ascii=False)
    fake_client = _FakeGeminiClient(response=SimpleNamespace(output_text=raw_json))
    service = NLPService(
        settings_obj=Settings(
            demo_mode=False,
            gemini_api_key="test-key-123",
            gemini_model="gemini-4-hydrogen",
            gemini_timeout_seconds=12.0,
        ),
        client=fake_client,
    )

    output, mode = service.analyze_text(
        raw_input="Öğrenciler staj başvurusu yapabilsin ve danışmanlar onaylayabilsin.",
        title="Özel Başlık",
    )

    assert mode == "llm"
    assert output.project_title == "Özel Başlık"
    assert len(output.requirements) == 2
    assert output.user_stories[0].acceptance_criteria[0].code == "AC-01.1"

    kwargs = fake_client.interactions.last_kwargs
    assert kwargs is not None
    assert kwargs["model"] == "gemini-4-hydrogen"
    assert kwargs["system_instruction"] == SYSTEM_PROMPT
    assert kwargs["store"] is False
    assert kwargs["timeout"] == 12.0
    assert kwargs["response_format"] == {
        "type": "text",
        "mime_type": "application/json",
        "schema": LLMAnalysisOutput.model_json_schema(),
    }


def test_nlp_service_raises_configuration_error_without_api_key() -> None:
    """API anahtarı eksik veya placeholder olduğunda LLMConfigurationError (503) fırlatıldığını doğrular."""
    for key in ("", "your_gemini_api_key_here"):
        service = NLPService(settings_obj=Settings(demo_mode=False, gemini_api_key=key))
        with pytest.raises(LLMConfigurationError) as exc_info:
            service.analyze_text("Bu test metni en az yirmi karakter uzunluğundadır.")
        assert exc_info.value.status_code == 503


def test_nlp_service_handles_timeout_and_api_errors() -> None:
    """Zaman aşımı ve Gemini API hatalarının LLMProviderError (503) olarak sarmalandığını doğrular."""
    timeout_client = _FakeGeminiClient(exc=httpx.ReadTimeout("timed out"))
    timeout_service = NLPService(
        settings_obj=Settings(
            demo_mode=False,
            gemini_api_key="valid-key",
            gemini_fallback_models="",
        ),
        client=timeout_client,
    )
    with pytest.raises(LLMProviderError) as timeout_exc:
        timeout_service.analyze_text("Sistem kullanıcıların raporlarını güvenli biçimde dışa aktarsın.")
    assert timeout_exc.value.status_code == 503
    assert "30 saniye" in timeout_exc.value.detail

    api_error = genai_errors.APIError(
        503,
        {"error": {"message": "Service unavailable", "status": "UNAVAILABLE"}},
    )
    api_client = _FakeGeminiClient(exc=api_error)
    api_service = NLPService(
        settings_obj=Settings(
            demo_mode=False,
            gemini_api_key="valid-key",
            gemini_fallback_models="",
        ),
        client=api_client,
    )
    with pytest.raises(LLMProviderError) as api_exc:
        api_service.analyze_text("Sistem kullanıcıların raporlarını güvenli biçimde dışa aktarsın.")
    assert api_exc.value.status_code == 503


def test_nlp_service_falls_back_on_503_and_rejects_auth_errors() -> None:
    """Birincil model 503 InternalServerError verdiğinde yedek modele geçildiğini, 401'de geçilmediğini doğrular."""
    raw_json = json.dumps(_valid_payload_dict(), ensure_ascii=False)
    called_models: list[str] = []

    class _FallbackInteractions:
        def create(self, **kwargs: object) -> object:
            model_name = str(kwargs["model"])
            called_models.append(model_name)
            if model_name == "gemini-4-hydrogen":
                response = httpx.Response(
                    503,
                    request=httpx.Request("POST", "https://example.invalid/v1/interactions"),
                )
                raise interactions_errors.InternalServerError(
                    "gemini-4-hydrogen overloaded",
                    response=response,
                    body={"error": {"code": "service_unavailable"}},
                )
            return SimpleNamespace(output_text=raw_json)

    fallback_client = SimpleNamespace(interactions=_FallbackInteractions())
    service = NLPService(
        settings_obj=Settings(
            demo_mode=False,
            gemini_api_key="valid-key",
            gemini_model="gemini-4-hydrogen",
            gemini_fallback_models="gemini-3.5-flash-lite",
        ),
        client=fallback_client,
    )
    output, mode = service.analyze_text("Öğrenciler staj başvurularını çevrimiçi yapabilmelidir.")
    assert mode == "llm"
    assert called_models == ["gemini-4-hydrogen", "gemini-3.5-flash-lite"]
    assert output.project_title == "Staj Takip Portalı"

    # 401 AuthenticationError durumunda yedek modele geçmeden LLMConfigurationError fırlatılmalı
    auth_calls: list[str] = []

    class _AuthFailInteractions:
        def create(self, **kwargs: object) -> object:
            auth_calls.append(str(kwargs["model"]))
            response = httpx.Response(
                401,
                request=httpx.Request("POST", "https://example.invalid/v1/interactions"),
            )
            raise interactions_errors.AuthenticationError(
                "invalid api key",
                response=response,
                body={"error": {"code": "unauthenticated"}},
            )

    auth_service = NLPService(
        settings_obj=Settings(
            demo_mode=False,
            gemini_api_key="bad-key",
            gemini_model="gemini-3.5-flash-lite",
            gemini_fallback_models="gemini-3.1-flash-lite",
        ),
        client=SimpleNamespace(interactions=_AuthFailInteractions()),
    )
    with pytest.raises(LLMConfigurationError) as auth_exc:
        auth_service.analyze_text("Öğrenciler staj başvurularını çevrimiçi yapabilmelidir.")
    assert auth_exc.value.status_code == 503
    assert auth_calls == ["gemini-3.5-flash-lite"]


@pytest.mark.parametrize(
    "bad_output_text",
    [
        "",
        "   ",
        "{bozuk json",
        json.dumps({"project_title": "Eksik Alan"}),
    ],
)
def test_nlp_service_raises_output_parse_error_on_invalid_json(bad_output_text: str) -> None:
    """Boş veya şemaya uymayan LLM yanıtlarında LLMOutputParseError (502) fırlatıldığını doğrular."""
    fake_client = _FakeGeminiClient(response=SimpleNamespace(output_text=bad_output_text))
    service = NLPService(
        settings_obj=Settings(demo_mode=False, gemini_api_key="valid-key"),
        client=fake_client,
    )
    with pytest.raises(LLMOutputParseError) as exc_info:
        service.analyze_text("Sistem kullanıcıların raporlarını güvenli biçimde dışa aktarsın.")
    assert exc_info.value.status_code == 502
