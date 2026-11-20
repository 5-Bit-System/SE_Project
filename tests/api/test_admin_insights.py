"""The aggregate admin insight endpoint remains admin-only."""

from fastapi.testclient import TestClient

from app.main import app


def test_admin_insights_rejects_anonymous():
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        assert client.get("/admin/insights").status_code == 401


def test_admin_insights_rejects_student(verified_client):
    assert verified_client.get("/admin/insights").status_code == 403


def test_admin_insights_returns_aggregate_for_admin(verified_client, fake_accounts, monkeypatch):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"
    payload = {"students": {"status": "available", "data": {"students_total": 2}},
               "courses": {"status": "available", "data": {"course_memberships": 4}}}
    monkeypatch.setattr("app.api.admin.collect_admin_insights", lambda: payload)
    response = verified_client.get("/admin/insights")
    assert response.status_code == 200
    assert response.json() == payload
