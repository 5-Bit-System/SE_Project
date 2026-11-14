"""VT-102 RED contracts. Existing APIs, invented accounts/provider, no product patch."""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.integrations.daotao import runtime, store
from app.integrations.daotao.snapshot import PortalFailure
from app.main import app
from tests.integrations.test_portal_sessions import cookie

KEY = "vt102-request-00000001"
REAL_COLLECT = runtime.collect


@pytest.fixture
def sync_client(monkeypatch, fake_accounts):
    """Hold real job execution at deterministic boundaries, not timed polling sleeps."""
    monkeypatch.setattr(runtime, "sessions", {})
    monkeypatch.setattr(runtime, "jobs", {})
    monkeypatch.setattr(runtime, "tasks", set())
    entered, release = threading.Event(), threading.Event()
    save_entered, save_release = threading.Event(), threading.Event()
    trace = {"collect": 0, "save": 0, "fail": False, "hold_save": False}

    async def collect(submitted, **options):
        trace["collect"] += 1
        if options.get("on_started"):
            options["on_started"]()
        entered.set()
        assert await asyncio.to_thread(release.wait, 5), "Test collector gate was not released"
        if trace["fail"]:
            raise PortalFailure("portal_unavailable")
        return {"subject": submitted["subject"], "profile": {}, "snapshot": {
            "digest": "vt102-synthetic-snapshot", "completeness": "complete", "attempts": []}}

    def save(*args):
        trace["save"] += 1
        save_entered.set()
        if trace["hold_save"]:
            assert save_release.wait(5), "Test save gate was not released"
        return "saved"

    monkeypatch.setattr(runtime, "collect", collect)
    monkeypatch.setattr(store, "save", save)

    async def drain():
        await asyncio.gather(*list(runtime.tasks), return_exceptions=True)

    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        principal = fake_accounts.issue(client, linked=True, cookies=[cookie()])
        client.trace = trace
        client.entered = entered
        client.release = release
        client.save_entered = save_entered
        client.save_release = save_release
        client.principal = principal
        client.finish = lambda: (release.set(), save_release.set(), client.portal.call(drain))
        try:
            yield client
        finally:
            client.finish()


def submit(client, key=KEY, **kwargs):
    headers = {} if key is None else {"Idempotency-Key": key}
    return client.post("/me/portal-sync", headers=headers, **kwargs)


def begin(client):
    response = submit(client, json={})
    assert response.status_code == 202
    assert client.entered.wait(3), "Background collector did not start"
    return response.json()["id"]


def assert_progress(body, job_id, state, phase, percent):
    assert {"id", "state", "phase", "progress_percent", "error", "result"} <= body.keys(), (
        "VT-102 response is missing the new progress contract", sorted(body))
    assert body["id"] == job_id
    assert body["state"] == state
    assert body["phase"] == phase
    assert type(body["progress_percent"]) is int
    assert body["progress_percent"] == percent  # Literal expected value kills mapping mutations.
    assert not {"task", "session", "cookies", "password", "owner"} & body.keys()


def test_tc01_ack_precedes_completion_and_poll_has_progress(sync_client):
    client = sync_client
    job_id = begin(client)
    assert client.trace["save"] == 0
    response = client.get(f"/me/portal-sync/{job_id}")
    assert response.status_code == 200
    assert_progress(response.json(), job_id, "running", "collecting", 25)


def test_tc02_same_key_while_running_replays_receipt(sync_client):
    client = sync_client
    job_id = begin(client)
    replay = submit(client, json={})
    assert replay.status_code == 202, "Same-key retry must replay, not return busy"
    assert replay.json()["id"] == job_id
    assert len(runtime.jobs) == 1 and client.trace["collect"] == 1
    client.finish()
    assert client.trace["save"] == 1


def test_tc03_lost_ack_retry_after_commit_does_not_repeat_side_effect(sync_client):
    client = sync_client
    job_id = begin(client)  # Pretend that this response never reached the browser.
    client.finish()
    assert client.trace["save"] == 1
    replay = submit(client)
    assert replay.status_code == 202
    assert replay.json()["id"] == job_id, "Lost-ACK retry must not create a second job"
    client.finish()
    assert len(runtime.jobs) == 1
    assert client.trace["collect"] == client.trace["save"] == 1


@pytest.mark.parametrize("key", ["", "short", "a" * 129, "invalid key with spaces"])
def test_tc04_invalid_key_never_starts_job(sync_client, key):
    response = submit(sync_client, key)
    assert response.status_code == 400, "Invalid Idempotency-Key must be rejected"
    assert not runtime.jobs
    assert sync_client.trace["collect"] == sync_client.trace["save"] == 0


@pytest.mark.parametrize("key", ["a" * 16, "a" * 128])
def test_tc05_valid_key_length_boundaries(sync_client, key):
    response = submit(sync_client, key)
    assert response.status_code == 202
    sync_client.finish()
    assert sync_client.trace["collect"] == sync_client.trace["save"] == 1


@pytest.mark.parametrize("body", [[], None, {"owner": "other"}, {"password": "invented"}])
def test_tc06_invalid_body_never_starts_job(sync_client, body):
    import json

    response = submit(sync_client, content=json.dumps(body))
    assert response.status_code == 400
    assert not runtime.jobs
    assert sync_client.trace["collect"] == sync_client.trace["save"] == 0


def test_tc07_missing_key_preserves_legacy_admission(sync_client):
    response = submit(sync_client, None)
    assert response.status_code == 202 and response.json()["state"] == "running"
    sync_client.finish()
    assert sync_client.trace["save"] == 1


def test_tc08_done_mapping_is_exactly_100(sync_client):
    client = sync_client
    job_id = begin(client)
    client.finish()
    response = client.get(f"/me/portal-sync/{job_id}")
    assert_progress(response.json(), job_id, "done", "finished", 100)
    assert response.json()["result"] == "saved" and response.json()["error"] is None


