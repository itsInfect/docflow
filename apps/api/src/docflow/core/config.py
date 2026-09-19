from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DOCFLOW_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    database_url: str = "sqlite+aiosqlite:///./storage/docflow.db"
    auto_create_schema: bool = True
    redis_url: str = "redis://localhost:6379/0"

    storage_root: Path = Path("storage")
    max_upload_size_mb: int = 20

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "docflow"
    s3_secret_key: str = "docflow-secret"
    s3_bucket: str = "documents"

    llm_provider: str = "mock"
    anthropic_api_key: str | None = None
    jwt_secret: str = "replace-in-production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
