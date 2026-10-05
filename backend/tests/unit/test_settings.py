import pytest
from pydantic import ValidationError

from app.pkg.config import Settings

BASE = dict(_env_file=None, DATABASE_URL="sqlite://")


def test_database_url_required(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None, JWT_SECRET_KEY="x" * 40)


def test_jwt_secret_required(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(ValidationError):
        Settings(**BASE)


def test_production_requires_long_secret():
    with pytest.raises(ValidationError, match="at least 32"):
        Settings(**BASE, JWT_SECRET_KEY="short", ENVIRONMENT="production")
    Settings(**BASE, JWT_SECRET_KEY="x" * 32, ENVIRONMENT="production")
    Settings(**BASE, JWT_SECRET_KEY="short", ENVIRONMENT="development")


def test_cors_parsing_and_wildcard_rejected():
    s = Settings(**BASE, JWT_SECRET_KEY="k", CORS_ORIGINS="http://a.com, http://b.com,")
    assert s.cors_origins_list == ["http://a.com", "http://b.com"]
    assert Settings(**BASE, JWT_SECRET_KEY="k").cors_origins_list == []
    with pytest.raises(ValidationError):
        Settings(**BASE, JWT_SECRET_KEY="k", CORS_ORIGINS="*")


def test_defaults():
    s = Settings(**BASE, JWT_SECRET_KEY="k")
    assert s.DB_ECHO is False and s.MAX_UPLOAD_MB == 10
    assert s.ACCESS_TOKEN_TTL_SECONDS == 900 and s.REFRESH_TOKEN_TTL_SECONDS == 86400
    assert s.UPLOAD_DIR == "/app/data/uploads"
