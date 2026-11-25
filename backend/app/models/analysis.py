"""ReqSense ilişkisel veri modeli (SQLAlchemy ORM sınıfları)."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utc_now() -> datetime:
    """UTC zaman damgası döndürür."""
    return datetime.now(timezone.utc)


class AnalysisSession(Base):
    """Bir doğal dil gereksinim analizi oturumunu temsil eder."""

    __tablename__ = "analysis_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_input: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="llm")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )

    requirements: Mapped[list["Requirement"]] = relationship(
        "Requirement",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="Requirement.id",
        passive_deletes=True,
    )
    user_stories: Mapped[list["UserStory"]] = relationship(
        "UserStory",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="UserStory.id",
        passive_deletes=True,
    )

    @property
    def requirement_count(self) -> int:
        """Oturumdaki toplam gereksinim sayısını döndürür."""
        return len(self.requirements)

    @property
    def user_story_count(self) -> int:
        """Oturumdaki toplam kullanıcı hikâyesi sayısını döndürür."""
        return len(self.user_stories)

    @property
    def ambiguity_count(self) -> int:
        """Belirsizlik uyarısı içeren gereksinim sayısını döndürür."""
        return sum(1 for req in self.requirements if req.ambiguity_warning)


class Requirement(Base):
    """Oturuma bağlı fonksiyonel (FR) veya fonksiyonel olmayan (NFR) gereksinim kaydı."""

    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    req_type: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    moscow_priority: Mapped[str] = mapped_column(String(16), nullable=False)
    ambiguity_warning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    session: Mapped["AnalysisSession"] = relationship("AnalysisSession", back_populates="requirements")
    user_stories: Mapped[list["UserStory"]] = relationship("UserStory", back_populates="requirement")


class UserStory(Base):
    """Gereksinimle ilişkilendirilebilen Agile kullanıcı hikâyesi (Rol-Hedef-Fayda)."""

    __tablename__ = "user_stories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("analysis_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requirement_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("requirements.id", ondelete="SET NULL"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    related_requirement_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    role: Mapped[str] = mapped_column(String(128), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    benefit: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped["AnalysisSession"] = relationship("AnalysisSession", back_populates="user_stories")
    requirement: Mapped[Optional["Requirement"]] = relationship("Requirement", back_populates="user_stories")
    acceptance_criteria: Mapped[list["AcceptanceCriterion"]] = relationship(
        "AcceptanceCriterion",
        back_populates="user_story",
        cascade="all, delete-orphan",
        order_by="AcceptanceCriterion.id",
        passive_deletes=True,
    )


class AcceptanceCriterion(Base):
    """Kullanıcı hikâyesine ait Given-When-Then kabul kriteri."""

    __tablename__ = "acceptance_criteria"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_story_id: Mapped[int] = mapped_column(
        ForeignKey("user_stories.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    given_clause: Mapped[str] = mapped_column(Text, nullable=False)
    when_clause: Mapped[str] = mapped_column(Text, nullable=False)
    then_clause: Mapped[str] = mapped_column(Text, nullable=False)

    user_story: Mapped["UserStory"] = relationship("UserStory", back_populates="acceptance_criteria")
