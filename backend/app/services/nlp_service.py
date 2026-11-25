"""Google Gemini Interactions API tabanlı gereksinim analizi servisi."""

from typing import Any

import httpx
from google import genai
from google.genai import errors as genai_errors
from pydantic import ValidationError

from app.config import Settings, settings
from app.schemas.analysis import LLMAnalysisOutput, SourceMode
from app.services.demo_fallback import generate_demo_analysis
from app.services.exceptions import (
    LLMConfigurationError,
    LLMOutputParseError,
    LLMProviderError,
)

try:
    from google.genai import _interactions_errors as interactions_errors
except ImportError:  # pragma: no cover
    interactions_errors = None  # type: ignore[assignment]

PLACEHOLDER_API_KEYS = {"", "your_gemini_api_key_here", "changeme"}

_RETRYABLE_STATUS_CODES = {404, 408, 429, 500, 502, 503, 504}

SYSTEM_PROMPT = """Sen ISO/IEC/IEEE 29148 standartlarına hakim kıdemli bir Yazılım Gereksinim Mühendisi ve İş Analistisin.
Görevin, kullanıcının verdiği serbest doğal dil metnini analiz ederek eksiksiz, ölçülebilir ve tutarlı bir yazılım gereksinim analizi üretmektir.

Kurallar:
1. Tüm alan içeriklerini (başlıklar, açıklamalar, uyarılar, kullanıcı hikâyeleri ve kabul kriterleri) açık, profesyonel ve tutarlı Türkçe ile yaz.
2. Gereksinimleri kesin olarak `functional` (`FR-01`, `FR-02`, ...) ve `non_functional` (`NFR-01`, `NFR-02`, ...) biçiminde ayır ve kodla.
3. Her gereksinime bağlama uygun tek bir MoSCoW önceliği ata: `Must`, `Should`, `Could` veya `Wont`.
4. Girdi metninde ölçülebilir olmayan, öznel veya muğlak ifadeler varsa (ör. "hızlı olsun", "kullanıcı dostu", "güvenli", "modern", "kolay", "gerektiğinde") ilgili gereksinimin `ambiguity_warning` alanında muğlaklığın nedenini ve somutlaştırma önerisini açıkla; belirsizlik yoksa `ambiguity_warning` değerini `null` bırak.
5. Önemli fonksiyonel gereksinimler için `US-01`, `US-02` şeklinde Agile Kullanıcı Hikâyeleri (`role`, `goal`, `benefit`) üret ve `related_requirement_code` ile ilgili gereksinim koduna bağla.
6. Her kullanıcı hikâyesi için en az bir adet BDD uyumlu `Given - When - Then` kabul kriteri (`AC-01.1`, ...) oluştur.
7. Yalnızca tanımlanan JSON şemasına birebir uyan çıktı üret; şema dışı alan ekleme."""


def build_user_prompt(raw_input: str, title: str | None = None) -> str:
    """Ham kullanıcı metnini ve opsiyonel başlığı LLM istemine dönüştürür."""
    clean_title = title.strip() if title else ""
    header = (
        f"Proje Başlığı: {clean_title}\n\n"
        if clean_title
        else "Proje Başlığı: (Metinden kısa ve anlamlı bir proje başlığı türet)\n\n"
    )
    return (
        f"{header}"
        "Aşağıdaki paydaş/proje metnini analiz et ve istenen JSON şemasında "
        "gereksinimleri, belirsizlik uyarılarını, MoSCoW önceliklerini, kullanıcı "
        "hikâyelerini ve Given-When-Then kabul kriterlerini üret:\n\n"
        f"\"\"\"\n{raw_input.strip()}\n\"\"\""
    )


def _is_timeout_error(exc: Exception) -> bool:
    """İstisnanın zaman aşımından kaynaklanıp kaynaklanmadığını belirler."""
    if isinstance(exc, (httpx.TimeoutException, TimeoutError)):
        return True
    if interactions_errors is not None and isinstance(exc, interactions_errors.APITimeoutError):
        return True
    return False


def _is_connection_error(exc: Exception) -> bool:
    """İstisnanın ağ/bağlantı hatasından kaynaklanıp kaynaklanmadığını belirler."""
    if isinstance(exc, httpx.HTTPError):
        return True
    if interactions_errors is not None and isinstance(exc, interactions_errors.APIConnectionError):
        return True
    return False


def _extract_status_code(exc: Exception) -> int | None:
    """Gemini SDK veya Interactions hata nesnesinden HTTP durum kodunu çıkarır."""
    for attr in ("status_code", "code"):
        val = getattr(exc, attr, None)
        if isinstance(val, int):
            return val
    return None


def _is_auth_error(exc: Exception, status_code: int | None) -> bool:
    """API anahtarı veya yetkilendirme hatası olup olmadığını kontrol eder."""
    if status_code in (401, 403):
        return True
    if interactions_errors is not None and isinstance(
        exc,
        (interactions_errors.AuthenticationError, interactions_errors.PermissionDeniedError),
    ):
        return True
    return False


