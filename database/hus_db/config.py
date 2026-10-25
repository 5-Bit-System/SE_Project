"""Configuration helpers for the AI-07 HUS PostgreSQL database.

The connection string carries a password and is therefore a secret: it must come
from the environment (``HUS_DATABASE_URL``) and must never be committed. These
helpers only read and normalise configuration; they never open a connection.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
from urllib.parse import urlsplit, urlunsplit

from dotenv import dotenv_values

ENV_VAR = "HUS_DATABASE_URL"
DEFAULT_SSLMODE = "require"
LOCAL_ENV_FILE = Path(__file__).resolve().parents[1] / ".env.docker"


class HusDatabaseConfigError(RuntimeError):
    """Raised when the HUS database connection string is missing or malformed."""


def is_postgres_url(url: str) -> bool:
    """Return ``True`` when ``url`` looks like a PostgreSQL connection string."""
    try:
        scheme = urlsplit(url).scheme
    except ValueError:
        return False
    return scheme.startswith("postgres")


def redact_url(url: str) -> str:
    """Return ``url`` with any password replaced by ``***`` for safe logging."""
    if not url:
        return url
    try:
        parts = urlsplit(url)
    except ValueError:
        return "***"
    if "@" not in parts.netloc:
        return url
    userinfo, _, host = parts.netloc.rpartition("@")
    if ":" in userinfo:
        user, _, _password = userinfo.partition(":")
        netloc = f"{user}:***@{host}"
    else:
        netloc = parts.netloc
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def with_ssl_required(url: str) -> str:
    """Ensure the connection string asks for TLS, which Neon requires."""
    if "sslmode=" in url:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}sslmode={DEFAULT_SSLMODE}"


@dataclass(frozen=True)
class HusDatabaseConfig:
    """A validated HUS database connection target."""

    url: str
    env_var: str = ENV_VAR

    @property
    def safe_url(self) -> str:
        """The connection string with the password masked."""
        return redact_url(self.url)

    def engine_url(self) -> str:
        """Default to TLS; preserve explicit settings such as Docker loopback SSL off."""
        return with_ssl_required(self.url)


def load_config(env: Mapping[str, str] | None = None) -> HusDatabaseConfig:
    """Read and validate the connection string from the environment.

    An explicit mapping is read in isolation. Otherwise, process variables
    override the optional ``database/.env.docker`` file.
    """
    source = env
    if source is None:
        # Explicit process settings override the optional local Docker configuration.
        source = {**dotenv_values(LOCAL_ENV_FILE), **os.environ}
    raw = (source.get(ENV_VAR) or "").strip()
    if not raw:
        raise HusDatabaseConfigError(
            f"{ENV_VAR} is not set. Export the Neon connection string first, e.g.\n"
            f'  export {ENV_VAR}="postgresql://user:password@host/ai07?sslmode=require"'
        )
    if not is_postgres_url(raw):
        raise HusDatabaseConfigError(
            f"{ENV_VAR} must be a postgresql:// URL, got scheme {urlsplit(raw).scheme!r}"
        )
    return HusDatabaseConfig(url=raw)
