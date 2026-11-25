"""Uygulama yapılandırma ayarları."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ortam değişkenlerinden yüklenen ReqSense yapılandırması."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ReqSense"
    app_version: str = "1.0.0"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-4-hydrogen"
    gemini_timeout_seconds: float = 15.0
    database_url: str = "sqlite:///./reqsense.db"
    demo_mode: bool = False
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Virgülle ayrılmış CORS adreslerini liste olarak döndürür."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
