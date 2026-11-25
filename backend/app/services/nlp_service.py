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

PLACEHOLDER_API_KEYS = {"", "your_gemini_api_key_here", "changeme"}

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

        self._client = genai.Client(api_key=api_key)
        return self._client

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

        try:
            interaction = client.interactions.create(
                model=self.settings.gemini_model,
                system_instruction=SYSTEM_PROMPT,
                input=prompt,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": LLMAnalysisOutput.model_json_schema(),
                },
                generation_config={"temperature": 0.2},
                store=False,
                timeout=self.settings.gemini_timeout_seconds,
            )
        except (httpx.TimeoutException, TimeoutError) as exc:
            raise LLMProviderError(
                f"Gemini API yanıtı {self.settings.gemini_timeout_seconds:.0f} saniye içinde tamamlanamadı."
            ) from exc
        except genai_errors.APIError as exc:
            status_code = getattr(exc, "code", None)
            detail = f"Gemini API isteği başarısız oldu (durum: {status_code})." if status_code else "Gemini API isteği başarısız oldu."
            raise LLMProviderError(detail) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(
                f"Gemini API ağ bağlantısı kurulamadı: {type(exc).__name__}"
            ) from exc
        except Exception as exc:
            raise LLMProviderError(
                f"Yapay zekâ servisi çağrısı sırasında beklenmeyen hata: {type(exc).__name__}"
            ) from exc

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
