"""NLP ve LLM analiz servisine özgü istisna sınıfları."""


class NLPServiceError(Exception):
    """NLP analiz katmanı hataları için temel istisna sınıfı."""

    def __init__(
        self,
        detail: str,
        *,
        status_code: int = 502,
        error_code: str = "nlp_error",
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code


class LLMConfigurationError(NLPServiceError):
    """API anahtarı veya sağlayıcı yapılandırması eksik/geçersiz olduğunda fırlatılır."""

    def __init__(self, detail: str = "Gemini API anahtarı yapılandırılmamış veya geçersiz.") -> None:
        super().__init__(detail, status_code=503, error_code="llm_not_configured")


class LLMProviderError(NLPServiceError):
    """Harici LLM API çağrısı zaman aşımı, kota veya ağ hatası verdiğinde fırlatılır."""

    def __init__(self, detail: str = "Yapay zekâ servisiyle iletişim sırasında bir hata oluştu.") -> None:
        super().__init__(detail, status_code=503, error_code="llm_provider_error")


class LLMOutputParseError(NLPServiceError):
    """LLM çıktısı boş geldiğinde veya beklenen şemaya uymadığında fırlatılır."""

    def __init__(self, detail: str = "Yapay zekâ yanıtı beklenen yapılandırılmış şemaya uymuyor.") -> None:
        super().__init__(detail, status_code=502, error_code="llm_output_invalid")


class SessionNotFoundError(Exception):
    """İstenen analiz oturumu veritabanında bulunamadığında fırlatılır."""

    def __init__(self, session_id: int) -> None:
        self.session_id = session_id
        self.status_code = 404
        self.error_code = "session_not_found"
        self.detail = f"#{session_id} numaralı analiz oturumu bulunamadı."
        super().__init__(self.detail)
