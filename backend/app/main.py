"""ReqSense FastAPI ana uygulama modülü."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Yapay Zekâ Destekli Yazılım Gereksinim Analizi Sistemi API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["Sistem"])
def health_check() -> dict[str, str | bool]:
    """Servisin ayakta olduğunu ve yapılandırma özetini döndürür."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "demo_mode": settings.demo_mode,
    }
