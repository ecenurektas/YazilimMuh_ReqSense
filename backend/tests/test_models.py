"""SQLAlchemy ORM modelleri, ilişkiler, cascade delete ve kalıcılık servisi testleri."""

from collections.abc import Generator

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.database import create_db_engine, init_db
from app.models.analysis import (
    AcceptanceCriterion,
    AnalysisSession,
    Requirement,
    UserStory,
)
from app.schemas.analysis import (
    AnalysisSessionDetail,
    LLMAcceptanceCriterion,
    LLMAnalysisOutput,
    LLMRequirement,
    LLMUserStory,
)
from app.services.nlp_service import NLPService
from app.services.session_service import (
    analyze_and_save,
    create_analysis_session,
    delete_session,
    get_session_by_id,
    list_sessions,
)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Her test için izole bellek içi SQLite veritabanı ve oturumu sağlar."""
    engine = create_db_engine("sqlite:///:memory:")
    init_db(engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = testing_session_local()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _sample_output() -> LLMAnalysisOutput:
    return LLMAnalysisOutput(
        project_title="Kütüphane Randevu Sistemi",
        summary="Öğrencilerin çalışma odası ayırtmasını sağlayan sistem özeti.",
        requirements=[
            LLMRequirement(
                code="FR-01",
                req_type="functional",
                category="Rezervasyon",
                title="Çalışma Odası Rezervasyonu",
                description="Öğrenciler uygun saat dilimleri için çalışma odası ayırtabilmelidir.",
                moscow_priority="Must",
                ambiguity_warning=None,
            ),
            LLMRequirement(
                code="NFR-01",
                req_type="non_functional",
                category="Performans",
                title="Sayfa Yanıt Süresi",
                description="Müsaitlik sorguları normal yükte 500 ms altında yanıt vermelidir.",
                moscow_priority="Should",
                ambiguity_warning="Yoğun sınav dönemleri için eşzamanlı kullanıcı sayısı belirtilmelidir.",
            ),
        ],
        user_stories=[
            LLMUserStory(
                code="US-01",
                related_requirement_code="FR-01",
                role="Öğrenci",
                goal="boş çalışma odalarını görüp rezervasyon yapabilmek",
                benefit="kütüphaneye gitmeden yerimi garanti altına alabilirim",
                acceptance_criteria=[
                    LLMAcceptanceCriterion(
                        code="AC-01.1",
                        given_clause="Öğrenci sisteme giriş yapmıştır ve müsait bir oda seçmiştir",
                        when_clause="Rezervasyonu onayla butonuna tıklandığında",
                        then_clause="Rezervasyon kaydedilir ve saat dilimi dolu olarak işaretlenir",
                    ),
                ],
            ),
        ],
    )


def test_create_and_read_session_with_traceability(db_session: Session) -> None:
    """Oturum, gereksinim, kullanıcı hikâyesi ve kabul kriterlerinin ilişkili kaydedildiğini doğrular."""
    raw_input = "Öğrenciler kütüphanedeki çalışma odalarını çevrimiçi olarak hızlıca rezerve edebilsin."
    created = create_analysis_session(
        db_session,
        raw_input=raw_input,
        output=_sample_output(),
        source_mode="llm",
    )

    assert created.id > 0
    assert created.title == "Kütüphane Randevu Sistemi"
    assert created.source_mode == "llm"
    assert len(created.requirements) == 2
    assert len(created.user_stories) == 1

    story = created.user_stories[0]
    fr01 = next(req for req in created.requirements if req.code == "FR-01")
    assert story.requirement_id == fr01.id
    assert story.related_requirement_code == "FR-01"
    assert len(story.acceptance_criteria) == 1
    assert story.acceptance_criteria[0].code == "AC-01.1"

    detail = AnalysisSessionDetail.model_validate(created)
    assert detail.id == created.id
    assert len(detail.requirements) == 2
    assert len(detail.user_stories[0].acceptance_criteria) == 1


def test_delete_session_cascades_all_child_rows(db_session: Session) -> None:
    """Bir oturum silindiğinde bağlı tüm alt kayıtların cascade ile temizlendiğini doğrular."""
    created = create_analysis_session(
        db_session,
        raw_input="Kütüphane çalışma odası rezervasyon modülü için gereksinim analizi metni.",
        output=_sample_output(),
        source_mode="demo",
    )

    assert delete_session(db_session, created.id) is True
    assert get_session_by_id(db_session, created.id) is None
    assert delete_session(db_session, created.id) is False

    assert db_session.scalar(select(func.count(AnalysisSession.id))) == 0
    assert db_session.scalar(select(func.count(Requirement.id))) == 0
    assert db_session.scalar(select(func.count(UserStory.id))) == 0
    assert db_session.scalar(select(func.count(AcceptanceCriterion.id))) == 0


def test_deleting_requirement_sets_user_story_fk_to_null(db_session: Session) -> None:
    """Bir gereksinim silindiğinde bağlı UserStory kaydının silinmeyip requirement_id=None olduğunu doğrular."""
    created = create_analysis_session(
        db_session,
        raw_input="Öğrenciler için kütüphane çalışma odası rezervasyon takip uygulaması.",
        output=_sample_output(),
        source_mode="llm",
    )
    fr01 = next(req for req in created.requirements if req.code == "FR-01")

    db_session.delete(fr01)
    db_session.commit()
    db_session.expire_all()

    stories = list(db_session.scalars(select(UserStory)).all())
    assert len(stories) == 1
    assert stories[0].requirement_id is None
    assert stories[0].related_requirement_code == "FR-01"


def test_analyze_and_save_with_demo_mode_and_list_sessions(db_session: Session) -> None:
    """DEMO_MODE=true ile uçtan uca analiz ve oturum listeleme akışını doğrular."""
    demo_nlp = NLPService(settings_obj=Settings(demo_mode=True, gemini_api_key=""))

    first = analyze_and_save(
        db_session,
        title="İlk Proje",
        raw_input="Sistem hızlı çalışsın, arayüz kullanıcı dostu olsun ve veriler güvenli saklansın.",
        nlp_service=demo_nlp,
    )
    second = analyze_and_save(
        db_session,
        title="İkinci Proje",
        raw_input="Müşteriler sipariş durumlarını canlı izleyebilsin ve fatura indirebilsin.",
        nlp_service=demo_nlp,
    )

    sessions = list_sessions(db_session)
    assert [s.id for s in sessions] == [second.id, first.id]
    assert first.source_mode == "demo"
    assert len(first.requirements) == 6
    assert len(first.user_stories) == 3

    loaded = get_session_by_id(db_session, first.id)
    assert loaded is not None
    assert loaded.title == "İlk Proje"
    assert any(req.ambiguity_warning for req in loaded.requirements)
