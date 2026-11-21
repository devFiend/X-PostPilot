"""
Configuration manager using Pydantic Settings.
"""

from pathlib import Path
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # AI Providers
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GEMINI_API_KEY: str | None = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3:8b"
    DEFAULT_AI_PROVIDER: str = "groq"

    # Telegram
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_OWNER_ID: int | None = None

    # Hosting & Redirects (Auto-populated by Render or custom domain)
    RENDER_EXTERNAL_URL: str | None = None
    APP_URL: str | None = None

    # Official X API
    X_API_KEY: str | None = None
    X_API_SECRET: str | None = None
    X_ACCESS_TOKEN: str | None = None
    X_ACCESS_TOKEN_SECRET: str | None = None
    X_CLIENT_ID: str | None = None
    X_CLIENT_SECRET: str | None = None

    # Publishing settings
    DEFAULT_PUBLISH_METHOD: str = "manual"  # 'manual' or 'x_api'
    DEFAULT_PUBLISH_MODE: str = "approval"  # 'approval' or 'autopilot'

    # General
    TIMEZONE: str = "Africa/Lagos"
    MAX_POSTS_PER_DAY: int = 3
    POSTPILOT_DB_PATH: str = "postpilot.db"
    LOG_LEVEL: str = "INFO"

    @property
    def base_url(self) -> str | None:
        """Returns the public base URL if running on Render or custom cloud host."""
        return self.APP_URL or self.RENDER_EXTERNAL_URL

    @field_validator("TELEGRAM_OWNER_ID", mode="before")
    @classmethod
    def parse_owner_id(cls, v: Any) -> Any:
        if v == "" or v is None:
            return None
        return int(v)

    @field_validator(
        "GROQ_API_KEY",
        "GEMINI_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "RENDER_EXTERNAL_URL",
        "APP_URL",
        "X_API_KEY",
        "X_API_SECRET",
        "X_ACCESS_TOKEN",
        "X_ACCESS_TOKEN_SECRET",
        "X_CLIENT_ID",
        "X_CLIENT_SECRET",
        mode="before",
    )
    @classmethod
    def parse_empty_strings(cls, v: Any) -> Any:
        if v == "" or v is None:
            return None
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
