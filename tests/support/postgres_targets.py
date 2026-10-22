"""Fail-closed connection targets for tests that can issue PostgreSQL DDL."""

from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


def _validate_test_target(raw_url: str, database: str) -> URL:
    try:
        target = make_url(raw_url)
    except ArgumentError as exc:
        raise ValueError(f"Database tests require local {database}") from exc
    if (
        target.drivername not in {"postgresql", "postgresql+psycopg2"}
        or target.host not in {"127.0.0.1", "localhost"}
        or target.database != database
        or set(target.query) - {"sslmode"}
    ):
        raise ValueError(f"Database tests require local {database}")
    return target


def validate_hus_test_target(raw_url: str) -> URL:
    return _validate_test_target(raw_url, "ai07")


def validate_legacy_test_target(raw_url: str) -> URL:
    return _validate_test_target(raw_url, "se_project_test")
