"""API authorization and contract tests for GET /admin/overview."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_admin_overview_anonymous_rejected():
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        response = client.get("/admin/overview")
        assert response.status_code == 401
        assert response.json().get("detail") == "session_expired"


def test_admin_overview_student_forbidden(verified_client):
    response = verified_client.get("/admin/overview")
    assert response.status_code == 403
    assert response.json().get("detail") == "forbidden"


def test_admin_overview_admin_authorized(verified_client, fake_accounts):
    # Promote the authenticated test session to admin
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    response = verified_client.get("/admin/overview")
    assert response.status_code == 200

    data = response.json()
    # Contract checks: all 5 named metrics must exist with truthful metadata
    for metric_name in (
        "accounts_total",
        "programs_count",
        "courses_count",
        "catalog_status",
        "system_readiness",
    ):
        assert metric_name in data, f"Missing metric: {metric_name}"
        metric = data[metric_name]
        assert "status" in metric
        assert metric["status"] in {"available", "unavailable"}
        assert "source" in metric
        assert "updated_at" in metric

    # Catalog status contract check: currently draft_unverified
    assert data["catalog_status"]["value"] == "draft_unverified"
