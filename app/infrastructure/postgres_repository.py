"""Runtime adapter for versioned catalog and synthetic profile data."""

import logging
from contextlib import contextmanager
from typing import Any, Iterator

from pydantic import ValidationError
from sqlalchemy import Connection, Engine, select, text
from sqlalchemy.exc import SQLAlchemyError

from app.catalog_validation import validate_curriculum_selections
from app.db import schema as db
from app.db.session import get_engine
from app.errors import CatalogError, StorageDataError, StorageUnavailable
from app.models import Catalog, Course, Program
from app.transcript import resolve_program_id

logger = logging.getLogger(__name__)


class PostgresRepository:
    def __init__(self, engine: Engine | None = None) -> None:
        self.engine = engine if engine is not None else get_engine()

    @contextmanager
    def connection(self) -> Iterator[Connection]:
        try:
            with self.engine.connect().execution_options(isolation_level="REPEATABLE READ") as conn:
                yield conn
        except SQLAlchemyError as exc:
            logger.error("PostgreSQL operation failed: %s", type(exc).__name__)
            raise StorageUnavailable(
                "PostgreSQL chưa sẵn sàng; kiểm tra kết nối và migration"
            ) from None
        except ValidationError:
            raise StorageDataError("Dữ liệu PostgreSQL không khớp schema ứng dụng") from None

    def ready(self) -> None:
        with self.connection() as conn:
            conn.execute(text("SELECT 1"))
            count = len(
                conn.execute(
                    select(db.catalog_revisions.c.program_id).where(
                        db.catalog_revisions.c.active.is_(True)
                    )
                ).all()
            )
            if count != 4:
                raise StorageDataError("PostgreSQL chưa được seed đủ bốn catalog")

    def _load_catalog(self, conn: Connection, program_id: str) -> Catalog:
        revision = (
            conn.execute(
                select(db.catalog_revisions).where(
                    db.catalog_revisions.c.program_id == resolve_program_id(program_id),
                    db.catalog_revisions.c.active.is_(True),
                )
            )
            .mappings()
            .one_or_none()
        )
        if revision is None:
            raise CatalogError(f"Không tìm thấy chương trình: {program_id}")
        revision_id = revision["revision_id"]
        rows = (
            conn.execute(
                select(db.courses)
                .where(db.courses.c.revision_id == revision_id)
                .order_by(db.courses.c.position)
            )
            .mappings()
            .all()
        )
        prerequisites: dict[str, list[list[str]]] = {}
        groups = conn.execute(
            select(db.prerequisite_groups)
            .where(db.prerequisite_groups.c.revision_id == revision_id)
            .order_by(db.prerequisite_groups.c.course_code, db.prerequisite_groups.c.group_no)
        ).mappings()
        for group in groups:
            prerequisites.setdefault(group["course_code"], []).append([])
        options = conn.execute(
            select(db.prerequisite_options)
            .where(db.prerequisite_options.c.revision_id == revision_id)
            .order_by(
                db.prerequisite_options.c.course_code,
                db.prerequisite_options.c.group_no,
                db.prerequisite_options.c.option_no,
            )
        ).mappings()
        for option in options:
            prerequisites[option["course_code"]][option["group_no"]].append(
                option["required_code"] or option["external_code"]
            )
        memberships: dict[str, list[str]] = {}
        links = conn.execute(
            select(db.choice_group_courses)
            .where(db.choice_group_courses.c.revision_id == revision_id)
            .order_by(db.choice_group_courses.c.course_code, db.choice_group_courses.c.position)
        ).mappings()
        for link in links:
            memberships.setdefault(link["course_code"], []).append(link["group_id"])
        catalog = Catalog(
            program=Program.model_validate(revision["payload"]),
            courses=[
                Course.model_validate(
                    {
                        **row["payload"],
                        "code": row["code"],
                        "name": row["name"],
                        "credits": row["credits"],
                        "block": row["block"],
                        "prerequisites": prerequisites.get(row["code"], []),
                        "choice_group_ids": memberships.get(row["code"], []),
                    }
                )
                for row in rows
            ],
        )
        if catalog.program.program_id != revision["program_id"]:
            raise StorageDataError("Ngành trong catalog không khớp revision PostgreSQL")
        validate_curriculum_selections(catalog.program, {course.code for course in catalog.courses})
        return catalog

    def load_catalog(self, program_id: str) -> Catalog:
        with self.connection() as conn:
            return self._load_catalog(conn, program_id)

    def list_catalogs(self) -> list[Catalog]:
        with self.connection() as conn:
            ids = (
                conn.execute(
                    select(db.catalog_revisions.c.program_id)
                    .where(db.catalog_revisions.c.active.is_(True))
                    .order_by(db.catalog_revisions.c.program_id)
                )
                .scalars()
                .all()
            )
            return [self._load_catalog(conn, program_id) for program_id in ids]

    def read_profiles(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = (
                conn.execute(
                    select(db.demo_profiles, db.catalog_revisions.c.program_id)
                    .join(
                        db.catalog_revisions,
                        db.demo_profiles.c.revision_id == db.catalog_revisions.c.revision_id,
                    )
                    .where(db.catalog_revisions.c.active.is_(True))
                    .order_by(db.demo_profiles.c.profile_id)
                )
                .mappings()
                .all()
            )
            result = []
            for row in rows:
                records = conn.execute(
                    select(db.transcript_records)
                    .where(
                        db.transcript_records.c.revision_id == row["revision_id"],
                        db.transcript_records.c.profile_id == row["profile_id"],
                    )
                    .order_by(db.transcript_records.c.position)
                ).mappings()
                result.append(
                    {
                        **row["payload"],
                        "profile_id": row["profile_id"],
                        "program_id": row["program_id"],
                        "records": [
                            {
                                **record["payload"],
                                "course_code": record["course_code"],
                                "grade": record["grade"],
                                "passed": record["passed"],
                                "term": record["term"],
                            }
                            for record in records
                        ],
                    }
                )
            return result
