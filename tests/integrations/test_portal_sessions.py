"""Session-only provider state and owner-bound jobs, using invented cookies only."""

import asyncio
import copy
import json
import time

import pytest
from fastapi.testclient import TestClient

from app.api.portal import sync_job
from app.integrations.daotao import runtime, store
from app.integrations.daotao.session_state import validated_cookies
from app.integrations.daotao.snapshot import PortalFailure
from app.main import app


def cookie(value="synthetic-secret-cookie"):
    return {"name": "synthetic", "value": value, "domain": "daotao.vnu.edu.vn",
            "path": "/dkmh/", "expires": -1, "httpOnly": True, "secure": True, "sameSite": "Strict"}


@pytest.fixture
def connected(monkeypatch, fake_accounts):
    trace = {"requests": [], "saved": []}
    runtime.sessions.clear()
    runtime.jobs.clear()

    async def collect(request):
        trace["requests"].append(copy.deepcopy(request))
        subject = request.get("subject", request.get("username"))
        return {"subject": subject, "snapshot": {"synthetic": True},
                "profile": {"name": "Synthetic student"},
                "cookies": [cookie(f"synthetic-secret-{subject}-{len(trace['requests'])}")]}

    monkeypatch.setattr(runtime, "collect", collect)
    monkeypatch.setattr(store, "owner", lambda subject: (subject, 0))
    monkeypatch.setattr(store, "save", lambda *args: trace["saved"].append(args) or "unchanged")
    monkeypatch.setattr(store, "profile", lambda owner: {"subject": owner, "snapshot": {}})
    monkeypatch.setattr(store, "clear", lambda owner: None)
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        fake_accounts.issue(client)
        assert client.post("/me/portal-connection", json={"username": "synthetic-a", "password": "synthetic-password"}).status_code == 200
        yield client, trace


def active(client):
    account = client.fake_accounts.resolve(client.cookies.get('study_app_session'))
    return runtime.sessions['app:' + account['session_id']]


def finished(client, job_id):
    for _ in range(50):
        response = client.get(f"/me/portal-sync/{job_id}")
        result = response.json()
        if result.get("state") not in {"running", "saving"}:
            return result
        time.sleep(.005)
    pytest.fail("Synthetic job did not finish")


def test_sync_reuses_and_rotates_only_current_session_state(connected, caplog):
    client, trace = connected
    value = active(client)
    previous = value.portal["cookies"]
    for _ in range(2):
        response = client.post("/me/portal-sync")
        assert response.status_code == 202
        result = finished(client, response.json()["id"])
        assert result == {"state": "done", "result": "unchanged"}
        assert "synthetic-secret" not in json.dumps(result)
        assert set(trace["requests"][-1]) == {"mode", "subject", "cookies"}
        assert trace["requests"][-1]["mode"] == "resume"
        assert value.portal["cookies"][0]["value"] != trace["requests"][-1]["cookies"][0]["value"]
    assert previous == []
    assert "synthetic-secret" not in repr(value)
    assert "synthetic-secret" not in caplog.text
    assert all("cookies" not in args[2] and "cookies" not in args[3] for args in trace["saved"])
    assert client.post("/auth/logout").status_code == 200
    assert value.portal is None
    assert client.get("/me/profile").status_code == 401


@pytest.mark.parametrize("body", [{"password": "private-test"}, {"owner": "other"},
                                  {"subject": "other"}, {"cookies": [cookie()]}, [], None])
def test_sync_rejects_browser_credentials_and_owner_selection(connected, body):
    client, trace = connected
    response = client.post("/me/portal-sync", content=json.dumps(body))
    assert response.status_code == 400
    assert response.json() == {"detail": "invalid_sync_request"}
    assert len(trace["requests"]) == 1
    assert not runtime.jobs


@pytest.mark.parametrize('expired', [False, True])
def test_expired_vnu_requires_explicit_password_only_reauth_but_keeps_app_session(connected, expired):
    client, trace = connected
    value = active(client)
    if expired:
        value.portal['expiry'] = time.monotonic() - 1
    else:
        runtime.clear_portal(value)
    response = client.post("/me/portal-sync")
    assert response.status_code == 200
    assert response.json() == {'state': 'reauth_required'}
    assert response.headers['cache-control'] == 'no-store'
    assert len(trace['requests']) == 1 and not runtime.jobs
    assert value.portal is None
    assert client.get("/me/profile").status_code == 200
    assert client.post("/me/portal-reauth", json={"username": "other", "password": "private-test"}).status_code == 400
    response = client.post("/me/portal-reauth", json={"password": "private-test"})
    assert response.status_code == 202
    assert finished(client, response.json()["id"])["state"] == "done"
    assert trace["requests"][-1] == {"mode": "login", "username": value.subject, "password": "private-test"}
    assert active(client) is value and value.portal


