"""Opt-in HUS runtime acceptance in a disposable database, never product tables."""

import copy
import json
import os
import uuid

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

import database.tools.publish_catalogs as publisher
from alembic import command
from app.errors import StorageDataError
from app.infrastructure.hus_repository import HusRepository
from database.tools.apply_sql import apply_sql
from database.tools.migrate import config
from database.tools.publish_catalogs import SOURCE, activate_revision, publish_catalogs


def _validate_runtime_test_target(url: str) -> URL:
    target = make_url(url)
    if (
        target.get_backend_name() != "postgresql"
        or target.host not in {"127.0.0.1", "localhost"}
        or target.database != "ai07"
        or set(target.query) - {"sslmode"}
    ):
        raise ValueError("HUS migration tests require local ai07")
    return target


@pytest.fixture(scope="module")
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
def test_fresh_migration_publication_and_rollback(runtime_engine, monkeypatch):
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

    # Fail after actual upserts, once the publication transaction has changed
    # existing source facts, and verify the database is byte-for-byte equivalent
    # at the row level after PostgreSQL rolls the transaction back.
    tables = (
        "faculties", "majors", "curricula", "courses", "curriculum_courses",
        "course_prerequisites", "official_curriculum_groups",
        "official_curriculum_entries", "hus_catalog_revisions",
    )

    def snapshot():
        with engine.connect() as conn:
            return {
                name: sorted(
                    (dict(row) for row in conn.execute(text(f"SELECT * FROM public.{name}")).mappings()),
                    key=lambda row: json.dumps(row, sort_keys=True, default=str),
                )
                for name in tables
            }

    before_failed_publish = snapshot()
    changed = copy.deepcopy(bundle)
    changed["tables"]["faculties"][0]["faculty_name"] += " (injected failure)"
    original_upsert = publisher._upsert
    successful_upserts = 0

    def fail_after_upserts(conn, table, row, keys):
        nonlocal successful_upserts
        original_upsert(conn, table, row, keys)
        successful_upserts += 1
        if successful_upserts == 2:
            raise RuntimeError("Injected failure after source upserts")

    with monkeypatch.context() as patch:
        patch.setattr(publisher, "_upsert", fail_after_upserts)
        with pytest.raises(RuntimeError, match="Injected failure"):
            publish_catalogs(engine, changed)
    assert successful_upserts == 2
    assert snapshot() == before_failed_publish
    repo.ready()

    # The failed transaction must release the advisory lock and leave the
    # publisher usable for a subsequent valid publication.
    assert publish_catalogs(engine, bundle) == first
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
