"""Central configuration — env-driven, typed, fail-fast."""

from __future__ import annotations

import logging
import sys
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"


def setup_logging(*, verbose: bool = False) -> None:
    """Configure root logger with a clean format."""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s"
    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt="%H:%M:%S",
        stream=sys.stderr,
        force=True,
    )
    # Quiet noisy third-party loggers
    for noisy in ("httpx", "httpcore", "urllib3", "openai", "anthropic"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Identity
    leetcode_username: str = Field(default="pYwmntvkNk", alias="LEETCODE_USERNAME")
    leetcode_session: str | None = Field(default=None, alias="LEETCODE_SESSION")

    # GitHub streak target
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")
    github_repo: str = Field(default="Aayush-pixel29/leetcode", alias="GITHUB_REPO")
    github_branch: str = Field(default="main", alias="GITHUB_BRANCH")

    # LLM
    llm_provider: str = Field(default="ollama", alias="LLM_PROVIDER")  # ollama|openai|anthropic|gemini
    llm_model: str = Field(default="llama3", alias="LLM_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")

    # Notifications
    gmail_address: str | None = Field(default=None, alias="GMAIL_ADDRESS")
    gmail_app_password: str | None = Field(default=None, alias="GMAIL_APP_PASSWORD")

    # Runtime
    dry_run: bool = Field(default=False, alias="DRY_RUN")
    output_dir: Path = Field(default=OUTPUT_DIR)


@lru_cache
def get_settings() -> Settings:
    return Settings()
