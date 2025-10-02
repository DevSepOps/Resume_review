from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # ✅ Change to match .env variable name
    SQLALCHEMY_DATABASE_URL: Optional[str] = None
    JWT_SECRET_KEY: str
    SECRET_KEY: str = "supersecretkey"
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()