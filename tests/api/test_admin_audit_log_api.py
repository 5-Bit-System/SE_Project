"""API and integration tests for admin action audit logs."""

import uuid
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


@pytest.fixture(autouse=True)
def setup_engine(monkeypatch):
    config = dotenv_values(ENV_PATH)
    url = config.get("DATABASE_URL")
    if url:
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

    # 1. Trigger an administrative action: create a crawler source
    source_name = f"Audit Test Source {uuid.uuid4().hex[:6]}"
    create_resp = verified_client.post(
        "/admin/crawler/sources",
        json={
            "name": source_name,
            "base_url": "https://hus.vnu.edu.vn/tuyen-sinh",
            "schedule": "daily",
            "depth_limit": 2,
        },
    )
    assert create_resp.status_code == 200
    source_id = create_resp.json()["id"]

    # 2. Query audit logs
    logs_resp = verified_client.get("/admin/audit-logs?action=crawler&limit=20")
    assert logs_resp.status_code == 200
    data = logs_resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1

    # Find the created source action
    item = next((it for it in data["items"] if it["target_id"] == source_id), None)
    assert item is not None
    assert item["action"] == "crawler.create_source"
    assert item["target_type"] == "crawler_source"
    assert source_name in item["summary"]
    assert item["result"] == "ok"

    # 3. Test text search with query parameter
    search_resp = verified_client.get(f"/admin/audit-logs?q={source_id}")
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert search_data["total"] >= 1
    assert any(it["target_id"] == source_id for it in search_data["items"])

    # 4. Test summary metrics
    metrics_resp = verified_client.get("/admin/audit-logs/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert "total_events" in metrics
    assert "events_last_24h" in metrics
    assert metrics["total_events"] >= 1
