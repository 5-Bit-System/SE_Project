"""Opt-in HUS runtime acceptance in a disposable database, never product tables."""

import copy
import json
import os
import uuid

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.errors import StorageDataError
from app.infrastructure.hus_repository import HusRepository
from database.tools.apply_sql import apply_sql
from database.tools.migrate import config
from database.tools.publish_catalogs import SOURCE, activate_revision, publish_catalogs

pytestmark = pytest.mark.hus_postgres


@pytest.fixture(scope="module")
def runtime_engine():
    url = os.getenv("HUS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("HUS_TEST_DATABASE_URL is not configured")
    target = make_url(url)
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