class NLPService:
    """Gemini Structured Output veya DEMO_MODE kullanarak gereksinim analizi yürütür."""

    def __init__(
        self,
        settings_obj: Settings | None = None,
        client: Any | None = None,
    ) -> None:
        self.settings = settings_obj or settings
        self._client = client

    def _get_client(self) -> Any:
        """Enjekte edilen veya API anahtarından üretilen Gemini istemcisini döndürür."""
        if self._client is not None:
            return self._client

        api_key = (self.settings.gemini_api_key or "").strip()
        if api_key in PLACEHOLDER_API_KEYS:
            raise LLMConfigurationError(
                "GEMINI_API_KEY tanımlanmamış. Gerçek analiz için geçerli bir API anahtarı "
                "girin veya çevrimdışı test için DEMO_MODE=true ayarlayın."
            )

        client = genai.Client(api_key=api_key)
        # SDK varsayılan 30 sn içsel 503 tekrar denemesini azalt ki model fallback hızlı devreye girsin
        interactions_cfg = getattr(getattr(client, "interactions", None), "sdk_configuration", None)
        retry_cfg = getattr(interactions_cfg, "retry_config", None)
        if retry_cfg is not None and hasattr(retry_cfg, "max_retries"):
            retry_cfg.max_retries = 0 if len(self.settings.candidate_gemini_models) > 1 else 1
        self._client = client
        return self._client

    def _map_provider_exception(self, exc: Exception) -> LLMProviderError:
        """Yakalanan sağlayıcı/ağ istisnasını anlaşılır Türkçe LLMProviderError'a dönüştürür."""
        if _is_timeout_error(exc):
            return LLMProviderError(
                f"Gemini API yanıtı {self.settings.gemini_timeout_seconds:.0f} saniye içinde tamamlanamadı."
            )

        status_code = _extract_status_code(exc)
        if status_code == 429:
            return LLMProviderError(
                "Gemini API istek/kota sınırına ulaşıldı (HTTP 429). Kısa süre sonra tekrar deneyin veya Demo Modunu kullanın."
            )
        if status_code in (500, 502, 503, 504):
            return LLMProviderError(
                f"Gemini servisi şu anda yoğun veya geçici olarak erişilemiyor (HTTP {status_code}). Lütfen tekrar deneyin veya Demo Modunu kullanın."
            )
        if _is_connection_error(exc):
            return LLMProviderError(
                f"Gemini API ağ bağlantısı kurulamadı: {type(exc).__name__}"
            )
        if status_code is not None:
            return LLMProviderError(
                f"Gemini API isteği başarısız oldu (durum: {status_code})."
            )
        return LLMProviderError(
            f"Yapay zekâ servisi çağrısı sırasında beklenmeyen hata: {type(exc).__name__}"
        )

    def analyze_text(
        self,
        raw_input: str,
        title: str | None = None,
        *,
        force_demo: bool = False,
    ) -> tuple[LLMAnalysisOutput, SourceMode]:
        """Verilen ham metni analiz ederek doğrulanmış LLMAnalysisOutput ve kaynak modunu döndürür."""
        clean_title = title.strip() if title and title.strip() else None

        if self.settings.demo_mode or force_demo:
            demo_output = generate_demo_analysis(raw_input, title=clean_title)
            return demo_output, "demo"

        client = self._get_client()
        prompt = build_user_prompt(raw_input, title=clean_title)
        response_format = {
            "type": "text",
            "mime_type": "application/json",
            "schema": LLMAnalysisOutput.model_json_schema(),
        }

        candidate_models = self.settings.candidate_gemini_models
        interaction: Any = None
        last_exc: Exception | None = None

        for idx, model_name in enumerate(candidate_models):
            has_next = idx < len(candidate_models) - 1
            try:
                interaction = client.interactions.create(
                    model=model_name,
                    system_instruction=SYSTEM_PROMPT,
                    input=prompt,
                    response_format=response_format,
                    generation_config={"temperature": 0.2},
                    store=False,
                    timeout=self.settings.gemini_timeout_seconds,
                )
                break
            except Exception as exc:
                last_exc = exc
                status_code = _extract_status_code(exc)

                if _is_auth_error(exc, status_code):
                    raise LLMConfigurationError(
                        "Gemini API anahtarı geçersiz veya bu işlem için yetkisiz. "
                        "Lütfen backend/.env içindeki GEMINI_API_KEY değerini kontrol edin."
                    ) from exc

                is_sdk_api_error = isinstance(exc, genai_errors.APIError) or (
                    interactions_errors is not None
                    and isinstance(exc, interactions_errors.APIError)
                )
                can_fallback = (
                    _is_timeout_error(exc)
                    or status_code in _RETRYABLE_STATUS_CODES
                    or is_sdk_api_error
                )
                if has_next and can_fallback:
                    continue

                raise self._map_provider_exception(exc) from exc

        if interaction is None:
            if last_exc is not None:
                raise self._map_provider_exception(last_exc) from last_exc
            raise LLMProviderError("Gemini API isteği tamamlanamadı.")

        raw_output_text = getattr(interaction, "output_text", None)
        if not raw_output_text or not str(raw_output_text).strip():
            raise LLMOutputParseError("Yapay zekâ servisinden boş yanıt döndü.")

        try:
            parsed = LLMAnalysisOutput.model_validate_json(raw_output_text)
        except (ValidationError, ValueError) as exc:
            raise LLMOutputParseError(
                "Yapay zekâ yanıtı geçerli gereksinim analizi şemasına dönüştürülemedi."
            ) from exc

        if clean_title is not None:
            parsed = parsed.model_copy(update={"project_title": clean_title[:255]})

        return parsed, "llm"
