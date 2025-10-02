from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    # connect_args={"check_same_thread": False} # Just for Sqlite
)

session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = session_local()

    try:
        yield db
    finally:
        db.close()