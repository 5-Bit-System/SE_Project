"""SQLAlchemy engine factory for the AI-07 HUS Neon database."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine

from database.hus_db.config import HusDatabaseConfig, load_config

# Neon's pooled endpoint can leave a TCP connect hanging; libpq's
# ``connect_timeout`` makes the engine fail fast instead of blocking forever.
DEFAULT_CONNECT_TIMEOUT = 15


def create_engine_for(
    config: HusDatabaseConfig,
    *,
    pool_pre_ping: bool = True,
    connect_timeout: int | None = DEFAULT_CONNECT_TIMEOUT,
) -> Engine:
    """Build an engine that keeps TLS and re-checks pooled connections."""
    connect_args: dict[str, object] = {}
    if connect_timeout:
        connect_args["connect_timeout"] = connect_timeout
    return create_engine(
        config.engine_url(),
        pool_pre_ping=pool_pre_ping,
        connect_args=connect_args,
        future=True,
    )


def connect(config: HusDatabaseConfig | None = None) -> Engine:
    """Load configuration from the environment and build an engine.

    Raises :class:`database.hus_db.config.HusDatabaseConfigError` when
    ``HUS_DATABASE_URL`` is missing or malformed.
    """
    return create_engine_for(config or load_config())
