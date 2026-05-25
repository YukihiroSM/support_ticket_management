from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["local", "test", "staging", "production"] = "local"
    log_level: str = "INFO"
    api_title: str = "Support Ticket Manager"
    api_version: str = "0.1.0"

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/support_tickets"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    aws_endpoint_url: str | None = None
    aws_access_key_id: str = "test"
    aws_secret_access_key: str = "test"
    aws_default_region: str = "us-east-1"

    sqs_queue_url: str = "http://localhost:4566/000000000000/ticket-processing"

    worker_poll_wait_seconds: int = 20
    worker_max_messages: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
