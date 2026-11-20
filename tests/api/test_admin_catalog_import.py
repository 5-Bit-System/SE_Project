"""Tests for admin catalog revision import and validation endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.support.admin_database import admin_test_engine

pytestmark = pytest.mark.hus_postgres



@pytest.fixture(autouse=True)
def setup_engine(monkeypatch):
    eng = admin_test_engine()
    monkeypatch.setattr("app.api.admin.engine", lambda: eng)


def test_import_anonymous_rejected():
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        response = client.post(
            "/admin/catalog-revisions/import",
            json={"program_id": "p", "version_title": "t", "csv_content": "code,name,credits\nM1,N1,3"},
        )
        assert response.status_code == 401


def test_import_student_forbidden(verified_client):
    response = verified_client.post(
        "/admin/catalog-revisions/import",
        json={"program_id": "p", "version_title": "t", "csv_content": "code,name,credits\nM1,N1,3"},
    )
    assert response.status_code == 403


def test_import_admin_authorized(verified_client, fake_accounts):
    # Promote session to admin
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    csv_data = """code,name,credits,prerequisites,block
MAT1001,Giải tích 1,3,,Đại cương
MAT1002,Giải tích 2,3,MAT1001,Đại cương
"""
    payload = {
        "program_id": "khdl_7460108_2022",
        "version_title": "K68 Nhập khẩu thử nghiệm",
        "cohort": "2026",
        "csv_content": csv_data,
        "filename": "curriculum_k68.csv",
    }

    response = verified_client.post("/admin/catalog-revisions/import", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["revision_id"].startswith("rev_")
    assert data["status"] in ("draft", "validated")
    assert data["validation_summary"]["valid"] is True
    assert data["validation_summary"]["stats"]["course_count"] == 2

    rev_id = data["revision_id"]

    # Test validation detail endpoint
    val_resp = verified_client.get(f"/admin/catalog-revisions/{rev_id}/validation")
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["revision_id"] == rev_id
    assert val_data["validation_summary"]["valid"] is True

    # Crucial assertion: Active catalog remains unchanged! (fixture has 14 courses, imported has 2)
    prog_resp = verified_client.get("/admin/programs")
    assert prog_resp.status_code == 200
    programs = prog_resp.json()
    khdl = next(p for p in programs if p["program_id"] == "khdl_7460108_2022")
    assert khdl["catalog_status"] == "draft_unverified"
    assert khdl["course_count"] == 14  # Still the fixture's 14 courses, NOT the imported 2!
