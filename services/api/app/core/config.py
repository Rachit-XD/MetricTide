"""Application configuration.

Settings are loaded from environment variables (and an optional `.env` file)
and validated eagerly at startup via pydantic-settings. Import the cached
`get_settings()` accessor rather than instantiating `Settings` directly.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogFormat(str, Enum):
    CONSOLE = "console"
    JSON = "json"


class Settings(BaseSettings):
    """Typed, validated application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- General ----
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    log_level: str = Field(default="INFO")
    log_format: LogFormat = Field(default=LogFormat.CONSOLE)

    # ---- API ----
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_secret_key: str = Field(default="change-me-in-production")
    api_cors_origins: str = Field(default="http://localhost:3000")

    # ---- Datastores ----
    database_url: str = Field(
        default="postgresql+asyncpg://metrictide:metrictide@localhost:5432/metrictide",
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ---- Kafka (deferred) ----
    kafka_bootstrap_servers: str | None = Field(default=None)

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def cors_origins(self) -> list[str]:
        """CORS origins as a list (comma-separated in the env var)."""
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()
