"""API workflow tests for curriculum diff, approval, publish and rollback."""

import os
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


def test_malformed_import_blocks_approval_and_publication(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    # Malformed CSV missing 'credits' column
    bad_csv = """code,name,prerequisites,block
MAT9999,Giải tích lỗi,,Đại cương
"""
    imp_resp = verified_client.post(
        "/admin/catalog-revisions/import",
        json={"program_id": "khdl_7460108_2022", "version_title": "Bản lỗi thiếu tín chỉ", "csv_content": bad_csv},
    )
    assert imp_resp.status_code == 200
    res = imp_resp.json()
    rev_id = res["revision_id"]
    assert res["status"] == "draft"
    assert res["validation_summary"]["valid"] is False
    assert len(res["validation_summary"]["errors"]) > 0

    # Attempt approve must fail
    appr_resp = verified_client.post(
        f"/admin/catalog-revisions/{rev_id}/approve",
        json={"reason": "Cố tình duyệt bản lỗi"},
    )
    assert appr_resp.status_code == 400
    assert "validation" in appr_resp.json()["detail"].lower()

    # Attempt publish must fail
    pub_resp = verified_client.post(
        f"/admin/catalog-revisions/{rev_id}/publish",
        json={"reason": "Cố tình xuất bản bản lỗi"},
    )
    assert pub_resp.status_code == 400
    assert ("validation" in pub_resp.json()["detail"].lower() or "approved" in pub_resp.json()["detail"].lower())


def test_rollback_api_rejects_unreviewed_or_draft_revision(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    csv_draft = """code,name,credits,prerequisites,block
MAT1001,Giải tích 1,3,,Đại cương
"""
    imp_resp = verified_client.post(
        "/admin/catalog-revisions/import",
        json={"program_id": "khdl_7460108_2022", "version_title": "Bản nháp chưa xuất bản", "csv_content": csv_draft},
    )
    assert imp_resp.status_code == 200
    draft_id = imp_resp.json()["revision_id"]

    # Rollback to this never-published draft must be rejected with 400
    rb_resp = verified_client.post(
        f"/admin/catalog-revisions/{draft_id}/rollback",
        json={"reason": "Thử rollback về bản nháp"},
    )
    assert rb_resp.status_code == 400
    assert "previously published" in rb_resp.json()["detail"].lower()
