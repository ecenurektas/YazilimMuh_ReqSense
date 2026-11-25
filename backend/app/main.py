"""ReqSense FastAPI ana uygulama modülü."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.routers import analyze_router, sessions_router
from app.services.exceptions import NLPServiceError, SessionNotFoundError


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Uygulama başlangıcında veritabanı tablolarını hazırlar."""
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Yapay Zekâ Destekli Yazılım Gereksinim Analizi Sistemi API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Pydantic/FastAPI doğrulama hatalarını okunabilir Türkçe JSON yanıtına çevirir."""
    errors = jsonable_encoder(exc.errors())
    message = "Girdi doğrulama hatası."
    if errors:
        raw_msg = str(errors[0].get("msg", "")).strip()
        if raw_msg.startswith("Value error, "):
            raw_msg = raw_msg[len("Value error, ") :]
        if raw_msg:
            message = raw_msg

    return JSONResponse(
        status_code=422,
        content={
            "detail": message,
            "error_code": "validation_error",
            "errors": errors,
        },
    )


@app.exception_handler(SessionNotFoundError)
async def session_not_found_handler(
    _request: Request,
    exc: SessionNotFoundError,
) -> JSONResponse:
    """Bulunamayan oturumlar için standart HTTP 404 JSON hatası döndürür."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )


@app.exception_handler(NLPServiceError)
async def nlp_service_exception_handler(
    _request: Request,
    exc: NLPServiceError,
) -> JSONResponse:
    """LLM/NLP katmanı hataları için kontrollü HTTP 502/503 JSON hatası döndürür."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": exc.error_code},
    )


app.include_router(analyze_router)
app.include_router(sessions_router)


@app.get("/api/health", tags=["Sistem"])
def health_check() -> dict[str, str | bool]:
    """Servisin ayakta olduğunu ve yapılandırma özetini döndürür."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "demo_mode": settings.demo_mode,
        "model": settings.gemini_model,
    }
