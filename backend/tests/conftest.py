import os

# Must be set before app modules read settings.
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-test-secret-key-0123456789")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.api.http.app import create_app
from app.api.http.dependencies import Container
from app.internal.adapters.db import Base
from app.internal.adapters.security import BcryptHasher
from app.pkg.config import Settings


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        _env_file=None,
        DATABASE_URL="sqlite://",
        JWT_SECRET_KEY="test-secret-key-test-secret-key-0123456789",
        ENVIRONMENT="test",
        UPLOAD_DIR=str(tmp_path / "uploads"),
        MAX_UPLOAD_MB=1,
        CORS_ORIGINS="http://localhost:8001",
    )


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def container(settings, engine) -> Container:
    return Container(settings, engine=engine, hasher=BcryptHasher(rounds=4))


@pytest.fixture
def client(settings, container) -> TestClient:
    app = create_app(settings, container)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
