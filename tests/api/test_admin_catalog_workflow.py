"""API workflow tests for curriculum diff, approval, publish and rollback."""

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


def test_workflow_full_lifecycle(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    # 1. Create two revisions
    csv1 = """code,name,credits,prerequisites,block
MAT1001,Giải tích 1,3,,Đại cương
MAT1002,Giải tích 2,3,MAT1001,Đại cương
"""
    r1 = verified_client.post(
        "/admin/catalog-revisions/import",
        json={"program_id": "khdl_7460108_2022", "version_title": "v1 Ban đầu", "csv_content": csv1},
    ).json()
    rev1_id = r1["revision_id"]

    csv2 = """code,name,credits,prerequisites,block
MAT1001,Giải tích 1 (Mới),4,,Đại cương
DAT2001,Nhập môn KHDL,3,,Cơ sở ngành
"""
    r2 = verified_client.post(
        "/admin/catalog-revisions/import",
        json={"program_id": "khdl_7460108_2022", "version_title": "v2 Cập nhật", "csv_content": csv2},
    ).json()
    rev2_id = r2["revision_id"]

    # 2. Test Diff between rev2 and rev1
    diff_resp = verified_client.get(f"/admin/catalog-revisions/{rev2_id}/diff?base_revision_id={rev1_id}")
    assert diff_resp.status_code == 200
    diff = diff_resp.json()
    assert diff["summary"]["added_count"] == 1  # DAT2001 added
    assert diff["summary"]["removed_count"] == 1  # MAT1002 removed
    assert diff["summary"]["modified_count"] == 1  # MAT1001 modified (name + credits)

    # 3. Test publish before approval fails
    pub_fail = verified_client.post(f"/admin/catalog-revisions/{rev1_id}/publish", json={"reason": "Vội vàng"})
    assert pub_fail.status_code == 400
    assert "approved" in pub_fail.json()["detail"]

    # 4. Test approve rev1 (requires reason)
    appr_fail = verified_client.post(f"/admin/catalog-revisions/{rev1_id}/approve", json={"reason": ""})
    assert appr_fail.status_code in (400, 422)

    appr_ok = verified_client.post(
        f"/admin/catalog-revisions/{rev1_id}/approve",
        json={"reason": "Hội đồng khoa học đã thông qua", "notes": "Chuẩn bị áp dụng"},
    )
    assert appr_ok.status_code == 200
    assert appr_ok.json()["status"] == "approved"

    # 5. Publish rev1
    pub_ok = verified_client.post(
        f"/admin/catalog-revisions/{rev1_id}/publish",
        json={"reason": "Ban hành chính thức học kỳ 1"},
    )
    assert pub_ok.status_code == 200
    assert pub_ok.json()["is_active"] is True

    # 6. Approve and Publish rev2 -> rev1 deactivated atomically
    verified_client.post(f"/admin/catalog-revisions/{rev2_id}/approve", json={"reason": "Duyệt v2"})
    pub2_ok = verified_client.post(f"/admin/catalog-revisions/{rev2_id}/publish", json={"reason": "Ban hành v2"})
    assert pub2_ok.status_code == 200
    assert pub2_ok.json()["is_active"] is True

    # 7. Rollback to rev1
    rollback_ok = verified_client.post(
        f"/admin/catalog-revisions/{rev1_id}/rollback",
        json={"reason": "Khôi phục v1 do v2 phát sinh lỗi chương trình"},
    )
    assert rollback_ok.status_code == 200
    assert rollback_ok.json()["revision_id"] == rev1_id
    assert rollback_ok.json()["is_active"] is True
