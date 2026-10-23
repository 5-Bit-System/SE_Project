"""Opt-in HUS runtime acceptance in a disposable database, never product tables."""

import copy
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.sql.dml import Update

from alembic import command
from app.catalog_contracts import digest
from app.config import get_settings
from app.errors import StorageDataError
from app.infrastructure.hus_repository import HusRepository
from app.main import app
from database.hus_db.catalog_builder import build_catalogs
from database.tools import publish_catalogs as publisher
from database.tools.apply_sql import apply_sql
from database.tools.migrate import config
from database.tools.publish_catalogs import (
    NATURAL_KEYS,
    SOURCE,
    activate_revision,
    publish_catalogs,
)
from tests.support.postgres_targets import validate_hus_test_target

_validate_runtime_test_target = validate_hus_test_target


@pytest.fixture
def runtime_engine():
    url = os.getenv("HUS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("HUS_TEST_DATABASE_URL is not configured")
    target = _validate_runtime_test_target(url)
    name = "ai07_runtime_test_" + uuid.uuid4().hex[:12]
    admin = create_engine(target, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    engine = create_engine(target.set(database=name), hide_parameters=True)
    try:
        with engine.begin() as conn:
            cfg = config()
            cfg.attributes["connection"] = conn
            command.upgrade(cfg, "head")
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()


PUBLISHER_TABLES = (*NATURAL_KEYS, "hus_catalog_revisions")


def publisher_snapshot(engine) -> dict[str, list[str]]:
    """Return a deterministic view of every relation the publisher can mutate."""
    snapshot = {}
    with engine.connect() as conn:
        for name in PUBLISHER_TABLES:
            rows = conn.execute(text(
                f"SELECT to_jsonb(row_data) FROM public.{name} AS row_data "
                "ORDER BY to_jsonb(row_data)::text"
            )).scalars().all()
            snapshot[name] = [json.dumps(row, sort_keys=True, default=str) for row in rows]
    return snapshot


@pytest.mark.parametrize("query", ["", "?sslmode=disable"])
def test_runtime_target_accepts_local_ai07(query):
    target = _validate_runtime_test_target(
        "postgresql+psycopg2://user:secret@127.0.0.1:5433/ai07" + query
    )
    assert target.host == "127.0.0.1"
    assert target.database == "ai07"


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg2://user:secret@example.invalid:5433/ai07",
        "postgresql+psycopg2://user:secret@127.0.0.1:5433/production",
        "postgresql+psycopg2://user:secret@localhost:5433/ai07?host=example.invalid",
        "postgresql+psycopg2://user:secret@localhost:5433/ai07?hostaddr=203.0.113.1",
        "postgresql+psycopg2://user:secret@localhost:5433/ai07?dbname=production",
        "postgresql+psycopg2://user:secret@localhost:5433/ai07?service=remote",
        "mysql+pymysql://user:secret@localhost:5433/ai07",
    ],
)
def test_runtime_engine_rejects_unsafe_target_before_connection(monkeypatch, url):
    monkeypatch.setenv("HUS_TEST_DATABASE_URL", url)

    def reject_engine_creation(*args, **kwargs):
        raise AssertionError("create_engine was reached before URL validation")

    monkeypatch.setitem(runtime_engine.__wrapped__.__globals__, "create_engine", reject_engine_creation)
    with pytest.raises(ValueError, match="local ai07"):
        next(runtime_engine.__wrapped__())


