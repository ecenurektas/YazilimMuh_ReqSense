"""Analiz oturumları CRUD ve çoklu format dışa aktarma API uç noktaları."""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analysis import (
    AnalysisSessionDetail,
    AnalysisSessionSummary,
    DeleteSessionResponse,
    ErrorResponse,
    ExportFormat,
    SessionUpdateRequest,
)
from app.services.exceptions import SessionNotFoundError
from app.services.export_service import build_export_payload
from app.services.session_service import (
    delete_session,
    get_session_or_raise,
    list_sessions,
    update_analysis_session,
)

router = APIRouter(prefix="/api/sessions", tags=["Oturumlar ve Dışa Aktarma"])


@router.get(
    "",
    response_model=list[AnalysisSessionSummary],
)
def get_sessions(db: Session = Depends(get_db)) -> list[AnalysisSessionSummary]:
    """Kayıtlı analiz oturumlarını en yeniden eskiye doğru listeler."""
    sessions = list_sessions(db)
    return [AnalysisSessionSummary.model_validate(item) for item in sessions]


@router.get(
    "/{session_id}",
    response_model=AnalysisSessionDetail,
    responses={404: {"model": ErrorResponse, "description": "Oturum bulunamadı"}},
)
def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
) -> AnalysisSessionDetail:
    """Belirtilen analiz oturumunun tüm gereksinim, hikâye ve kriter detaylarını döndürür."""
    session_obj = get_session_or_raise(db, session_id)
    return AnalysisSessionDetail.model_validate(session_obj)


@router.put(
    "/{session_id}",
    response_model=AnalysisSessionDetail,
    responses={
        404: {"model": ErrorResponse, "description": "Oturum bulunamadı"},
        422: {"model": ErrorResponse, "description": "Geçersiz güncelleme verisi"},
    },
)
def update_session(
    session_id: int,
    payload: SessionUpdateRequest,
    db: Session = Depends(get_db),
) -> AnalysisSessionDetail:
    """Oturum başlığını, özetini, gereksinimlerini ve kullanıcı hikâyelerini günceller."""
    updated = update_analysis_session(db, session_id, payload)
    return AnalysisSessionDetail.model_validate(updated)


@router.delete(
    "/{session_id}",
    response_model=DeleteSessionResponse,
    responses={404: {"model": ErrorResponse, "description": "Oturum bulunamadı"}},
)
def remove_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> DeleteSessionResponse:
    """Belirtilen oturumu ve bağlı tüm alt kayıtları kalıcı olarak siler."""
    deleted = delete_session(db, session_id)
    if not deleted:
        raise SessionNotFoundError(session_id)
    return DeleteSessionResponse(
        id=session_id,
        deleted=True,
        message=f"#{session_id} numaralı analiz oturumu silindi.",
    )


@router.get(
    "/{session_id}/export",
    responses={
        200: {"description": "İndirilebilir dışa aktarma dosyası (.md, .csv veya .json)"},
        404: {"model": ErrorResponse, "description": "Oturum bulunamadı"},
        422: {"model": ErrorResponse, "description": "Desteklenmeyen dışa aktarma formatı"},
    },
)
def export_session(
    session_id: int,
    export_format: ExportFormat = Query(default="md", alias="format"),
    db: Session = Depends(get_db),
) -> Response:
    """Analiz oturumunu Markdown, CSV veya JSON dosyası olarak dışa aktarır."""
    session_obj = get_session_or_raise(db, session_id)
    content_bytes, media_type, filename = build_export_payload(session_obj, export_format)
    return Response(
        content=content_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
