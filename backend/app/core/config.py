from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["dev", "test", "prod"] = "dev"
    app_name: str = "Lexora AI"

    database_url: str = "postgresql+asyncpg://lexora:lexora@localhost:5432/lexora"
    db_null_pool: bool = False
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = "change-me-in-production-use-a-long-random-string"
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    cookie_secure: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]
    trust_proxy: bool = True

    # AI
    ai_provider: Literal["gemini", "fake", "none"] = "gemini"
    gemini_api_key: str | None = None
    gemini_model_smart: str = "gemini-3.8-flash"
    gemini_model_fast: str = "gemini-3.5-flash-lite"
    gemini_model_tts: str = "gemini-3.8-flash-lite-tts"
    gemini_tts_voice: str = "Kore"
    ai_timeout_seconds: int = 60
    ai_publish_threshold: float = 0.6
    ai_reject_threshold: float = 0.3

    # Background jobs: "inline" runs in the API process (dev/test), "celery" uses the worker.
    tasks_mode: Literal["inline", "celery"] = "inline"

    # Storage for audio files
    storage_backend: Literal["local", "s3"] = "local"
    storage_local_dir: str = "./storage"
    s3_endpoint_url: str | None = None
    s3_bucket: str = "lexora"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_region: str = "us-east-1"

    search_rate_limit_per_minute: int = 60

    @property
    def ai_available(self) -> bool:
        if self.ai_provider == "fake":
            return True
        return self.ai_provider == "gemini" and bool(self.gemini_api_key)


# Daily quotas per plan. Staff (editor/admin) are not limited.
QUOTAS: dict[str, dict[str, int]] = {
    "anon": {"ai_explain": 5, "ai_generate": 3, "translate_chars": 2_000, "tts": 30},
    "free": {"ai_explain": 20, "ai_generate": 10, "translate_chars": 10_000, "tts": 100},
    "pro": {"ai_explain": 500, "ai_generate": 100, "translate_chars": 200_000, "tts": 2_000},
}

# Max characters for a single translation request.
TRANSLATE_MAX_CHARS = {"anon": 1_000, "free": 1_000, "pro": 5_000}

# USD per 1M tokens (input, output). Approximate, used for cost tracking only.
AI_PRICING: dict[str, tuple[float, float]] = {
    "gemini-3.8-flash": (0.75, 3.75),
    "gemini-3.5-flash-lite": (0.30, 2.50),
    "gemini-3.8-flash-lite-tts": (0.50, 6.00),
    "fake": (0.0, 0.0),
}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
