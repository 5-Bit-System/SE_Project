"""API and integration tests for admin action audit logs."""

import os
import uuid
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine

pytestmark = pytest.mark.hus_postgres

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


@pytest.fixture(autouse=True)
def setup_engine(monkeypatch):
    config = dotenv_values(ENV_PATH)
    url = os.environ.get("HUS_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL") or config.get("DATABASE_URL")
    if not url:
        pytest.skip("PostgreSQL database URL not configured")
    eng = create_engine(url)
    monkeypatch.setattr("app.api.admin.engine", lambda: eng)


def test_audit_log_access_forbidden_for_non_admin(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "student"

    resp = verified_client.get("/admin/audit-logs")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "forbidden"


def test_audit_log_lifecycle_and_actions(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    # 1. Trigger an administrative action: create an academic announcement
    ann_title = f"Audit Test Announcement {uuid.uuid4().hex[:6]}"
    create_resp = verified_client.post(
        "/admin/announcements",
        json={
            "title": ann_title,
            "content": "Audit test content for privileged action log verification",
            "source_url": "https://hus.vnu.edu.vn/announcements",
            "target_audience": "all",
            "effective_date": "2026-11-01T00:00:00Z",
        },
    )
    assert create_resp.status_code in (200, 201)
    ann_id = create_resp.json()["id"]

    # 2. Query audit logs
    logs_resp = verified_client.get("/admin/audit-logs?action=announcement&limit=20")
    assert logs_resp.status_code == 200
    data = logs_resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1

    # Find the created announcement action
    item = next((it for it in data["items"] if it["target_id"] == ann_id), None)
    assert item is not None
    assert item["action"] == "announcement.create"
    assert item["target_type"] == "announcement"
    assert ann_title in item["summary"]
    assert item["result"] == "ok"

    # 3. Test text search with query parameter
    search_resp = verified_client.get(f"/admin/audit-logs?q={ann_id}")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total"] >= 1
    assert any(it["target_id"] == ann_id for it in search_data["items"])

    # 4. Test summary metrics
    metrics_resp = verified_client.get("/admin/audit-logs/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert "total_events" in metrics
    assert "events_last_24h" in metrics
    assert metrics["total_events"] >= 1
