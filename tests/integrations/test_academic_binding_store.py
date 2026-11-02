"""Binding metadata uses existing storage and current account transactions."""

import copy
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import text

from app.academic_policies import POLICY_VERSION
from app.integrations.daotao import runtime, store
from app.integrations.daotao.snapshot import PortalFailure, snapshot
from app.program_bindings import source_scope
from tests.database.test_hus_migration_runtime import runtime_engine  # noqa: F401
from tests.integrations.test_portal_store import portal_db  # noqa: F401
from tests.integrations.test_system_auth import system  # noqa: F401

pytestmark = pytest.mark.hus_postgres
DETAILS = {"name": "Invented student", "program": "Khoa học máy tính và thông tin", "cohort": "68"}


def binding(details=DETAILS):
    return {"binding_schema_version": 1, "program_id": "khmtt_7480113qtd_2022",
            "cohort": 68, "catalog_revision": "a" * 64, "verified": True,
            "policy_version": POLICY_VERSION, "source_scope": source_scope(details),
            "confirmation_method": "owner_confirmed_source_enrollment",
            "confirmed_at": "2026-10-26T00:00:00+00:00", "evidence_ref": "synthetic-owner-confirmation"}


def seed():
    owner, generation = store.owner("invented-binding-owner")
    payload = snapshot([["1", "TEST001", "Invented course", "3", "7.5", "B", "3"]])
    store.save(owner, generation, payload, DETAILS)
    return owner, generation, payload


def test_binding_preserves_source_and_sync_time_and_refresh_preserves_binding(portal_db):  # noqa: F811
    owner, generation, payload = seed()
    before = store.profile(owner)
    confirmed = binding()
    store.save_academic_binding(owner, generation, confirmed, payload["digest"], source_scope(DETAILS))
    after = store.profile(owner)
    assert after["snapshot"] == before["snapshot"]
    assert after["fetched_at"] == before["fetched_at"]
    assert after["last_synced_at"] == before["last_synced_at"]
    assert after["profile"]["academic_binding"] == confirmed
    store.save(owner, generation, payload, {**DETAILS, "name": "New display name"})
    assert store.profile(owner)["profile"]["academic_binding"] == confirmed
    store.save(owner, generation, payload, {**DETAILS, "cohort": "69"})
    assert "academic_binding" not in store.profile(owner)["profile"]


def test_stale_and_foreign_confirmation_and_rejected_sync_leave_binding_intact(portal_db):  # noqa: F811
    owner, generation, payload = seed()
    store.save_academic_binding(owner, generation, binding(), payload["digest"], source_scope(DETAILS))
    before = store.profile(owner)
    for stale_digest, stale_scope in (("stale", source_scope(DETAILS)), (payload["digest"], "foreign")):
        with pytest.raises(PortalFailure, match="context_changed"):
            store.save_academic_binding(owner, generation, binding(), stale_digest, stale_scope)
        assert store.profile(owner) == before
    other, gen = store.owner("another-invented-owner")
    with pytest.raises(PortalFailure, match="context_changed"):
        store.save_academic_binding(other, gen, binding(), payload["digest"], source_scope(DETAILS))
    changed = copy.deepcopy(payload)
    changed["digest"] = "changed-but-incomplete"
    with pytest.raises(PortalFailure, match="incomplete_snapshot"):
        store.save(owner, generation, changed, {**DETAILS, "cohort": "69"})
    assert store.profile(owner) == before
    store.clear(owner)
    with pytest.raises(PortalFailure, match="cancelled"):
        store.save_academic_binding(owner, generation, binding(), payload["digest"], source_scope(DETAILS))


def test_concurrent_confirmation_and_identical_sync_keep_both_metadata_fields(portal_db):  # noqa: F811
    owner, generation, payload = seed()
    barrier = Barrier(2)

    def confirm():
        barrier.wait(timeout=10)
        return store.save_academic_binding(owner, generation, binding(), payload["digest"], source_scope(DETAILS))

    def sync():
        barrier.wait(timeout=10)
        return store.save(owner, generation, payload, DETAILS)

    with ThreadPoolExecutor(2) as workers:
        a, b = workers.submit(confirm), workers.submit(sync)
        assert a.result(timeout=20) == "confirmed"
        assert b.result(timeout=20) == "unchanged"
    saved = store.profile(owner)
    assert saved["last_synced_at"]
    assert saved["profile"]["academic_binding"] == binding()


def test_real_vnu_account_confirms_with_csrf_and_revoked_session_cannot_write(system, monkeypatch):  # noqa: F811
    client, engine, _ = system
    proof = dict.fromkeys(("source_host_valid", "source_path_valid", "transcript_container_valid",
        "filters_absent", "pagination_absent", "hidden_records_absent", "virtualization_absent",
        "loading_absent", "network_idle"), True)
    proof.update(layout_contract="vnu-full-table-20261025", stable_reads=3, data_table_count=1)
    payload = snapshot([["HỌC KỲ 1 - 2023-2024"],
                        ["1", "PHI1006", "Invented course", "3", "7.5", "B", "3"]], proof)

    async def collect(request):
        return {"authenticated": True, "subject": request["username"], "snapshot": payload,
                "profile": DETAILS, "cookies": []}

    monkeypatch.setattr(runtime, "collect", collect)
    assert client.post('/auth/vnu', json={'username': 'invented-real-db-test', 'password': 'synthetic'}).status_code == 200
    state = client.get('/auth/session').json()
    client.headers['x-csrf-token'] = state['csrf_token']
    options = client.get('/me/academic-program').json()
    program = next(p for p in options['programs'] if p['program_id'] == options['suggested_program_id'])
    body = {"program_id": program['program_id'], "cohort": 68, "confirm": True,
            "expected_catalog_revision": program['catalog_revision'],
            "expected_source_scope": options['source_scope'],
            "expected_snapshot_digest": options['snapshot_digest']}
    before = client.get('/me/profile').json()
    assert client.post('/me/academic-program', json=body).status_code == 200
    after = client.get('/me/profile').json()
    assert after['snapshot'] == before['snapshot']
    assert after['last_synced_at'] == before['last_synced_at']
    assert client.get('/me/course-status?selected_graduation_path_id=thesis').status_code == 200
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM auth_audit_events WHERE action='confirm_academic_program'")).scalar_one() == 1
    assert client.post('/auth/logout').status_code == 200
    assert client.post('/me/academic-program', json=body).status_code == 401
