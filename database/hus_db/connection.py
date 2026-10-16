"""SQLAlchemy engine factory for the AI-07 HUS Neon database."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine

from database.hus_db.config import HusDatabaseConfig, load_config


def create_engine_for(config: HusDatabaseConfig, *, pool_pre_ping: bool = True) -> Engine:
    """Build an engine that keeps TLS and re-checks pooled connections."""
    return create_engine(config.engine_url(), pool_pre_ping=pool_pre_ping, future=True)


def connect(config: HusDatabaseConfig | None = None) -> Engine:
    """Load configuration from the environment and build an engine.

    Raises :class:`database.hus_db.config.HusDatabaseConfigError` when
    ``HUS_DATABASE_URL`` is missing or malformed.
    """
    return create_engine_for(config or load_config())
