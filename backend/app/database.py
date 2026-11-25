"""SQLAlchemy veritabanı motoru, oturum yönetimi ve tablo başlatma yardımcıları."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings


class Base(DeclarativeBase):
    """Tüm SQLAlchemy ORM modelleri için temel sınıf."""


def create_db_engine(database_url: str) -> Engine:
    """Verilen veritabanı URL'si için yapılandırılmış SQLAlchemy motoru oluşturur."""
    is_sqlite = database_url.startswith("sqlite")
    engine_kwargs: dict[str, object] = {}

    if is_sqlite:
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if database_url == "sqlite:///:memory:" or database_url.endswith(":memory:"):
            engine_kwargs["poolclass"] = StaticPool

    db_engine = create_engine(database_url, **engine_kwargs)

    if is_sqlite:
        @event.listens_for(db_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection: object, _connection_record: object) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return db_engine


engine = create_db_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(target_engine: Engine | None = None) -> None:
    """ORM modellerini içe aktarır ve eksik tabloları veritabanında oluşturur."""
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=target_engine or engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI bağımlılık enjeksiyonu için veritabanı oturumu sağlar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
