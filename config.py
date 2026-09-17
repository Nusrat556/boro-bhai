"""Configuration for BORO BHAI."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer.") from exc


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    environment: str = "development"
    debug: bool = False
    ollama_url: str = "http://127.0.0.1:11434/api/generate"
    model_name: str = "qwen2.5:3b"
    api_max_content_length: int = 10 * 1024 * 1024
    max_upload_bytes: int = 5 * 1024 * 1024
    max_message_length: int = 4000
    max_query_length: int = 250
    max_job_text_length: int = 20000
    reports_dir: str = "reports"
    db_path: str = "data/boro_bhai.db"
    tracing_enabled: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        environment = os.getenv("BORO_BHAI_ENV", "development").strip().lower()
        if environment not in {"development", "production", "test"}:
            raise ValueError("BORO_BHAI_ENV must be one of: development, production, test.")

        debug = os.getenv("BORO_BHAI_DEBUG", "false").strip().lower() in {"1", "true", "yes"}

        return cls(
            environment=environment,
            debug=debug,
            ollama_url=os.getenv("BORO_BHAI_OLLAMA_URL", "http://127.0.0.1:11434/api/generate"),
            model_name=os.getenv("BORO_BHAI_MODEL_NAME", "qwen2.5:3b"),
            api_max_content_length=_int_env("BORO_BHAI_API_MAX_CONTENT_LENGTH", 10 * 1024 * 1024),
            max_upload_bytes=_int_env("BORO_BHAI_MAX_UPLOAD_BYTES", 5 * 1024 * 1024),
            max_message_length=_int_env("BORO_BHAI_MAX_MESSAGE_LENGTH", 4000),
            max_query_length=_int_env("BORO_BHAI_MAX_QUERY_LENGTH", 250),
            max_job_text_length=_int_env("BORO_BHAI_MAX_JOB_TEXT_LENGTH", 20000),
            reports_dir=os.getenv("BORO_BHAI_REPORTS_DIR", "reports"),
            db_path=os.getenv("BORO_BHAI_DB_PATH", "data/boro_bhai.db"),
            tracing_enabled=os.getenv("BORO_BHAI_TRACING_ENABLED", "false").strip().lower() in {"1", "true", "yes"},
        )


settings = Settings.from_env()
