"""Environment-driven settings (see docs/architecture/contracts.md section 2)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_PROD_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    JWT_SECRET_KEY: str = Field(min_length=1)
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    CORS_ORIGINS: str = ""
    UPLOAD_DIR: str = "/app/data/uploads"
    MAX_UPLOAD_MB: int = Field(default=10, gt=0)
    ACCESS_TOKEN_TTL_SECONDS: int = Field(default=900, gt=0)
    REFRESH_TOKEN_TTL_SECONDS: int = Field(default=86400, gt=0)
    LOG_LEVEL: str = "INFO"
    DB_ECHO: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @model_validator(mode="after")
    def _check_security(self) -> "Settings":
        if (
            self.ENVIRONMENT == "production"
            and len(self.JWT_SECRET_KEY) < MIN_PROD_SECRET_LENGTH
        ):
            raise ValueError(
                f"JWT_SECRET_KEY must be at least {MIN_PROD_SECRET_LENGTH} "
                "characters when ENVIRONMENT=production"
            )
        if "*" in self.cors_origins_list:
            raise ValueError(
                "CORS_ORIGINS must list exact origins; '*' is not allowed "
                "because credentials are enabled"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