def test_jobs_are_private_to_web_session_even_for_same_owner(connected):
    client, _ = connected
    first = active(client)
    response = client.post("/me/portal-sync")
    job_id = response.json()["id"]
    assert finished(client, job_id)["state"] == "done"
    client.fake_accounts.issue(client, first.owner, first.subject, linked=True, cookies=[cookie('other-session-cookie')])
    second = active(client)
    assert client.get(f"/me/portal-sync/{job_id}").status_code == 404
    assert client.delete(f"/me/portal-sync/{job_id}").status_code == 404
    client.post("/auth/logout")
    assert second.portal is None and first.portal is not None


def test_delete_revokes_all_sessions_of_owner(connected):
    client, _ = connected
    first = active(client)
    token = runtime.new_session(first.owner, first.subject, first.generation, [cookie("second-private")])
    second = runtime.sessions[runtime.digest(token)]
    assert client.delete("/me/portal-data").status_code == 200
    assert first.portal is None and second.portal is None
    assert not runtime.sessions


def test_periodic_reaping_clears_secrets_without_a_followup_request(monkeypatch):
    monkeypatch.setattr(runtime, "sessions", {})
    monkeypatch.setattr(runtime, "jobs", {})
    token = runtime.new_session("owner", "synthetic", 0, [cookie()])
    value = runtime.sessions[runtime.digest(token)]
    jar = value.portal["cookies"]
    value.expiry = time.monotonic() - 1
    runtime.reap()
    assert jar == [] and value.portal is None and not runtime.sessions


@pytest.mark.parametrize("reauth", [False, True])
def test_late_worker_result_cannot_restore_revoked_state_or_save(monkeypatch, reauth):
    monkeypatch.setattr(runtime, "sessions", {})
    monkeypatch.setattr(runtime, "jobs", {})
    saved = []
    monkeypatch.setattr(store, "save", lambda *args: saved.append(args))

    async def scenario():
        entered = asyncio.Event()
        token = runtime.new_session("owner", "synthetic", 0, [cookie()])
        value = runtime.sessions[runtime.digest(token)]
        original_version = value.portal_version

        async def collect(request):
            entered.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                return {"subject": "synthetic", "snapshot": {}, "cookies": [cookie("late-secret")]}

        monkeypatch.setattr(runtime, "collect", collect)
        submitted = {"mode": "login", "username": value.subject, "password": "private-test"} if reauth else runtime.resume_request(value)
        job = {"owner": value.owner, "session": value, "state": "running", "portal_version": original_version}
        task = asyncio.create_task(sync_job(job, value, submitted))
        job["task"] = task
        runtime.jobs["test"] = job
        await entered.wait()
        runtime.revoke(value)
        await task
        assert value.portal is None and not runtime.sessions
        assert job["state"] == "cancelled" and submitted == {}
        with pytest.raises(PortalFailure, match="cancelled"):
            runtime.install_portal(value, [cookie("late-secret")], original_version)

    asyncio.run(scenario())
    assert not saved


@pytest.mark.parametrize("changes", [{"domain": ".vnu.edu.vn"}, {"domain": ["bad"]},
                                     {"sameSite": []}, {"expires": float("inf")},
                                     {"value": "x" * 4097}, {"unexpected": "secret"}])
def test_cookie_schema_rejects_unsafe_scope_or_malformed_state(changes):
    with pytest.raises(PortalFailure, match="^portal_state_invalid$"):
        validated_cookies([{**cookie(), **changes}])


def test_cookie_count_and_total_size_are_bounded():
    with pytest.raises(PortalFailure):
        validated_cookies([cookie()] * 65)
    with pytest.raises(PortalFailure):
        validated_cookies([cookie("x" * 4000)] * 20)