def test_tc09_provider_failure_retry_keeps_same_failed_job(sync_client):
    client = sync_client
    client.trace["fail"] = True
    job_id = begin(client)
    client.finish()
    original = client.get(f"/me/portal-sync/{job_id}").json()
    assert original["state"] == "failed" and client.trace["save"] == 0
    replay = submit(client)
    assert replay.status_code == 202 and replay.json()["id"] == job_id
    client.finish()
    assert client.trace["collect"] == 1 and client.trace["save"] == 0
    assert_progress(original, job_id, "failed", "failed", 25)


def test_tc10_40_concurrent_retries_create_one_job(sync_client):
    client = sync_client
    job_id = begin(client)
    barrier = threading.Barrier(40)

    def retry(_):
        barrier.wait(timeout=5)
        return submit(client)

    with ThreadPoolExecutor(max_workers=40) as executor:
        responses = list(executor.map(retry, range(40)))
    assert {response.status_code for response in responses} == {202}
    assert {response.json()["id"] for response in responses} == {job_id}
    client.finish()
    assert len(runtime.jobs) == 1
    assert client.trace["collect"] == client.trace["save"] == 1


def test_tc11_different_session_cannot_read_same_owner_job(sync_client, fake_accounts):
    client = sync_client
    job_id = begin(client)
    client.finish()
    fake_accounts.issue(client, linked=True, cookies=[cookie("another-synthetic-session")])
    assert client.get(f"/me/portal-sync/{job_id}").status_code == 404


def test_tc12_expired_app_session_creates_nothing(sync_client):
    sync_client.principal["expires_in"] = 0
    assert submit(sync_client).status_code == 401
    assert not runtime.jobs


def test_tc13_new_key_while_owner_busy_is_distinct_intent(sync_client):
    client = sync_client
    begin(client)
    response = submit(client, "vt102-new-intent-0002")
    assert response.status_code == 409
    assert len(runtime.jobs) == 1 and client.trace["collect"] == 1


def test_tc14_saving_phase_before_commit_is_75(sync_client):
    client = sync_client
    client.trace["hold_save"] = True
    job_id = begin(client)
    client.release.set()
    assert client.save_entered.wait(3), "Save boundary was not reached"
    response = client.get(f"/me/portal-sync/{job_id}")
    assert_progress(response.json(), job_id, "saving", "saving", 75)


def test_tc15_cancel_before_save_does_not_report_100(sync_client):
    client = sync_client
    job_id = begin(client)
    response = client.delete(f"/me/portal-sync/{job_id}")
    assert response.status_code == 200
    body = client.get(f"/me/portal-sync/{job_id}").json()
    assert_progress(body, job_id, "cancelled", "cancelled", 25)
    assert client.trace["save"] == 0


def test_tc16_body_validation_still_applies_to_reused_key(sync_client):
    begin(sync_client)
    response = submit(sync_client, json={"owner": "other"})
    assert response.status_code == 400
    assert len(runtime.jobs) == 1 and sync_client.trace["collect"] == 1


def test_tc17_expired_vnu_prompts_reauth_without_job(sync_client):
    value = runtime.sessions["app:" + sync_client.principal["session_id"]]
    runtime.clear_portal(value)
    response = submit(sync_client)
    assert response.status_code == 200 and response.json() == {"state": "reauth_required"}
    assert not runtime.jobs and sync_client.trace["collect"] == 0


def test_tc18_missing_csrf_rejects_admission(sync_client):
    sync_client.headers.pop("x-csrf-token")
    assert submit(sync_client).status_code == 403
    assert not runtime.jobs and sync_client.trace["collect"] == 0


def test_tc21_receipt_replay_precedes_expired_provider_cookie(sync_client):
    client = sync_client
    job_id = begin(client)
    client.finish()
    runtime.clear_portal(runtime.sessions["app:" + client.principal["session_id"]])
    response = submit(client)
    assert response.status_code == 202 and response.json()["id"] == job_id
    assert submit(client, "vt102-new-intent-0002").json() == {"state": "reauth_required"}
    assert client.trace["collect"] == client.trace["save"] == 1


def test_tc22_duplicate_key_headers_are_rejected(sync_client):
    response = sync_client.post("/me/portal-sync", headers=[("Idempotency-Key", KEY), ("Idempotency-Key", KEY)])
    assert response.status_code == 400
    assert not runtime.jobs


def test_tc23_queued_job_does_not_contact_vnu_after_provider_revocation(sync_client, monkeypatch):
    client = sync_client
    spawned = []
    waiting = threading.Event()

    class QueueGate(asyncio.Semaphore):
        async def acquire(self):
            waiting.set()
            return await super().acquire()

    class Process:
        returncode = 0

        async def communicate(self, body):
            import json

            request = json.loads(body)
            return json.dumps({"subject": request["subject"], "snapshot": {}}).encode(), b""

    async def create(*args, **kwargs):
        spawned.append(True)
        return Process()

    monkeypatch.setattr(runtime, "collect", REAL_COLLECT)
    monkeypatch.setattr(runtime, "slots", QueueGate(0))
    monkeypatch.setattr(asyncio, "create_subprocess_exec", create)
    response = submit(client)
    assert waiting.wait(3), "Job did not reach the collector queue"
    value = runtime.sessions["app:" + client.principal["session_id"]]
    runtime.clear_portal(value)
    client.portal.call(runtime.slots.release)
    client.finish()
    assert not spawned, "Queued work must recheck provider version before spawning"
    body = client.get('/me/portal-sync/' + response.json()["id"]).json()
    assert body["state"] == "failed" and body["progress_percent"] == 0
