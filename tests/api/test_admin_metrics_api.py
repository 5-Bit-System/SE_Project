"""API authorization and contract tests for GET /admin/metrics/health."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.operational_metrics import metrics_recorder


def test_admin_metrics_anonymous_rejected():
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        response = client.get("/admin/metrics/health")
        assert response.status_code == 401
        assert response.json().get("detail") == "session_expired"


def test_admin_metrics_student_forbidden(verified_client):
    response = verified_client.get("/admin/metrics/health")
    assert response.status_code == 403
    assert response.json().get("detail") == "forbidden"


def test_admin_metrics_admin_authorized(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    # Populate a test request
    metrics_recorder.record_request(
        route_group="academic",
        path="/academic/documents",
        method="GET",
        status_code=200,
        duration_ms=42.0,
    )

    response = verified_client.get("/admin/metrics/health?window=24h")
    assert response.status_code == 200
    data = response.json()

    assert data["window"] == "24h"
    assert data["source"] == "runtime:operational_metrics"
    assert "route_groups" in data
    assert "overall_health" in data
    assert "consultation_health" in data
    assert "feedback_signals" in data

    # Academic route group should be available
    academic = data["route_groups"]["academic"]
    assert academic["status"] == "available"
    assert academic["total_requests"] >= 1
    assert academic["p50_latency_ms"] >= 0


def test_admin_metrics_invalid_window_fallback(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    response = verified_client.get("/admin/metrics/health?window=invalid")
    assert response.status_code == 200
    data = response.json()
    assert data["window"] == "24h"  # fallback default
