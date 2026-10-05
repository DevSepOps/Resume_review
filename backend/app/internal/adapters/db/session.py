from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.pkg.config import Settings


def create_db_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.DATABASE_URL, pool_pre_ping=True, echo=settings.DB_ECHO
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
