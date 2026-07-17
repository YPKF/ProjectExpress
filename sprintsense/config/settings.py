"""Application settings loaded from environment variables."""

import os
import logging
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application configuration loaded from .env file."""

    # ── LLM ──────────────────────────────────
    llm_api_base_url: str = Field("https://api.openai.com/v1", validation_alias="LLM_API_BASE_URL")
    openai_api_key: str = Field("", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o", validation_alias="OPENAI_MODEL")

    # ── JIRA ─────────────────────────────────
    jira_base_url: str = Field("", validation_alias="JIRA_BASE_URL")
    jira_email: str = Field("", validation_alias="JIRA_EMAIL")
    jira_api_token: str = Field("", validation_alias="JIRA_API_TOKEN")
    jira_project_key: str = Field("", validation_alias="JIRA_PROJECT_KEY")

    # ── GITHUB ───────────────────────────────
    github_token: str = Field("", validation_alias="GITHUB_TOKEN")
    github_repo_owner: str = Field("", validation_alias="GITHUB_REPO_OWNER")
    github_repo_name: str = Field("", validation_alias="GITHUB_REPO_NAME")

    # ── SLACK ────────────────────────────────
    slack_bot_token: str = Field("", validation_alias="SLACK_BOT_TOKEN")
    slack_channel_id: str = Field("", validation_alias="SLACK_CHANNEL_ID")
    slack_signing_secret: str = Field("", validation_alias="SLACK_SIGNING_SECRET")

    # ── APP CONFIG ───────────────────────────
    app_env: str = Field("development", validation_alias="APP_ENV")
    app_port: int = Field(8000, validation_alias="APP_PORT")
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")

    # ── SPRINT CONFIG ────────────────────────
    sprint_check_interval_minutes: int = Field(30, validation_alias="SPRINT_CHECK_INTERVAL_MINUTES")
    sprint_risk_threshold: float = Field(0.6, validation_alias="SPRINT_RISK_THRESHOLD")
    blocker_keywords: str = Field(
        "blocked,blocker,stuck,waiting,dependency",
        validation_alias="BLOCKER_KEYWORDS",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    def get_blocker_keywords_list(self) -> list[str]:
        """Parse blocker keywords string into a list."""
        return [kw.strip().lower() for kw in self.blocker_keywords.split(",") if kw.strip()]

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env.lower() == "development"

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()


def setup_logging() -> None:
    """Configure Python logging based on settings."""
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)-25s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
