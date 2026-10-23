"""Transactionally import HUS source facts and activate four catalog snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from sqlalchemy import Engine, MetaData, Table, select, text
from sqlalchemy.dialects.postgresql import insert

from app.catalog_contracts import EXPECTED_PROGRAM_IDS, catalog_payload, catalog_revision, digest
from app.catalog_validation import validate_catalog
from app.models import Catalog
from database.hus_db.catalog_builder import build_catalogs
from database.hus_db.connection import connect

SOURCE = Path(__file__).resolve().parents[1] / "data" / "hus_source.json"
NATURAL_KEYS = {
    "faculties": ("faculty_code",),
    "majors": ("major_code",),
    "curricula": ("major_code", "curriculum_version", "cohort_year"),
    "courses": ("course_code",),
    "curriculum_courses": ("curriculum_id", "course_code"),
    "course_prerequisites": ("curriculum_id", "course_code", "group_no", "prerequisite_course_code"),
    "official_curriculum_groups": ("curriculum_id", "group_key"),
    "official_curriculum_entries": ("curriculum_id", "group_key", "course_code"),
}


def _upsert(conn, table: Table, row: dict, keys: tuple[str, ...]) -> None:
    statement = insert(table).values(**row)
    updates = {key: getattr(statement.excluded, key) for key in row if key not in keys}
    if updates:
        statement = statement.on_conflict_do_update(index_elements=list(keys), set_=updates)
    else:
        statement = statement.on_conflict_do_nothing(index_elements=list(keys))
    conn.execute(statement)


def _mapped_rows(rows: list[dict], ids: dict[int, int]) -> list[dict]:
    result = []
    for source in rows:
        row = dict(source)
        row["curriculum_id"] = ids[row["curriculum_id"]]
        result.append(row)
    return result


def _assert_no_removed_relationships(conn, tables: dict[str, Table], rows: dict[str, list[dict]],
                                     target_ids: set[int]) -> None:
    """Never silently erase or strand relations from a prior source import."""
    for name in ("curriculum_courses", "course_prerequisites", "official_curriculum_groups",
                 "official_curriculum_entries"):
        keys = NATURAL_KEYS[name]
        incoming = {tuple(row[key] for key in keys) for row in rows[name]}
        current = conn.execute(select(*(tables[name].c[key] for key in keys)).where(
            tables[name].c.curriculum_id.in_(target_ids))).all()
        removed = {tuple(row) for row in current} - incoming
        if removed:
            raise ValueError(f"{name} has {len(removed)} existing relationships absent from source; manual review required")


def publish_catalogs(engine: Engine, bundle: dict, catalogs: list[Catalog] | None = None) -> dict[str, str]:
    """Preflight everything, then import source facts and activate all four in one commit."""
    built = build_catalogs(bundle)
    if catalogs is not None and [catalog_payload(c) for c in catalogs] != [catalog_payload(c) for c in built]:
        raise ValueError("Supplied catalogs do not match validated source bundle")
    catalogs = built
    if {c.program.program_id for c in catalogs} != EXPECTED_PROGRAM_IDS or len(catalogs) != 4:
        raise ValueError("HUS publication requires exactly the four expected programs")
    for catalog in catalogs:
        validate_catalog(catalog)
    source_digest = digest(bundle)
    revisions = {c.program.program_id: catalog_revision(c, source_digest) for c in catalogs}
    source = bundle["tables"]
    with engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(hashtext('ai07_hus_catalog_publish'))"))
        head = conn.execute(text("SELECT version_num FROM hus_alembic_version")).scalar_one()
        if head not in {"hus_20261017_02", "hus_20261023_03", "hus_20261023_04"}:
            raise RuntimeError("HUS migrations are not at runtime head")
        metadata = MetaData()
        tables = {name: Table(name, metadata, autoload_with=conn) for name in (*NATURAL_KEYS, "hus_catalog_revisions")}
        for name in ("faculties", "majors", "courses"):
            for row in source[name]:
                _upsert(conn, tables[name], row, NATURAL_KEYS[name])
        ids = {}
        catalog_by_id = {c.program.program_id: c for c in catalogs}
        from database.hus_db.catalog_builder import PROGRAM_IDS
        for row in source["curricula"]:
            # The curated builder owns this stable natural-key mapping.
            program_id = PROGRAM_IDS[(row["major_code"], row["cohort_year"], row["curriculum_version"])]
            new = {k: v for k, v in row.items() if k != "curriculum_id"}
            new["program_id"] = program_id
            new["runtime_rules"] = catalog_by_id[program_id].program.model_dump(mode="json")
            _upsert(conn, tables["curricula"], new, NATURAL_KEYS["curricula"])
            db_id = conn.execute(select(tables["curricula"].c.curriculum_id).where(
                *(tables["curricula"].c[k] == row[k] for k in NATURAL_KEYS["curricula"]))).scalar_one()
            ids[row["curriculum_id"]] = db_id
        mapped = {name: _mapped_rows(source[name], ids) for name in
                  ("curriculum_courses", "course_prerequisites", "official_curriculum_groups",
                   "official_curriculum_entries")}
        _assert_no_removed_relationships(conn, tables, mapped, set(ids.values()))
        course_by_program = {c.program.program_id: {course.code: course for course in c.courses}
                             for c in catalogs}
        program_by_id = {db_id: next(PROGRAM_IDS[(r["major_code"], r["cohort_year"], r["curriculum_version"])]
                                    for r in source["curricula"] if r["curriculum_id"] == source_id)
                         for source_id, db_id in ids.items()}
        for row in mapped["curriculum_courses"]:
            course = course_by_program[program_by_id[row["curriculum_id"]]][row["course_code"]]
            row["applicable_credits"] = course.credits
            row["counted_in_total"] = course.counted_in_total
            row["runtime_metadata"] = course.model_dump(mode="json")
            row["prerequisite_state"] = course.prerequisite_status
            _upsert(conn, tables["curriculum_courses"], row, NATURAL_KEYS["curriculum_courses"])
        for name in ("course_prerequisites", "official_curriculum_groups", "official_curriculum_entries"):
            for row in mapped[name]:
                if name == "official_curriculum_entries":
                    row.pop("entry_id", None)
                _upsert(conn, tables[name], row, NATURAL_KEYS[name])
        revisions_table = tables["hus_catalog_revisions"]
        for source_row in source["curricula"]:
            program_id = PROGRAM_IDS[(source_row["major_code"], source_row["cohort_year"], source_row["curriculum_version"])]
            revision_id = revisions[program_id]
            db_id = ids[source_row["curriculum_id"]]
            existing = conn.execute(select(revisions_table).where(revisions_table.c.revision_id == revision_id)).mappings().one_or_none()
            payload = catalog_payload(catalog_by_id[program_id])
            if existing and (existing["program_id"] != program_id or existing["curriculum_id"] != db_id
                             or existing["payload"] != payload or existing["source_digest"] != source_digest):
                raise ValueError("Immutable HUS revision collides with different content or source")
            if not existing:
                conn.execute(insert(revisions_table).values(revision_id=revision_id, curriculum_id=db_id,
                            program_id=program_id, active=False, source_digest=source_digest, payload=payload))
        conn.execute(revisions_table.update().where(revisions_table.c.active.is_(True)).values(active=False))
        conn.execute(revisions_table.update().where(revisions_table.c.revision_id.in_(revisions.values())).values(active=True))
    return revisions


def activate_revision(engine: Engine, program_id: str, revision_id: str) -> None:
    """Rollback one program to a previously published immutable revision."""
    if program_id not in EXPECTED_PROGRAM_IDS:
        raise ValueError("Unknown HUS program")
    with engine.begin() as conn:
        conn.execute(text("SELECT pg_advisory_xact_lock(hashtext('ai07_hus_catalog_publish'))"))
        row = conn.execute(text("SELECT curriculum_id FROM hus_catalog_revisions WHERE revision_id=:r AND program_id=:p"),
                           {"r": revision_id, "p": program_id}).one_or_none()
        if row is None:
            raise ValueError("Revision does not belong to program")
        conn.execute(text("UPDATE hus_catalog_revisions SET active=false WHERE program_id=:p OR curriculum_id=:c"),
                     {"p": program_id, "c": row.curriculum_id})
        conn.execute(text("UPDATE hus_catalog_revisions SET active=true WHERE revision_id=:r"), {"r": revision_id})


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish HUS source catalogs")
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--dry-run", action="store_true", help="Validate all source catalogs without connecting or writing")
    parser.add_argument("--activate", nargs=2, metavar=("PROGRAM_ID", "REVISION_ID"))
    args = parser.parse_args()
    if args.dry_run:
        if args.activate:
            parser.error("--dry-run cannot be combined with --activate")
        bundle = json.loads(args.source.read_text(encoding="utf-8"))
        catalogs = build_catalogs(bundle)
        print(json.dumps({c.program.program_id: len(c.courses) for c in catalogs}, sort_keys=True))
        return
    engine = connect()
    try:
        if args.activate:
            activate_revision(engine, *args.activate)
        else:
            bundle = json.loads(args.source.read_text(encoding="utf-8"))
            print(json.dumps(publish_catalogs(engine, bundle), sort_keys=True))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
