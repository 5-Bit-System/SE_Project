"""Select the configured PostgreSQL catalog repository."""

from app.config import get_settings


def postgres_repository():
    """Return the HUS runtime or the explicitly selected legacy adapter."""
    if get_settings().database_model == "legacy":
        from app.infrastructure.postgres_repository import PostgresRepository

        return PostgresRepository()

    from app.infrastructure.hus_repository import HusRepository

    return HusRepository()
