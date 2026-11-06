"""API authorization and contract tests for POST /admin/recommendations/preview."""

from fastapi.testclient import TestClient

from app.catalog import list_catalogs
from app.main import app


def test_preview_anonymous_rejected():
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        response = client.post(
            "/admin/recommendations/preview",
            json={"program_id": "test", "passed_course_codes": []},
        )
        assert response.status_code == 401
        assert response.json().get("detail") == "session_expired"


def test_preview_student_forbidden(verified_client):
    response = verified_client.post(
        "/admin/recommendations/preview",
        json={"program_id": "test", "passed_course_codes": []},
    )
    assert response.status_code == 403
    assert response.json().get("detail") == "forbidden"


def test_preview_admin_authorized(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    catalogs = list_catalogs()
    prog_id = catalogs[0].program.program_id

    response = verified_client.post(
        "/admin/recommendations/preview",
        json={
            "program_id": prog_id,
            "passed_course_codes": [],
            "max_credits": 16,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_simulated"] is True
    assert "recommendations" in data
    assert "eligible_courses" in data
    assert "blocked_courses" in data
    assert data["total_eligible"] >= 1


def test_preview_invalid_program_404(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    response = verified_client.post(
        "/admin/recommendations/preview",
        json={"program_id": "nonexistent_prog_999", "passed_course_codes": []},
    )
    assert response.status_code == 404
