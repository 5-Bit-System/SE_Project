"""Read the active, immutable catalog snapshots in the HUS database."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

from pydantic import ValidationError
from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.catalog_validation import validate_catalog
from app.db.session import get_engine
from app.errors import CatalogError, StorageDataError, StorageUnavailable
from app.models import Catalog
from app.transcript import resolve_program_id
from database.hus_db.runtime import EXPECTED_PROGRAM_IDS, PROGRAM_MAJOR_IDS, catalog_revision

logger = logging.getLogger(__name__)
HEAD = "hus_20261017_02"


class HusRepository:
    def __init__(self, engine: Engine | None = None) -> None:
        # Runtime config deliberately uses the app's DATABASE_URL. HUS_DATABASE_URL
        # is reserved for isolated migration and publication tools.
        self.engine = engine if engine is not None else get_engine()

    @contextmanager
    def connection(self) -> Iterator[Connection]:
        try:
            with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn:
                yield conn
        except SQLAlchemyError as exc:
            logger.error("HUS storage operation failed: %s", type(exc).__name__)
            raise StorageUnavailable("HUS PostgreSQL is unavailable") from None
        except (ValidationError, ValueError, TypeError, KeyError) as exc:
            if isinstance(exc, CatalogError):
                raise
            logger.error("Invalid HUS stored catalog: %s", type(exc).__name__)
            raise StorageDataError("HUS catalog data is invalid") from None

    @staticmethod
    def _validated(row: Any, identity: Any) -> Catalog:
        payload = row["payload"]
        if not isinstance(payload, dict):
            raise StorageDataError("HUS revision payload is invalid")
        catalog = Catalog.model_validate(payload)
        program_id = catalog.program.program_id
        if program_id != row["program_id"] or program_id != identity["program_id"]:
            raise StorageDataError("HUS revision program identity mismatch")
        if row["curriculum_id"] != identity["curriculum_id"]:
            raise StorageDataError("HUS revision curriculum identity mismatch")
        if row["revision_id"] != catalog_revision(catalog, row["source_digest"]):
            raise StorageDataError("HUS revision content hash mismatch")
        if catalog.metadata_schema_version != "1.0" or catalog.vocabulary_version != "1.0":
            raise StorageDataError("Unsupported HUS metadata schema")
        validate_catalog(catalog)
        return catalog

    def _load_catalog(self, conn: Connection, program_id: str) -> Catalog:
        row = conn.execute(text("""
            SELECT r.revision_id, r.program_id, r.curriculum_id, r.source_digest, r.payload,
                   c.curriculum_id AS source_curriculum_id, c.program_id AS source_program_id,
                   c.major_code, c.runtime_rules
            FROM hus_catalog_revisions r JOIN curricula c ON c.curriculum_id=r.curriculum_id
            WHERE r.program_id=:program_id AND r.active
        """), {"program_id": resolve_program_id(program_id)}).mappings().one_or_none()
        if row is None:
            raise CatalogError(f"Unknown HUS program: {program_id}")
        identity = {"program_id": row["source_program_id"], "curriculum_id": row["source_curriculum_id"]}
        catalog = self._validated(row, identity)
        if PROGRAM_MAJOR_IDS.get(catalog.program.program_id) != row["major_code"]:
            raise StorageDataError("HUS major identity mismatch")
        return catalog

    def load_catalog(self, program_id: str) -> Catalog:
        with self.connection() as conn:
            return self._load_catalog(conn, program_id)

    def list_catalogs(self) -> list[Catalog]:
        with self.connection() as conn:
            ids = conn.execute(text("SELECT program_id FROM hus_catalog_revisions WHERE active ORDER BY program_id")).scalars().all()
            return [self._load_catalog(conn, program_id) for program_id in ids]

    def read_profiles(self) -> list[dict[str, Any]]:
        # The HUS source has accounts/students, but this demo never reads real
        # profiles or persists personal transcript data.
        return []

    def ready(self) -> None:
        with self.connection() as conn:
            head = conn.execute(text("SELECT version_num FROM hus_alembic_version")).scalar_one_or_none()
            if head != HEAD:
                raise StorageDataError("HUS database migrations are not current")
            ids = conn.execute(text("SELECT program_id FROM hus_catalog_revisions WHERE active ORDER BY program_id")).scalars().all()
            if set(ids) != EXPECTED_PROGRAM_IDS or len(ids) != 4:
                raise StorageDataError("HUS database requires four active catalogs")
            for program_id in ids:
                self._load_catalog(conn, program_id)
