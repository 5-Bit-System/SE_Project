import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from app.integrations.daotao import runtime, store
from app.main import app


@pytest.fixture
def client(monkeypatch):
    runtime.sessions.clear()
    runtime.jobs.clear()
    async def collect(value):
        return {"subject": value["username"].casefold(), "snapshot": {"synthetic": True}}
    monkeypatch.setattr(runtime, "collect", collect)
    monkeypatch.setattr(store, "owner", lambda subject: (subject, 0))
    monkeypatch.setattr(store, "save", lambda *args: "saved")
    monkeypatch.setattr(store, "profile", lambda owner: {"subject": owner})
    monkeypatch.setattr(store, "clear", lambda owner: None)
    with TestClient(app, base_url="http://127.0.0.1:8000") as value:
        value.headers["origin"] = "http://127.0.0.1:8000"
        yield value


def login(client, username="synthetic-a"):
    return client.post("/auth/portal", json={"username": username, "password": "secret-test"})


def test_authentication_expiry_rotation_and_logout(client):
    assert client.get("/me/profile").status_code == 401
    response = login(client)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert "HttpOnly" in response.headers["set-cookie"]
    profile = client.get("/me/profile").json()
    assert profile["subject"] == "synthetic-a"
    assert 0 < profile["expires_in"] <= 1800
    old = client.cookies.get("study_portal_session")
    login(client)
    assert runtime.digest(old) not in runtime.sessions
    runtime.sessions[runtime.digest(client.cookies.get("study_portal_session"))].expiry = 0
    assert client.get("/auth/me").status_code == 401
    login(client)
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/me/profile").status_code == 401


def test_csrf_invalid_body_and_no_password_echo(client):
    response = client.post("/auth/portal", json={"password": "never-echo-this"})
    assert response.status_code == 400
    assert "never-echo-this" not in response.text
    client.headers["origin"] = "https://other.invalid"
    assert login(client).status_code == 403
    assert client.post("/auth/logout").status_code == 403


def test_job_ownership_delete_and_failed_login(client, monkeypatch):
    login(client)
    runtime.jobs["other"] = {"owner": "synthetic-b", "state": "done"}
    assert client.get("/me/portal-sync/other").status_code == 404
    assert client.delete("/me/portal-sync/other").status_code == 404
    assert client.delete("/me/portal-data").status_code == 200
    assert client.get("/auth/me").status_code == 401
    from app.integrations.daotao.snapshot import PortalFailure
    async def fail(value):
        raise PortalFailure("identity_unverified")
    monkeypatch.setattr(runtime, "collect", fail)
    assert login(client).status_code == 401
    assert client.get("/me/profile").status_code == 401


def test_sync_is_bound_to_session_subject(client):
    login(client)
    response = client.post("/me/portal-sync", json={"username": "synthetic-b", "password": "x"})
    assert response.status_code == 400
    assert not runtime.jobs


@pytest.mark.parametrize("code,status", [("worker_failed", 502), ("worker_output_invalid", 502),
                                        ("timeout", 504), ("busy", 429),
                                        ("interaction_required", 409)])
def test_worker_failure_is_technical_not_bad_password(client, monkeypatch, code, status):
    from app.integrations.daotao.snapshot import PortalFailure

    async def fail(value):
        raise PortalFailure(code)

    monkeypatch.setattr(runtime, "collect", fail)
    response = login(client)
    assert response.status_code == status
    assert response.json() == {"detail": code}
    assert "secret-test" not in response.text


def test_cancelled_and_finished_jobs_are_safe(client):
    login(client)
    runtime.jobs["finished"] = {"owner": "synthetic-a", "state": "done",
                                "created": time.monotonic()}
    assert client.delete("/me/portal-sync/finished").json() == {"state": "done"}


@pytest.mark.parametrize("body", [b'[]', b'null', b'"text"', b'\xff'])
def test_malformed_credentials_never_raise_server_error(client, body):
    response = client.post("/auth/portal", content=body)
    assert response.status_code == 400
    assert response.json() == {"detail": "invalid_credentials"}