@pytest.mark.hus_postgres
def test_fresh_migration_publication_and_rollback(runtime_engine):
    engine = runtime_engine
    bundle = json.loads(SOURCE.read_text(encoding="utf-8"))
    first = publish_catalogs(engine, bundle)
    repo = HusRepository(engine)
    repo.ready()
    with engine.begin() as conn:
        legacy_config = Config("alembic.ini")
        legacy_config.attributes["connection"] = conn
        with pytest.raises(RuntimeError, match="Refusing legacy migrations"):
            command.upgrade(legacy_config, "head")
    assert repo.read_profiles() == []
    assert sorted(len(c.courses) for c in repo.list_catalogs()) == [65, 67, 68, 90]
    assert publish_catalogs(engine, bundle) == first
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM hus_catalog_revisions")).scalar_one() == 4
        for table in ("accounts", "students", "course_attempts"):
            assert conn.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0
    broken = copy.deepcopy(bundle)
    broken["tables"]["majors"].append(broken["tables"]["majors"][0])
    with pytest.raises(ValueError):
        publish_catalogs(engine, broken)
    repo.ready()
    # A valid newer source revision retains old snapshots and supports rollback.
    newer = copy.deepcopy(bundle)
    newer["source"] += " (repeatability acceptance)"
    second = publish_catalogs(engine, newer)
    assert all(first[p] != second[p] for p in first)
    for program, revision in first.items():
        activate_revision(engine, program, revision)
    repo.ready()
    with engine.connect() as conn:
        active = dict(conn.execute(text("SELECT program_id, revision_id FROM hus_catalog_revisions WHERE active")).all())
        assert active == first
        assert conn.execute(text("SELECT count(*) FROM hus_catalog_revisions")).scalar_one() == 8
    with pytest.raises(RuntimeError, match="managed by migrations"):
        apply_sql(engine, "SELECT 1")
    # Tampered persisted content fails closed; no JSON fallback.
    with engine.begin() as conn:
        conn.execute(text("UPDATE hus_catalog_revisions SET source_digest=:bad WHERE active"), {"bad": "0" * 64})
    with pytest.raises(StorageDataError, match="hash"):
        repo.ready()


@pytest.mark.hus_postgres
def test_publisher_rolls_back_mid_import_and_releases_lock(runtime_engine, monkeypatch):
    bundle = json.loads(SOURCE.read_text(encoding="utf-8"))
    first = publish_catalogs(runtime_engine, bundle)
    before = publisher_snapshot(runtime_engine)
    newer = copy.deepcopy(bundle)
    newer["source"] += " (rollback injection)"
    original_upsert = publisher._upsert

    def fail_at_curriculum_courses(conn, table, row, keys):
        if table.name == "curriculum_courses":
            raise RuntimeError("injected publisher failure")
        original_upsert(conn, table, row, keys)

    monkeypatch.setattr(publisher, "_upsert", fail_at_curriculum_courses)
    with pytest.raises(RuntimeError, match="injected publisher failure"):
        publish_catalogs(runtime_engine, newer)
    assert publisher_snapshot(runtime_engine) == before

    monkeypatch.setattr(publisher, "_upsert", original_upsert)
    second = publish_catalogs(runtime_engine, newer)
    assert all(first[program] != second[program] for program in first)
    HusRepository(runtime_engine).ready()


@pytest.mark.hus_postgres
def test_publisher_rolls_back_after_deactivating_revisions(runtime_engine):
    bundle = json.loads(SOURCE.read_text(encoding="utf-8"))
    first = publish_catalogs(runtime_engine, bundle)
    before = publisher_snapshot(runtime_engine)
    newer = copy.deepcopy(bundle)
    newer["source"] += " (activation rollback injection)"
    revision_updates = 0

    def fail_before_reactivation(conn, clauseelement, multiparams, params, execution_options):
        nonlocal revision_updates
        if isinstance(clauseelement, Update) and clauseelement.table.name == "hus_catalog_revisions":
            revision_updates += 1
            if revision_updates == 2:
                raise RuntimeError("injected activation failure")

    event.listen(runtime_engine, "before_execute", fail_before_reactivation)
    try:
        with pytest.raises(RuntimeError, match="injected activation failure"):
            publish_catalogs(runtime_engine, newer)
    finally:
        event.remove(runtime_engine, "before_execute", fail_before_reactivation)

    assert revision_updates == 2
    assert publisher_snapshot(runtime_engine) == before
    with runtime_engine.connect() as conn:
        active = dict(conn.execute(text(
            "SELECT program_id, revision_id FROM hus_catalog_revisions WHERE active"
        )).all())
        assert active == first
    HusRepository(runtime_engine).ready()

    second = publish_catalogs(runtime_engine, newer)
    assert all(first[program] != second[program] for program in first)
    with runtime_engine.connect() as conn:
        active = dict(conn.execute(text(
            "SELECT program_id, revision_id FROM hus_catalog_revisions WHERE active"
        )).all())
        assert active == second
    HusRepository(runtime_engine).ready()


