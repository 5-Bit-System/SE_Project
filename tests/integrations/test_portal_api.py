import asyncio
import time

import pytest
from fastapi.testclient import TestClient

from app.integrations.daotao import runtime, store
from app.main import app


@pytest.fixture
def client(monkeypatch, fake_accounts):
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
        value.fake_accounts = fake_accounts
        yield value


def login(client, username="synthetic-a"):
    if not client.fake_accounts.resolve(client.cookies.get('study_app_session')):
        client.fake_accounts.issue(client)
    return client.post("/me/portal-connection", json={"username": username, "password": "secret-test"})


def test_authentication_expiry_rotation_and_logout(client):
    assert client.get("/me/profile").status_code == 401
    response = login(client)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    # Connecting VNU must not issue or replace an application login cookie.
    assert 'set-cookie' not in response.headers
    profile = client.get("/me/profile").json()
    assert profile["subject"] == "synthetic-a"
    assert 0 < profile["expires_in"] <= 1800
    old = client.cookies.get("study_app_session")
    login(client)
    assert client.cookies.get('study_app_session') == old
    client.fake_accounts.resolve(old)['expires_in'] = 0
    assert client.get("/auth/me").status_code == 401
    login(client)
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/me/profile").status_code == 401


def test_session_status_is_public_but_profile_remains_protected(client, monkeypatch):
    def forbidden_read(*args):
        pytest.fail("Session status must never read stored personal data")

    monkeypatch.setattr(store, "profile", forbidden_read)
    for cookie in (None, "unrecognized-test-token"):
        if cookie:
            client.cookies.set("study_app_session", cookie)
        response = client.get("/auth/session")
        assert response.status_code == 200
        assert response.json() == {"authenticated": False}
        assert response.headers["cache-control"] == "no-store"
        assert client.get("/me/profile").status_code == 401
    client.cookies.clear()
    login(client)
    response = client.get("/auth/session")
    assert response.json()['authenticated'] is True
    assert 'snapshot' not in response.json() and 'profile' not in response.json()
    client.fake_accounts.resolve(client.cookies.get('study_app_session'))['expires_in'] = 0
    assert client.get("/auth/session").json() == {"authenticated": False}
    # Provider cookie cleanup is separately bounded by its RAM TTL/reaper.
    assert client.get("/me/profile").status_code == 401


def test_csrf_invalid_body_and_no_password_echo(client):
    client.fake_accounts.issue(client)
    response = client.post("/me/portal-connection", json={"password": "never-echo-this"})
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
    assert client.get("/auth/me").status_code == 200
    from app.integrations.daotao.snapshot import PortalFailure
    async def fail(value):
        raise PortalFailure("identity_unverified")
    monkeypatch.setattr(runtime, "collect", fail)
    assert login(client).status_code == 409
    assert client.get("/me/profile").json()['subject'] is None


def test_sync_is_bound_to_session_subject(client):
    login(client)
    response = client.post("/me/portal-sync", json={"username": "synthetic-b", "password": "x"})
    assert response.status_code == 400
    assert not runtime.jobs


@pytest.mark.parametrize("code,status", [("worker_failed", 502), ("worker_output_invalid", 502),
                                        ("timeout", 504), ("busy", 429),
                                        ("browser_unavailable", 503), ("portal_unavailable", 502),
                                        ("network_access_denied", 503),
                                        ("structure_changed", 502),
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


def test_student_login_network_block_never_creates_an_account_or_retries(client, monkeypatch):
    from app.api.portal import account_portal
    from app.integrations.daotao.snapshot import PortalFailure

    submissions = []

    async def fail(value):
        submissions.append(value)
        raise PortalFailure("network_access_denied")

    def forbid_signin(*args):
        pytest.fail("A network failure must never create an identity or session")

    monkeypatch.setattr(runtime, "collect", fail)
    monkeypatch.setattr(account_portal, "signin", forbid_signin)
    response = client.post('/auth/vnu', json={'username': 'synthetic', 'password': 'never-log'})
    assert response.status_code == 503
    assert response.json() == {'detail': 'network_access_denied'}
    assert 'set-cookie' not in response.headers
    assert submissions == [{}], "Credentials must be cleared, without automatic resubmission"
    assert client.get('/auth/session').json() == {'authenticated': False}


def test_cancelled_and_finished_jobs_are_safe(client):
    login(client)
    runtime.jobs["finished"] = {"owner": "synthetic-a", "state": "done",
                                "created": time.monotonic(),
                                "session": next(iter(runtime.sessions.values()))}
    assert client.delete("/me/portal-sync/finished").json() == {"state": "done"}


@pytest.mark.parametrize("body", [b'[]', b'null', b'"text"', b'\xff'])
def test_malformed_credentials_never_raise_server_error(client, body):
    client.fake_accounts.issue(client)
    response = client.post("/me/portal-connection", content=body)
    assert response.status_code == 400
    assert response.json() == {"detail": "invalid_credentials"}


def test_logout_clears_expired_cookie_and_is_idempotent(client):
    login(client)
    client.fake_accounts.resolve(client.cookies.get('study_app_session'))['expires_in'] = 0
    assert client.post("/auth/logout").status_code == 200
    assert not client.cookies.get("study_app_session")
    assert not runtime.sessions
    assert client.post("/auth/logout").status_code == 200


def test_profile_not_returned_when_session_revoked_during_storage_read(client, monkeypatch):
    login(client)

    def profile(owner):
        client.fake_accounts.revoke(client.cookies.get('study_app_session'))
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
    client.fake_accounts.issue(client)
    response = client.post("/me/portal-connection", json={
        "username": "synthetic-a", "password": "synthetic", "profile": {"name": "Spoof"}})
    assert response.status_code == 400
    assert captured == []
    response = client.post('/me/portal-connection', json={'username': 'synthetic-a', 'password': 'synthetic'})
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
    client.fake_accounts.issue(client, "synthetic-b", linked=True)
    assert client.get("/me/profile").json()["latest_collection"] is None


def test_failed_sync_reports_why_new_collection_was_not_saved(client, monkeypatch):
    from app.api.portal import sync_job
    from app.integrations.daotao.snapshot import PortalFailure

    login(client)
    principal = client.fake_accounts.resolve(client.cookies.get("study_app_session"))
    value = runtime.sessions["app:" + principal["session_id"]]

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
