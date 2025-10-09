from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: Optional[str] = None
    JWT_SECRET_KEY: str = "fallback-secret"
    SECRET_KEY: str = "fallback-secret-2"
    
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