def test_logout_clears_expired_cookie_and_is_idempotent(client):
    login(client)
    for value in runtime.sessions.values():
        value.expiry = 0
    assert client.post("/auth/logout").status_code == 200
    assert not client.cookies.get("study_portal_session")
    assert not runtime.sessions
    assert client.post("/auth/logout").status_code == 200


def test_profile_not_returned_when_session_revoked_during_storage_read(client, monkeypatch):
    login(client)

    def profile(owner):
        runtime.sessions.clear()
        return {"subject": owner, "private": "must-not-return"}

    monkeypatch.setattr(store, "profile", profile)
    response = client.get("/me/profile")
    assert response.status_code == 401
    assert "must-not-return" not in response.text


def test_login_passes_only_worker_profile_to_store(client, monkeypatch):
    captured = []
    details = {"name": "Synthetic source", "program": None, "cohort": None}

    async def collect(submitted):
        assert "profile" not in submitted
        return {"subject": "synthetic-a", "snapshot": {}, "profile": details}

    monkeypatch.setattr(runtime, "collect", collect)
    monkeypatch.setattr(store, "save", lambda *args: captured.append(args))
    response = client.post("/auth/portal", json={
        "username": "synthetic-a", "password": "synthetic", "profile": {"name": "Spoof"}})
    assert response.status_code == 200
    assert captured[0][3] == details


def test_rejected_collection_keeps_new_diagnostics_separate_from_old_snapshot(client, monkeypatch):
    from app.integrations.daotao.snapshot import PortalFailure

    async def collect(submitted):
        return {"subject": submitted["username"], "snapshot": {
            "connector_version": "vnu-full-table-20261025", "completeness": "unknown",
            "unknown_rows": [], "collection_evidence": {"filters_absent": False,
                "source_host_valid": True, "stable_reads": 3, "data_table_count": 1,
                "unreviewed_private_value": "must-not-echo"},
            "rows": [["never-copy-source-rows"]]}}

    def refused(*args):
        raise PortalFailure("incomplete_snapshot")

    monkeypatch.setattr(runtime, "collect", collect)
    monkeypatch.setattr(store, "save", refused)
    monkeypatch.setattr(store, "profile", lambda owner: {"subject": owner, "profile": {},
        "snapshot": {"connector_version": "b790d6af+identity1", "completeness": "unknown"}})
    response = login(client)
    assert response.status_code == 200
    assert response.json()["warning"] == "incomplete_snapshot"
    for _ in range(2):  # Passive reload must retain the failed attempt's proof.
        response = client.get("/me/profile")
        result = response.json()
        assert result["snapshot"]["connector_version"] == "b790d6af+identity1"
        report = result["latest_collection"]
        assert report["connector_version"] == "vnu-full-table-20261025"
        assert report["save_status"] == "retained"
        assert report["evidence"]["filters_absent"] is False
        assert "must-not-echo" not in response.text
        assert "never-copy-source-rows" not in response.text
    assert client.get("/me/course-status").json()["latest_collection"] == report
    # A separate owner/session has no access to this attempt report.
    other = runtime.new_session("synthetic-b", "synthetic-b", 0)
    client.cookies.set("study_portal_session", other)
    assert client.get("/me/profile").json()["latest_collection"] is None


def test_failed_sync_reports_why_new_collection_was_not_saved(client, monkeypatch):
    from app.api.portal import sync_job
    from app.integrations.daotao.snapshot import PortalFailure

    login(client)
    value = runtime.sessions[runtime.digest(client.cookies.get("study_portal_session"))]

    async def collect(submitted):
        return {"subject": value.subject, "snapshot": {
            "connector_version": "vnu-full-table-20261025", "completeness": "unknown",
            "collection_evidence": {"network_idle": False}, "unknown_rows": []}}

    def refused(*args):
        raise PortalFailure("incomplete_snapshot")

    monkeypatch.setattr(runtime, "collect", collect)
    monkeypatch.setattr(store, "save", refused)
    job, submitted = {"state": "running"}, {"password": "synthetic"}
    asyncio.run(sync_job(job, value, submitted))
    assert job["state"] == "failed"
    assert job["error"] == "incomplete_snapshot"
    assert not submitted
    response = client.get("/me/profile")
    assert response.json()["latest_collection"]["save_status"] == "retained"
    assert response.json()["latest_collection"]["evidence"]["network_idle"] is False
