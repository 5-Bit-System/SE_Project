"""Server configuration, loaded explicitly from the repository's .env."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, repr=False)
class Settings:
    storage_backend: str
    database_url: str
    gemini_api_key: str
    gemini_base_url: str
    gemini_model: str
    recommendation_llm_enabled: bool


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    backend = os.getenv("STORAGE_BACKEND", "postgres").strip().lower()
    if backend not in {"postgres", "json"}:
        raise ValueError("STORAGE_BACKEND must be postgres or json")
    database_url = os.getenv("DATABASE_URL", "").strip()
    if backend == "postgres":
        try:
            url = make_url(database_url)
            valid = url.get_backend_name() == "postgresql" and bool(url.database)
        except (ArgumentError, ValueError):
            valid = False
        if not valid:
            raise ValueError("DATABASE_URL must identify a PostgreSQL database")
    return Settings(
        storage_backend=backend,
        database_url=database_url,
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_base_url=os.getenv("GEMINI_BASE_URL", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash",
        recommendation_llm_enabled=os.getenv("RECOMMENDATION_LLM_ENABLED", "true")
        .strip()
        .casefold()
        not in {"0", "false", "no", "off"},
    )
