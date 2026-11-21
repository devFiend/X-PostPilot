"""
Configuration manager using Pydantic Settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # AI Providers
    GROQ_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3:8b"
    DEFAULT_AI_PROVIDER: str = "groq"

    # Telegram
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_OWNER_ID: int | None = None

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
