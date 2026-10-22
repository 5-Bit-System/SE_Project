"""Opt-in HUS runtime acceptance in a disposable database, never product tables."""

import copy
import json
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, event, text
from sqlalchemy.sql.dml import Update

from alembic import command
from app.errors import StorageDataError
from app.infrastructure.hus_repository import HusRepository
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
