"""Validate and atomically import source artifacts into PostgreSQL.

Run from the repository root: python -m tools.seed_database
Content-addressed revisions include catalog, source rows and synthetic profiles.
Unchanged seeds retain their rows; changed source creates a new revision.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, Engine, Table, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from app.db import schema as db
from app.db.session import get_engine
from app.infrastructure.json_catalog_repository import DATA_ROOT, load_catalog
from app.profiles import PROFILES_PATH, DemoProfile, validate_profile
from app.transcript import PROGRAM_ALIASES
from tools.build_catalogs import check_curriculum


def _insert(conn: Connection, table: Table, rows: list[dict[str, Any]]) -> None:
    if rows:
        conn.execute(table.insert(), rows)


def _seed_revision(conn: Connection, revision_id: str, bundle: dict[str, Any]) -> None:
    program, courses, sources, profiles = (
        bundle[key] for key in ("program", "courses", "sources", "profiles")
    )
    rev = {"revision_id": revision_id}
    conn.execute(
        db.catalog_revisions.insert().values(
            **rev,
            program_id=program["program_id"],
            active=False,
            payload=program,
        )
    )
    _insert(
        conn,
        db.courses,
        [
            {
                **rev,
                "code": course["code"],
                "position": position,
                "name": course["name"],
                "credits": course["credits"],
                "block": course["block"],
                "payload": course,
            }
            for position, course in enumerate(courses)
        ],
    )
    _insert(
        conn,
        db.course_sources,
        [
            {
                **rev,
                "course_code": row["code"],
                "position": position,
                "source_page": row["source_page"],
                "payload": row,
            }
            for position, row in enumerate(sources)
        ],
    )
    _insert(
        conn,
        db.choice_groups,
        [
            {
                **rev,
                "group_id": group["id"],
                "required_credits": group["required_credits"],
                "selection_mode": group["selection_mode"],
                "payload": group,
            }
            for group in program["choice_groups"]
        ],
    )
    _insert(
        conn,
        db.choice_group_courses,
        [
            {
                **rev,
                "group_id": group_id,
                "course_code": course["code"],
                "position": position,
            }
            for course in courses
            for position, group_id in enumerate(course["choice_group_ids"])
        ],
    )
    _insert(
        conn,
        db.prerequisite_groups,
        [
            {
                **rev,
                "course_code": course["code"],
                "group_no": group_no,
                "source_status": course["prerequisite_status"],
            }
            for course in courses
            for group_no, _ in enumerate(course["prerequisites"])
        ],
    )
    known = {course["code"] for course in courses}
    _insert(
        conn,
        db.prerequisite_options,
        [
            {
                **rev,
                "course_code": course["code"],
                "group_no": group_no,
                "option_no": option_no,
                "required_code": code if code in known else None,
                "external_code": code if code not in known else None,
                "verification_status": "transcribed" if code in known else "unverified",
            }
            for course in courses
            for group_no, group in enumerate(course["prerequisites"])
            for option_no, code in enumerate(group)
        ],
    )
    tracks = program["track_selection"]["tracks"]
    _insert(
        conn, db.tracks, [{**rev, "track_id": track["id"], "payload": track} for track in tracks]
    )
    _insert(
        conn,
        db.track_choice_groups,
        [
            {
                **rev,
                "track_id": track["id"],
                "group_id": group_id,
            }
            for track in tracks
            for group_id in track["choice_group_ids"]
        ],
    )
    paths = program["graduation_selection"]["paths"]
    _insert(
        conn,
        db.graduation_paths,
        [{**rev, "path_id": path["id"], "payload": path} for path in paths],
    )
    _insert(
        conn,
        db.graduation_path_courses,
        [
            {
                **rev,
                "path_id": path["id"],
                "course_code": code,
            }
            for path in paths
            for code in path["course_codes"]
        ],
    )
    _insert(
        conn,
        db.graduation_path_tracks,
        [
            {
                **rev,
                "path_id": path["id"],
                "track_id": track_id,
            }
            for path in paths
            for track_id in path["allowed_track_ids"]
        ],
    )
    _insert(
        conn,
        db.demo_profiles,
        [
            {
                **rev,
                "profile_id": profile["profile_id"],
                "payload": {key: value for key, value in profile.items() if key != "records"},
            }
            for profile in profiles
        ],
    )
    _insert(
        conn,
        db.transcript_records,
        [
            {
                **rev,
                "profile_id": profile["profile_id"],
                "course_code": record["course_code"],
                "position": position,
                "grade": record["grade"],
                "passed": record["passed"],
                "term": record["term"],
                "payload": record,
            }
            for profile in profiles
            for position, record in enumerate(profile["records"])
        ],
    )


def seed_database(
    engine: Engine | None = None,
    source_root: Path = DATA_ROOT,
    profiles_path: Path = PROFILES_PATH,
) -> dict[str, int]:
    profiles = [
        DemoProfile.model_validate(item)
        for item in json.loads(profiles_path.read_text(encoding="utf-8"))
    ]
    if len(profiles) != 12 or len({profile.profile_id for profile in profiles}) != 12:
        raise ValueError("Seed requires 12 unique synthetic profiles")
    bundles = []
    for directory in sorted(source_root.iterdir()):
        if not directory.is_dir():
            continue
        catalog = load_catalog(directory.name, source_root)
        program = json.loads((directory / "curriculum.json").read_text(encoding="utf-8"))
        courses = json.loads((directory / "courses.json").read_text(encoding="utf-8"))
        sources = json.loads((directory / "source_rows.json").read_text(encoding="utf-8"))
        check_curriculum(program, sources, courses)
        selected = [profile for profile in profiles if profile.program_id == program["program_id"]]
        if len(selected) != 3:
            raise ValueError("Seed requires three profiles per program")
        for profile in selected:
            validate_profile(profile, catalog)
        bundles.append(
            {
                "program": program,
                "courses": courses,
                "sources": sources,
                "profiles": [profile.model_dump(mode="json") for profile in selected],
            }
        )
    if len(bundles) != 4 or {bundle["program"]["program_id"] for bundle in bundles} != set(
        PROGRAM_ALIASES.values()
    ):
        raise ValueError("Seed requires exactly four catalogs")
    engine = engine if engine is not None else get_engine()
    created = 0
    with engine.begin() as conn:
        # Serialize seed jobs; publishing all four catalogs is one transaction.
        conn.execute(text("SELECT pg_advisory_xact_lock(7460108)"))
        for bundle in bundles:
            program = bundle["program"]
            canonical = json.dumps(
                bundle, sort_keys=True, ensure_ascii=False, separators=(",", ":")
            )
            revision_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            conn.execute(
                insert(db.programs)
                .values(
                    program_id=program["program_id"],
                    name=program["name"],
                )
                .on_conflict_do_nothing(index_elements=[db.programs.c.program_id])
            )
            exists = conn.execute(
                select(db.catalog_revisions.c.revision_id).where(
                    db.catalog_revisions.c.revision_id == revision_id,
                )
            ).scalar_one_or_none()
            if exists is None:
                _seed_revision(conn, revision_id, bundle)
                created += 1
            conn.execute(
                db.catalog_revisions.update()
                .where(
                    db.catalog_revisions.c.program_id == program["program_id"],
                    db.catalog_revisions.c.active.is_(True),
                )
                .values(active=False)
            )
            conn.execute(
                db.catalog_revisions.update()
                .where(
                    db.catalog_revisions.c.revision_id == revision_id,
                )
                .values(active=True)
            )
    return {
        "programs": 4,
        "courses": sum(len(bundle["courses"]) for bundle in bundles),
        "profiles": len(profiles),
        "new_revisions": created,
    }


def main() -> None:
    try:
        print(json.dumps(seed_database(), ensure_ascii=False))
    except SQLAlchemyError:
        raise SystemExit(
            "Seed failed: check PostgreSQL connectivity and run alembic upgrade head"
        ) from None


if __name__ == "__main__":
    main()