@pytest.mark.hus_postgres
def test_concurrent_publications_keep_one_active_revision_per_program(runtime_engine):
    bundle = json.loads(SOURCE.read_text(encoding="utf-8"))
    first = publish_catalogs(runtime_engine, bundle)
    newer = copy.deepcopy(bundle)
    newer["source"] += " (concurrent acceptance)"
    barrier = Barrier(2)

    def publish_after_barrier() -> dict[str, str]:
        barrier.wait(timeout=5)
        return publish_catalogs(runtime_engine, newer)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = [pool.submit(publish_after_barrier) for _ in range(2)]
        left, right = (result.result(timeout=15) for result in results)

    assert left == right
    assert all(first[program] != left[program] for program in first)
    with runtime_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM hus_catalog_revisions")).scalar_one() == 8
        active_counts = dict(conn.execute(text(
            "SELECT program_id, count(*) FROM hus_catalog_revisions "
            "WHERE active GROUP BY program_id"
        )).all())
    assert active_counts == {program: 1 for program in left}
    HusRepository(runtime_engine).ready()


@pytest.mark.hus_postgres
def test_concurrent_distinct_bundles_activate_one_complete_snapshot(runtime_engine):
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    baseline = publish_catalogs(runtime_engine, source)
    sample = next(row for row in source["course_metadata"]
                  if row["values"].get("name_en") and row["values"].get("hours") is not None)
    candidates = {}
    for label in ("A", "B"):
        bundle = copy.deepcopy(source)
        bundle["source"] += f" (synthetic concurrent bundle {label})"
        row = next(row for row in bundle["course_metadata"]
                   if (row["program_id"], row["code"]) == (sample["program_id"], sample["code"]))
        row["values"]["name_en"] = f"Synthetic concurrent name {label}"
        for evidence in row["field_evidence"]["name_en"]:
            evidence["note"] = f"Synthetic concurrency test value {label}; not reviewed source data."
        candidates[label] = bundle

    barrier = Barrier(2)

    def publish_after_barrier(label: str) -> dict[str, str]:
        barrier.wait(timeout=10)
        return publish_catalogs(runtime_engine, candidates[label])

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {label: pool.submit(publish_after_barrier, label) for label in candidates}
        results = {label: future.result(timeout=60) for label, future in futures.items()}

    assert all(results[label] != baseline for label in candidates)
    assert results["A"] != results["B"]
    with runtime_engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT program_id, revision_id, source_digest "
            "FROM hus_catalog_revisions WHERE active"
        )).all()
        assert len(rows) == 4
        active = {row.program_id: row.revision_id for row in rows}
        assert active in results.values()
        winner = next(label for label, revisions in results.items() if revisions == active)
        assert {row.source_digest for row in rows} == {digest(candidates[winner])}
        assert conn.execute(text("SELECT count(*) FROM hus_catalog_revisions")).scalar_one() == 12
        stored_name = conn.execute(text(
            "SELECT m.runtime_metadata->>'name_en' "
            "FROM curriculum_courses m JOIN curricula c USING (curriculum_id) "
            "WHERE c.program_id=:program AND m.course_code=:code"
        ), {"program": sample["program_id"], "code": sample["code"]}).scalar_one()
        assert stored_name == f"Synthetic concurrent name {winner}"
    HusRepository(runtime_engine).ready()


