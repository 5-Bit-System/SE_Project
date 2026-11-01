"""API tests for admin curriculum and courses inspection endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_admin_programs_anonymous_rejected():
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        response = client.get("/admin/programs")
        assert response.status_code == 401
        assert response.json().get("detail") == "session_expired"


def test_admin_programs_student_forbidden(verified_client):
    response = verified_client.get("/admin/programs")
    assert response.status_code == 403
    assert response.json().get("detail") == "forbidden"


def test_admin_programs_admin_authorized(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    response = verified_client.get("/admin/programs")
    assert response.status_code == 200
    programs = response.json()
    assert isinstance(programs, list)
    assert len(programs) >= 1

    first = programs[0]
    assert "program_id" in first
    assert "name" in first
    assert "total_credits" in first
    assert "course_count" in first
    assert first["catalog_status"] == "draft_unverified"
    assert "source_file" in first
    assert "source_pages" in first


def test_admin_courses_admin_authorized(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    # 1. Fetch valid program id first
    progs_resp = verified_client.get("/admin/programs")
    assert progs_resp.status_code == 200
    program_id = progs_resp.json()[0]["program_id"]

    # 2. Fetch courses
    response = verified_client.get(f"/admin/courses?program_id={program_id}")
    assert response.status_code == 200
    courses = response.json()
    assert isinstance(courses, list)
    assert len(courses) > 0

    first = courses[0]
    assert "code" in first
    assert "name" in first
    assert "credits" in first
    assert "block" in first
    assert "prerequisite_status" in first
    assert first["prerequisite_status"] in {"draft_unverified", "verified"}


def test_admin_courses_not_found(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    response = verified_client.get("/admin/courses?program_id=non_existent_program_9999")
    assert response.status_code == 404
