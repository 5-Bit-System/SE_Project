"""Tests for prerequisite rule editing and dependency graph endpoints."""

import pytest

from tests.support.admin_database import admin_test_engine

pytestmark = pytest.mark.hus_postgres



@pytest.fixture(autouse=True)
def setup_engine(monkeypatch):
    eng = admin_test_engine()
    monkeypatch.setattr("app.api.admin.engine", lambda: eng)


def test_prereq_editor_api(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    # 1. Create a draft revision with 3 courses
    csv_data = """code,name,credits,prerequisites,block
CME1000,Giải tích 1,3,,Đại cương
FLF1107,Giải tích 2,3,CME1000,Đại cương
FLF1207,Giải tích 3,3,,Đại cương
"""
    r = verified_client.post(
        "/admin/catalog-revisions/import",
        json={
            "program_id": "khdl_7460108_2022",
            "version_title": "Rule Editor Test",
            "csv_content": csv_data,
        },
    ).json()
    rev_id = r["revision_id"]

    # 2. Test Get Prerequisite Graph
    graph_resp = verified_client.get(f"/admin/catalog-revisions/{rev_id}/prerequisite-graph")
    assert graph_resp.status_code == 200
    graph = graph_resp.json()
    assert graph["total_nodes"] == 3
    assert any(e["from"] == "CME1000" and e["to"] == "FLF1107" for e in graph["edges"])

    # 3. Test self-reference error
    self_ref_resp = verified_client.put(
        f"/admin/catalog-revisions/{rev_id}/courses/CME1000/prerequisites",
        json={"prerequisites": [["CME1000"]], "reason": "Self reference"},
    )
    assert self_ref_resp.status_code == 400
    assert "tự làm tiên quyết" in self_ref_resp.json()["detail"]

    # 4. Test cycle error (CME1000 requires FLF1107, while FLF1107 already requires CME1000)
    cycle_resp = verified_client.put(
        f"/admin/catalog-revisions/{rev_id}/courses/CME1000/prerequisites",
        json={"prerequisites": [["FLF1107"]], "reason": "Create cycle"},
    )
    assert cycle_resp.status_code == 400
    assert "Chu trình" in cycle_resp.json()["detail"]

    # 5. Test valid update: FLF1207 requires CME1000 AND FLF1107
    update_resp = verified_client.put(
        f"/admin/catalog-revisions/{rev_id}/courses/FLF1207/prerequisites",
        json={
            "prerequisites": [["CME1000"], ["FLF1107"]],
            "reason": "Thêm điều kiện tiên quyết cho Giải tích 3",
        },
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["course_code"] == "FLF1207"
    assert data["prerequisites"] == [["CME1000"], ["FLF1107"]]

    # Verify updated graph
    g2 = verified_client.get(f"/admin/catalog-revisions/{rev_id}/prerequisite-graph").json()
    assert any(e["from"] == "CME1000" and e["to"] == "FLF1207" for e in g2["edges"])
    assert any(e["from"] == "FLF1107" and e["to"] == "FLF1207" for e in g2["edges"])

    # 6. Test branching if revision is published/active
    # Revalidate, approve and publish revision
    val_resp = verified_client.post(f"/admin/catalog-revisions/{rev_id}/validate")
    assert val_resp.status_code == 200
    appr_resp = verified_client.post(
        f"/admin/catalog-revisions/{rev_id}/approve", json={"reason": "Phê duyệt để test publish"}
    )
    assert appr_resp.status_code == 200
    pub_resp = verified_client.post(
        f"/admin/catalog-revisions/{rev_id}/publish", json={"reason": "Phát hành chính thức"}
    )
    assert pub_resp.status_code == 200

    # Now edit course rules on the published revision -> should branch into a new draft revision
    branch_resp = verified_client.put(
        f"/admin/catalog-revisions/{rev_id}/courses/FLF1207/prerequisites",
        json={
            "prerequisites": [["CME1000"]],
            "reason": "Rút gọn điều kiện FLF1207 trên bản đã phát hành",
        },
    )
    assert branch_resp.status_code == 200
    b_data = branch_resp.json()
    assert b_data["branched"] is True
    assert b_data["revision_id"] != rev_id
    assert b_data["prerequisites"] == [["CME1000"]]

    # Verify original published revision remains untouched
    orig_rev = verified_client.get(f"/admin/catalog-revisions/{rev_id}").json()
    assert orig_rev["is_active"] is True
    assert orig_rev["status"] == "published"
    c_orig = [c for c in orig_rev["payload"]["courses"] if c["code"] == "FLF1207"][0]
    assert c_orig["prerequisites"] == [["CME1000"], ["FLF1107"]]


def test_editing_approved_revision_revokes_approval_and_blocks_publish(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    csv_data = """code,name,credits,prerequisites,block
CME1000,Giải tích 1,3,,Đại cương
FLF1107,Giải tích 2,3,CME1000,Đại cương
"""
    r = verified_client.post(
        "/admin/catalog-revisions/import",
        json={"program_id": "khdl_7460108_2022", "version_title": "Approval Revoke Test", "csv_content": csv_data},
    ).json()
    rev_id = r["revision_id"]

    # Approve
    appr_resp = verified_client.post(
        f"/admin/catalog-revisions/{rev_id}/approve",
        json={"reason": "Duyệt trước khi sửa luật"},
    )
    assert appr_resp.status_code == 200
    rev_before = verified_client.get(f"/admin/catalog-revisions/{rev_id}").json()
    assert rev_before["status"] == "approved"
    assert rev_before["review_decision"] == "approved"

    # Now edit course rules on the approved revision
    edit_resp = verified_client.put(
        f"/admin/catalog-revisions/{rev_id}/courses/FLF1107/prerequisites",
        json={"prerequisites": [], "reason": "Xóa tiên quyết khi đã duyệt"},
    )
    assert edit_resp.status_code == 200

    # Revision MUST have been returned to 'draft', with review and validation cleared
    rev_after = verified_client.get(f"/admin/catalog-revisions/{rev_id}").json()
    assert rev_after["status"] == "draft"
    assert rev_after["reviewed_by"] is None
    assert rev_after["reviewed_at"] is None
    assert rev_after["review_decision"] is None
    assert rev_after["validation_summary"] == {}

    # Attempt to publish must be rejected
    pub_resp = verified_client.post(
        f"/admin/catalog-revisions/{rev_id}/publish",
        json={"reason": "Cố tình xuất bản khi đã bị thu hồi duyệt"},
    )
    assert pub_resp.status_code == 400
    assert "approved" in pub_resp.json()["detail"].lower()
