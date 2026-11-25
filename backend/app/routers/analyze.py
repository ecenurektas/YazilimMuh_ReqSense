"""Doğal dil gereksinim analizi API uç noktası."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analysis import AnalysisSessionDetail, AnalyzeRequest, ErrorResponse
from app.services.nlp_service import NLPService
from app.services.session_service import create_analysis_session

router = APIRouter(prefix="/api", tags=["Analiz"])


def get_nlp_service() -> NLPService:
    """FastAPI bağımlılık enjeksiyonu için NLPService örneği sağlar."""
    return NLPService()


@router.post(
    "/analyze",
    response_model=AnalysisSessionDetail,
    status_code=status.HTTP_201_CREATED,
    responses={
        422: {"model": ErrorResponse, "description": "Geçersiz veya kısa girdi metni"},
        502: {"model": ErrorResponse, "description": "LLM çıktısı şema doğrulamasından geçemedi"},
        503: {"model": ErrorResponse, "description": "LLM sağlayıcı veya yapılandırma hatası"},
    },
)
def analyze_requirements(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
    nlp_service: NLPService = Depends(get_nlp_service),
) -> AnalysisSessionDetail:
    """Serbest metni analiz eder, ilişkisel veritabanına kaydeder ve tam oturumu döndürür."""
    output, source_mode = nlp_service.analyze_text(
        payload.raw_input,
        title=payload.title,
        force_demo=payload.use_demo,
    )
    created = create_analysis_session(
        db,
        raw_input=payload.raw_input,
        output=output,
        source_mode=source_mode,
        title=payload.title,
    )
    return AnalysisSessionDetail.model_validate(created)
