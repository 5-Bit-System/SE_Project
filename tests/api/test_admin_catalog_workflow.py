"""API workflow tests for curriculum diff, approval, publish and rollback."""

import pytest

from tests.support.admin_database import admin_test_engine

pytestmark = pytest.mark.hus_postgres



@pytest.fixture(autouse=True)
def setup_engine(monkeypatch):
    eng = admin_test_engine()
    monkeypatch.setattr("app.api.admin.engine", lambda: eng)


def test_workflow_full_lifecycle(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    # 1. Create two revisions
    csv1 = """code,name,credits,prerequisites,block
CME1000,Giải tích 1,3,,Đại cương
FLF1107,Giải tích 2,3,CME1000,Đại cương
"""
    r1 = verified_client.post(
        "/admin/catalog-revisions/import",
        json={"program_id": "khdl_7460108_2022", "version_title": "v1 Ban đầu", "csv_content": csv1},
    ).json()
    rev1_id = r1["revision_id"]

    csv2 = """code,name,credits,prerequisites,block
CME1000,Giải tích 1 (Mới),4,,Đại cương
FLF1307,Nhập môn KHDL,3,,Cơ sở ngành
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
    assert diff["summary"]["added_count"] == 1  # FLF1307 added
    assert diff["summary"]["removed_count"] == 1  # FLF1107 removed
    assert diff["summary"]["modified_count"] == 1  # CME1000 modified (name + credits)

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
    # A draft prepared before v1 publication has a stale canonical base.
    verified_client.post(f"/admin/catalog-revisions/{rev2_id}/approve", json={"reason": "Duyệt bản cũ"})
    assert verified_client.post(f"/admin/catalog-revisions/{rev2_id}/publish", json={"reason": "Bản cũ"}).status_code == 400
    rev2_id = verified_client.post("/admin/catalog-revisions/import", json={"program_id": "khdl_7460108_2022", "version_title": "v2 reviewed against v1", "csv_content": csv2}).json()["revision_id"]
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
CME1000,Giải tích 1,3,,Đại cương
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
