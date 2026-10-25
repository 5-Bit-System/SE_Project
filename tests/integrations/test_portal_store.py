"""Real transaction checks in a disposable database only."""

import copy
from datetime import datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.integrations.daotao import store
from app.integrations.daotao.snapshot import PortalFailure, snapshot
from tests.database.test_hus_migration_runtime import runtime_engine  # noqa: F401

pytestmark = pytest.mark.hus_postgres


@pytest.fixture
def portal_db(runtime_engine, monkeypatch):  # noqa: F811
    monkeypatch.setattr(store, "engine", lambda: runtime_engine)
    return runtime_engine


def source():
    return snapshot([["1", "TEST001", "Synthetic only", "3", "8", "B", "3"]])


def test_owner_atomic_delete_idempotency_and_late_response(portal_db):
    a, gen = store.owner("synthetic-a")
    b, _ = store.owner("synthetic-b")
    payload = source()
    assert store.save(a, gen, payload) == "saved"
    assert store.save(a, gen, payload) == "unchanged"
    assert store.profile(b)["snapshot"] is None
    changed = copy.deepcopy(payload)
    changed["digest"] = "changed"
    with pytest.raises(PortalFailure, match="incomplete_snapshot"):
        store.save(a, gen, changed)
    assert store.profile(a)["snapshot"] == payload
    store.clear(a)
    with pytest.raises(PortalFailure, match="cancelled"):
        store.save(a, gen, payload)
    with pytest.raises(PortalFailure, match="session_expired"):
        store.profile(a)


def test_cross_owner_fk_and_attempt_rollback(portal_db):
    a, gen = store.owner("synthetic-c")
    b, _ = store.owner("synthetic-d")
    store.save(a, gen, source())
    with portal_db.connect() as conn:
        snapshot_id = conn.execute(text(
            "SELECT current_snapshot_id FROM portal_users WHERE id=:id"), {"id": a}).scalar()
    with pytest.raises(IntegrityError), portal_db.begin() as conn:
        conn.execute(text("UPDATE portal_users SET current_snapshot_id=:s WHERE id=:b"),
                     {"s": snapshot_id, "b": b})
    payload = source()
    payload["attempts"] *= 2
    with pytest.raises(IntegrityError):
        store.save(b, gen, payload)
    assert store.profile(b)["snapshot"] is None


def test_concurrent_identical_sync_is_idempotent(portal_db):
    from concurrent.futures import ThreadPoolExecutor

    a, gen = store.owner("synthetic-concurrent")
    with ThreadPoolExecutor(2) as executor:
        results = list(executor.map(lambda _: store.save(a, gen, source()), range(2)))
    assert sorted(results) == ["saved", "unchanged"]


def test_source_profile_updates_on_identical_snapshot_without_changing_transcript(portal_db):
    owner, generation = store.owner("synthetic-profile")
    other, _ = store.owner("synthetic-profile-other")
    payload = source()
    store.save(owner, generation, payload)
    details = {"name": "Sinh viên giả lập", "program": "Ngành nguồn thử",
               "cohort": None, "policy_reviewed": True}
    assert store.save(owner, generation, payload, details) == "unchanged"
    saved = store.profile(owner)
    assert saved["profile"] == {key: details[key] for key in ("name", "program", "cohort")}
    assert saved["snapshot"] == payload
    assert store.profile(other)["profile"] == {}
    changed = copy.deepcopy(payload)
    changed["digest"] = "changed-profile"
    with pytest.raises(PortalFailure, match="incomplete_snapshot"):
        store.save(owner, generation, changed, {"name": "Must rollback"})
    assert store.profile(owner)["profile"] == saved["profile"]


def test_successful_sync_time_refreshes_without_mutating_snapshot_and_rolls_back_on_rejection(portal_db):
    owner, generation = store.owner("synthetic-reminder")
    other, _ = store.owner("synthetic-reminder-other")
    payload = source()
    store.save(owner, generation, payload)
    with portal_db.begin() as conn:
        conn.execute(text("""
            UPDATE portal_users SET profile=jsonb_set(
                profile, '{_last_synced_at}', to_jsonb(CURRENT_TIMESTAMP - interval '8 days'))
            WHERE id=:owner
        """), {"owner": owner})
        before = conn.execute(text("""
            SELECT s.id, s.fetched_at, s.payload FROM portal_users u
            JOIN portal_transcript_snapshots s ON s.id=u.current_snapshot_id WHERE u.id=:owner
        """), {"owner": owner}).mappings().one()
    previous = store.profile(owner)
    assert store.save(owner, generation, payload, {"name": "Synthetic reminder"}) == "unchanged"
    refreshed = store.profile(owner)
    assert datetime.fromisoformat(refreshed["last_synced_at"]) > datetime.fromisoformat(previous["last_synced_at"])
    assert refreshed["fetched_at"] == previous["fetched_at"]
    assert refreshed["profile"] == {"name": "Synthetic reminder", "program": None, "cohort": None}
    assert store.profile(other)["last_synced_at"] is None
    with portal_db.connect() as conn:
        after = conn.execute(text("""
            SELECT s.id, s.fetched_at, s.payload FROM portal_users u
            JOIN portal_transcript_snapshots s ON s.id=u.current_snapshot_id WHERE u.id=:owner
        """), {"owner": owner}).mappings().one()
    assert dict(before) == dict(after)
    changed = copy.deepcopy(payload)
    changed["digest"] = "synthetic-reminder-changed"
    with pytest.raises(PortalFailure, match="incomplete_snapshot"):
        store.save(owner, generation, changed, {"name": "Must rollback"})
    assert store.profile(owner) == refreshed