@pytest.mark.hus_postgres
def test_metadata_round_trips_through_postgres_repository_and_http(runtime_engine, monkeypatch):
    bundle = json.loads(SOURCE.read_text(encoding="utf-8"))
    publish_catalogs(runtime_engine, bundle)
    repository = HusRepository(runtime_engine)
    expected = {catalog.program.program_id: catalog for catalog in build_catalogs(bundle)}
    stored = {catalog.program.program_id: catalog for catalog in repository.list_catalogs()}
    assert set(stored) == set(expected)
    for program_id, catalog in expected.items():
        stored_courses = {course.code: course for course in stored[program_id].courses}
        for course in catalog.courses:
            actual = stored_courses[course.code]
            assert actual.name_en == course.name_en
            assert actual.hours == course.hours
            assert actual.field_evidence == course.field_evidence
            assert (actual.credits, actual.prerequisites, actual.prerequisite_status) == (
                course.credits, course.prerequisites, course.prerequisite_status
            )
    assert sum(course.hours is None for catalog in stored.values()
               for course in catalog.courses) == 8

    program_id = "toan_tin_7460117_2022"
    course = next(course for course in stored[program_id].courses if course.code == "MAT3366")
    with runtime_engine.connect() as conn:
        row = conn.execute(text(
            "SELECT m.runtime_metadata FROM curriculum_courses m "
            "JOIN curricula c USING (curriculum_id) "
            "WHERE c.program_id=:program AND m.course_code=:code"
        ), {"program": program_id, "code": course.code}).scalar_one()
    assert row["name_en"] == course.name_en
    assert row["hours"] == course.hours
    assert row["field_evidence"] == course.model_dump(mode="json")["field_evidence"]

    monkeypatch.setenv("STORAGE_BACKEND", "postgres")
    monkeypatch.setenv("DATABASE_MODEL", "hus")
    monkeypatch.setenv("DATABASE_URL", runtime_engine.url.render_as_string(hide_password=False))
    get_settings.cache_clear()
    monkeypatch.setattr("app.infrastructure.repositories.postgres_repository", lambda: repository)
    with TestClient(app) as client:
        assert client.get("/ready").status_code == 200
        response = client.get("/courses", params={"program_id": program_id})
    assert response.status_code == 200
    api_course = next(row for row in response.json() if row["code"] == course.code)
    assert api_course["name"] == course.name
    assert api_course["name_en"] == course.name_en
    assert api_course["hours"] == course.hours
    assert api_course["field_evidence"] == course.model_dump(mode="json")["field_evidence"]


@pytest.mark.hus_postgres
def test_metadata_change_creates_revision_without_changing_academic_rules(runtime_engine):
    bundle = json.loads(SOURCE.read_text(encoding="utf-8"))
    first = publish_catalogs(runtime_engine, bundle)
    changed = copy.deepcopy(bundle)
    row = next(row for row in changed["course_metadata"]
               if row["values"].get("name_en") and row["values"].get("hours") is not None)
    row["values"]["name_en"] = "Synthetic metadata revision test"
    for evidence in row["field_evidence"]["name_en"]:
        evidence["note"] = "Synthetic revision test value; not reviewed source data."
    second = publish_catalogs(runtime_engine, changed)
    assert all(first[program] != second[program] for program in first)
    assert publish_catalogs(runtime_engine, changed) == second

    repository = HusRepository(runtime_engine)
    actual = {catalog.program.program_id: catalog for catalog in repository.list_catalogs()}
    original = {catalog.program.program_id: catalog for catalog in build_catalogs(bundle)}
    for program_id, catalog in actual.items():
        originals = {course.code: course for course in original[program_id].courses}
        for course in catalog.courses:
            before = originals[course.code]
            assert (course.credits, course.prerequisites, course.prerequisite_status,
                    course.prerequisite_variants) == (
                        before.credits, before.prerequisites, before.prerequisite_status,
                        before.prerequisite_variants
                    )
    changed_course = next(course for course in actual[row["program_id"]].courses
                          if course.code == row["code"])
    assert changed_course.name_en == "Synthetic metadata revision test"
    with runtime_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM hus_catalog_revisions")).scalar_one() == 8
        active = dict(conn.execute(text(
            "SELECT program_id, revision_id FROM hus_catalog_revisions WHERE active"
        )).all())
        assert active == second
    repository.ready()
