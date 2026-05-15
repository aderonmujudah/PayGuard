from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "PayGuard"
    ENV: Literal["dev", "prod"] = "dev"
    API_PREFIX: str = "/api"
    SECRET_KEY: str = "change-me-in-prod"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    CORS_ORIGINS: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://payguard:payguard@localhost:5432/payguard"

    # Redis / jobs
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_BACKGROUND_JOBS: bool = False

    # File storage
    STORAGE_BACKEND: Literal["local", "s3"] = "local"
    LOCAL_STORAGE_DIR: str = "./storage"
    S3_BUCKET: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    PUBLIC_FILE_BASE_URL: str = "http://localhost:8000/api/files"

    # Model inference
    INVOICE_EXTRACTION_MODE: Literal["heuristic", "local_model", "hybrid"] = "hybrid"
    LOCAL_MODEL_DIR: str = "/models/invoice_extractor"

    # OCR
    OCR_ENABLED: bool = True
    TESSERACT_CMD: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