def test_source_expiry_and_web_expiry_bound_state_lifetime(monkeypatch):
    monkeypatch.setattr(runtime, "sessions", {})
    monkeypatch.setattr(runtime, "jobs", {})
    monkeypatch.setattr(runtime.time, "monotonic", lambda: 100.0)
    monkeypatch.setattr(runtime.time, "time", lambda: 1000.0)
    token = runtime.new_session("owner", "synthetic", 0, [{**cookie(), "expires": time.time() + 10}])
    value = runtime.sessions[runtime.digest(token)]
    assert value.portal["expiry"] <= value.expiry
    assert 0 < value.portal["expiry"] - time.monotonic() <= 10
    runtime.install_portal(value, [{**cookie(), "expires": time.time() + 999999}], value.portal_version)
    assert value.portal["expiry"] == value.expiry


def test_identity_conflict_revokes_vnu_state_before_store_and_keeps_app_account(connected, monkeypatch):
    client, trace = connected
    value = active(client)

    async def conflict(request):
        return {"subject": "synthetic-other", "snapshot": {}, "cookies": [cookie("wrong-account")]}

    monkeypatch.setattr(runtime, "collect", conflict)
    saved_count = len(trace["saved"])
    client.post("/me/portal-sync")
    assert client.get("/me/profile").status_code == 200
    assert value.portal is None and len(trace["saved"]) == saved_count


def test_busy_and_technical_failure_do_not_force_reauth(connected, monkeypatch):
    client, _ = connected
    value = active(client)
    version = value.portal_version

    async def failure(request):
        raise PortalFailure("portal_unavailable")

    monkeypatch.setattr(runtime, "collect", failure)
    response = client.post("/me/portal-sync")
    assert finished(client, response.json()["id"])["error"] == "portal_unavailable"
    assert value.portal and value.portal_version == version
    runtime.jobs["busy"] = {"owner": value.owner, "session": value, "state": "saving",
                            "task": None, "created": time.monotonic()}
    response = client.post("/me/portal-reauth", json={"password": "private-test"})
    assert response.status_code == 409 and "private-test" not in response.text
    runtime.jobs.pop("busy")


def test_expired_before_job_starts_does_not_launch_worker(monkeypatch):
    monkeypatch.setattr(runtime, "sessions", {})
    monkeypatch.setattr(runtime, "jobs", {})
    calls = []

    async def collect(request):
        calls.append(request)

    monkeypatch.setattr(runtime, "collect", collect)

    async def scenario():
        value = runtime.Session("owner", "synthetic", 0, time.monotonic() - 1)
        runtime.sessions["synthetic"] = value
        submitted = {"password": "private-test"}
        job = {"state": "running"}
        await sync_job(job, value, submitted)
        assert job["state"] == "failed" and submitted == {}

    asyncio.run(scenario())
    assert not calls


def test_cookie_reaped_during_read_requires_reauth_and_never_saves(monkeypatch):
    monkeypatch.setattr(runtime, "sessions", {})
    monkeypatch.setattr(runtime, "jobs", {})
    saved = []
    monkeypatch.setattr(store, "save", lambda *args: saved.append(args))

    async def scenario():
        token = runtime.new_session("owner", "synthetic", 0, [cookie()])
        value = runtime.sessions[runtime.digest(token)]

        async def collect(request):
            value.portal["expiry"] = time.monotonic() - 1
            runtime.reap()
            return {"subject": value.subject, "snapshot": {}, "cookies": [cookie("late-rotation")]}

        monkeypatch.setattr(runtime, "collect", collect)
        job = {"state": "running", "portal_version": value.portal_version}
        await sync_job(job, value, runtime.resume_request(value))
        assert job["error"] == "vnu_reauth_required" and value.portal is None

    asyncio.run(scenario())
    assert not saved


def test_shutdown_discards_state_and_stops_cleanup_task(monkeypatch):
    monkeypatch.setattr(runtime, "sessions", {})
    monkeypatch.setattr(runtime, "jobs", {})
    monkeypatch.setattr(runtime, "tasks", set())

    async def scenario():
        runtime.startup()
        token = runtime.new_session("owner", "synthetic", 0, [cookie()])
        value = runtime.sessions[runtime.digest(token)]
        jar = value.portal["cookies"]
        assert runtime.cleanup_task is not None
        await runtime.shutdown()
        assert jar == [] and value.portal is None
        assert not runtime.sessions and runtime.cleanup_task is None

    asyncio.run(scenario())
