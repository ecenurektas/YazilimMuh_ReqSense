"""Analiz oturumları için veritabanı kalıcılık ve iş akışı servisleri."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.analysis import (
    AcceptanceCriterion,
    AnalysisSession,
    Requirement,
    UserStory,
)
from app.schemas.analysis import (
    AnalyzeRequest,
    LLMAnalysisOutput,
    SessionUpdateRequest,
    SourceMode,
)
from app.services.exceptions import SessionNotFoundError
from app.services.nlp_service import NLPService


def _session_detail_query(session_id: int):
    """Bir oturumu tüm alt ilişkileriyle eager-load eden sorgu oluşturur."""
    return (
        select(AnalysisSession)
        .options(
            selectinload(AnalysisSession.requirements),
            selectinload(AnalysisSession.user_stories).selectinload(
                UserStory.acceptance_criteria
            ),
        )
        .where(AnalysisSession.id == session_id)
    )


def create_analysis_session(
    db: Session,
    *,
    raw_input: str,
    output: LLMAnalysisOutput,
    source_mode: SourceMode,
    title: str | None = None,
) -> AnalysisSession:
    """Doğrulanmış analiz çıktısını ilişkisel SQLite tablolarına kaydeder."""
    effective_title = (title.strip() if title and title.strip() else output.project_title)[:255]

    session_obj = AnalysisSession(
        title=effective_title,
        raw_input=raw_input.strip(),
        summary=output.summary,
        source_mode=source_mode,
    )

    try:
        db.add(session_obj)
        db.flush()

        requirement_id_by_code: dict[str, int] = {}
        for req in output.requirements:
            req_row = Requirement(
                session_id=session_obj.id,
                code=req.code,
                req_type=req.req_type,
                category=req.category,
                title=req.title,
                description=req.description,
                moscow_priority=req.moscow_priority,
                ambiguity_warning=req.ambiguity_warning,
            )
            db.add(req_row)
            db.flush()
            requirement_id_by_code[req.code] = req_row.id

        for story in output.user_stories:
            linked_req_id = (
                requirement_id_by_code.get(story.related_requirement_code)
                if story.related_requirement_code
                else None
            )
            story_row = UserStory(
                session_id=session_obj.id,
                requirement_id=linked_req_id,
                code=story.code,
                related_requirement_code=story.related_requirement_code,
                role=story.role,
                goal=story.goal,
                benefit=story.benefit,
            )
            for criterion in story.acceptance_criteria:
                story_row.acceptance_criteria.append(
                    AcceptanceCriterion(
                        code=criterion.code,
                        given_clause=criterion.given_clause,
                        when_clause=criterion.when_clause,
                        then_clause=criterion.then_clause,
                    )
                )
            db.add(story_row)

        db.commit()
    except Exception:
        db.rollback()
        raise

    created = get_session_by_id(db, session_obj.id)
    assert created is not None
    return created


def get_session_by_id(db: Session, session_id: int) -> AnalysisSession | None:
    """Belirtilen kimliğe sahip oturumu alt gereksinim ve hikâyeleriyle birlikte döndürür."""
    return db.execute(_session_detail_query(session_id)).scalar_one_or_none()


def get_session_or_raise(db: Session, session_id: int) -> AnalysisSession:
    """Belirtilen oturumu döndürür; yoksa SessionNotFoundError fırlatır."""
    session_obj = get_session_by_id(db, session_id)
    if session_obj is None:
        raise SessionNotFoundError(session_id)
    return session_obj


def list_sessions(db: Session) -> list[AnalysisSession]:
    """Kayıtlı tüm analiz oturumlarını en yeniden eskiye doğru listeler."""
    stmt = (
        select(AnalysisSession)
        .options(
            selectinload(AnalysisSession.requirements),
            selectinload(AnalysisSession.user_stories),
        )
        .order_by(
            AnalysisSession.created_at.desc(),
            AnalysisSession.id.desc(),
        )
    )
    return list(db.execute(stmt).scalars().all())


def update_analysis_session(
    db: Session,
    session_id: int,
    payload: SessionUpdateRequest,
) -> AnalysisSession:
    """Mevcut analiz oturumunu, gereksinimlerini, hikâyelerini ve kabul kriterlerini günceller."""
    session_obj = get_session_or_raise(db, session_id)

    try:
        if payload.title is not None:
            session_obj.title = payload.title
        if "summary" in payload.model_fields_set:
            session_obj.summary = payload.summary

        if payload.requirements is not None:
            for story in session_obj.user_stories:
                story.requirement_id = None
            db.flush()

            existing_reqs = {req.id: req for req in session_obj.requirements}
            updated_requirements: list[Requirement] = []
            for req_item in payload.requirements:
                if req_item.id is not None and req_item.id in existing_reqs:
                    req_row = existing_reqs[req_item.id]
                    req_row.code = req_item.code
                    req_row.req_type = req_item.req_type
                    req_row.category = req_item.category
                    req_row.title = req_item.title
                    req_row.description = req_item.description
                    req_row.moscow_priority = req_item.moscow_priority
                    req_row.ambiguity_warning = req_item.ambiguity_warning
                else:
                    req_row = Requirement(
                        session_id=session_obj.id,
                        code=req_item.code,
                        req_type=req_item.req_type,
                        category=req_item.category,
                        title=req_item.title,
                        description=req_item.description,
                        moscow_priority=req_item.moscow_priority,
                        ambiguity_warning=req_item.ambiguity_warning,
                    )
                updated_requirements.append(req_row)

            session_obj.requirements = updated_requirements
            db.flush()

        req_id_by_code = {req.code: req.id for req in session_obj.requirements}

        if payload.user_stories is not None:
            existing_stories = {story.id: story for story in session_obj.user_stories}
            updated_stories: list[UserStory] = []

            for story_item in payload.user_stories:
                linked_req_id = (
                    req_id_by_code.get(story_item.related_requirement_code)
                    if story_item.related_requirement_code
                    else None
                )
                if story_item.id is not None and story_item.id in existing_stories:
                    story_row = existing_stories[story_item.id]
                    story_row.code = story_item.code
                    story_row.related_requirement_code = story_item.related_requirement_code
                    story_row.requirement_id = linked_req_id
                    story_row.role = story_item.role
                    story_row.goal = story_item.goal
                    story_row.benefit = story_item.benefit
                else:
                    story_row = UserStory(
                        session_id=session_obj.id,
                        requirement_id=linked_req_id,
                        code=story_item.code,
                        related_requirement_code=story_item.related_requirement_code,
                        role=story_item.role,
                        goal=story_item.goal,
                        benefit=story_item.benefit,
                    )

                existing_criteria = {ac.id: ac for ac in story_row.acceptance_criteria}
                updated_criteria: list[AcceptanceCriterion] = []
                for ac_item in story_item.acceptance_criteria:
                    if ac_item.id is not None and ac_item.id in existing_criteria:
                        ac_row = existing_criteria[ac_item.id]
                        ac_row.code = ac_item.code
                        ac_row.given_clause = ac_item.given_clause
                        ac_row.when_clause = ac_item.when_clause
                        ac_row.then_clause = ac_item.then_clause
                    else:
                        ac_row = AcceptanceCriterion(
                            code=ac_item.code,
                            given_clause=ac_item.given_clause,
                            when_clause=ac_item.when_clause,
                            then_clause=ac_item.then_clause,
                        )
                    updated_criteria.append(ac_row)

                story_row.acceptance_criteria = updated_criteria
                updated_stories.append(story_row)

            session_obj.user_stories = updated_stories
        else:
            for story_row in session_obj.user_stories:
                story_row.requirement_id = (
                    req_id_by_code.get(story_row.related_requirement_code)
                    if story_row.related_requirement_code
                    else None
                )

        session_obj.updated_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return get_session_or_raise(db, session_id)


def delete_session(db: Session, session_id: int) -> bool:
    """Belirtilen oturumu (cascade ile alt kayıtlarıyla birlikte) siler."""
    session_obj = db.get(AnalysisSession, session_id)
    if session_obj is None:
        return False

    try:
        db.delete(session_obj)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True


def analyze_and_save(
    db: Session,
    *,
    raw_input: str,
    title: str | None = None,
    use_demo: bool = False,
    nlp_service: NLPService | None = None,
) -> AnalysisSession:
    """Girdiyi doğrular, NLP analizini çalıştırır ve sonucu veritabanına kaydeder."""
    request = AnalyzeRequest(title=title, raw_input=raw_input, use_demo=use_demo)
    service = nlp_service or NLPService()
    output, source_mode = service.analyze_text(
        request.raw_input,
        title=request.title,
        force_demo=request.use_demo,
    )
    return create_analysis_session(
        db,
        raw_input=request.raw_input,
        output=output,
        source_mode=source_mode,
        title=request.title,
    )
