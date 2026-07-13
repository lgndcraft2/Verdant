from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field

# Default hosted VERDANT API. Baked in so `VerdantClient(api_key=...)` works with no
# base_url; override with the VERDANT_API_URL env var or base_url=/settings=.
DEFAULT_API_URL = "https://verdant-be.onrender.com"


def _split_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    verdant_api_key: str = ""
    verdant_api_url: str = DEFAULT_API_URL
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    redis_url: str = "redis://localhost:6379/0"
    webhook_secret: str = ""
    environment: str = "development"
    log_level: str = "info"
    trust_score_alert_threshold: int = Field(default=40, ge=0, le=100)
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    claude_model: str = "claude-sonnet-4-6"
    gemini_model: str = "gemini-2.5-flash"
    request_timeout_seconds: float = 30.0
    webhook_timeout_seconds: float = 10.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            verdant_api_key=os.getenv("VERDANT_API_KEY", ""),
            verdant_api_url=os.getenv("VERDANT_API_URL", DEFAULT_API_URL),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            webhook_secret=os.getenv("WEBHOOK_SECRET", ""),
            environment=os.getenv("ENVIRONMENT", "development"),
            log_level=os.getenv("LOG_LEVEL", "info"),
            trust_score_alert_threshold=int(os.getenv("TRUST_SCORE_ALERT_THRESHOLD", "40")),
            cors_origins=_split_csv(os.getenv("CORS_ORIGINS"), ["*"]),
            claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
            webhook_timeout_seconds=float(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "10")),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
