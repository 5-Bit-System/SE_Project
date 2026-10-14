"""Compatible catalog entry points; runtime storage is explicitly configured."""

from pathlib import Path

from app.catalog_validation import validate_curriculum_selections
from app.config import get_settings
from app.errors import CatalogError
from app.infrastructure import json_catalog_repository as json_repository
from app.models import Catalog


DATA_ROOT = json_repository.DATA_ROOT


def load_catalog(program_id: str, root: Path | None = None) -> Catalog:
    if root is not None or get_settings().storage_backend == "json":
        return json_repository.load_catalog(program_id, root or DATA_ROOT)
    from app.infrastructure.postgres_repository import PostgresRepository

    return PostgresRepository().load_catalog(program_id)


def list_catalogs(root: Path | None = None) -> list[Catalog]:
    if root is not None or get_settings().storage_backend == "json":
        return json_repository.list_catalogs(root or DATA_ROOT)
    from app.infrastructure.postgres_repository import PostgresRepository

    return PostgresRepository().list_catalogs()


__all__ = [
    "Catalog",
    "CatalogError",
    "DATA_ROOT",
    "list_catalogs",
    "load_catalog",
    "validate_curriculum_selections",
]
