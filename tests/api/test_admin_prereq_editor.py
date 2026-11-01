"""Tests for prerequisite rule editing and dependency graph endpoints."""

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


def test_prereq_editor_api(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    # 1. Create a draft revision with 3 courses
    csv_data = """code,name,credits,prerequisites,block
MAT1001,Giải tích 1,3,,Đại cương
MAT1002,Giải tích 2,3,MAT1001,Đại cương
MAT1003,Giải tích 3,3,,Đại cương
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
    assert any(e["from"] == "MAT1001" and e["to"] == "MAT1002" for e in graph["edges"])

    # 3. Test self-reference error
    self_ref_resp = verified_client.put(
        f"/admin/catalog-revisions/{rev_id}/courses/MAT1001/prerequisites",
        json={"prerequisites": [["MAT1001"]], "reason": "Self reference"},
    )
    assert self_ref_resp.status_code == 400
    assert "tự làm tiên quyết" in self_ref_resp.json()["detail"]

    # 4. Test cycle error (MAT1001 requires MAT1002, while MAT1002 already requires MAT1001)
    cycle_resp = verified_client.put(
        f"/admin/catalog-revisions/{rev_id}/courses/MAT1001/prerequisites",
        json={"prerequisites": [["MAT1002"]], "reason": "Create cycle"},
    )
    assert cycle_resp.status_code == 400
    assert "Chu trình" in cycle_resp.json()["detail"]

    # 5. Test valid update: MAT1003 requires MAT1001 AND MAT1002
    update_resp = verified_client.put(
        f"/admin/catalog-revisions/{rev_id}/courses/MAT1003/prerequisites",
        json={
            "prerequisites": [["MAT1001"], ["MAT1002"]],
            "reason": "Thêm điều kiện tiên quyết cho Giải tích 3",
        },
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["course_code"] == "MAT1003"
    assert data["prerequisites"] == [["MAT1001"], ["MAT1002"]]

    # Verify updated graph
    g2 = verified_client.get(f"/admin/catalog-revisions/{rev_id}/prerequisite-graph").json()
    assert any(e["from"] == "MAT1001" and e["to"] == "MAT1003" for e in g2["edges"])
    assert any(e["from"] == "MAT1002" and e["to"] == "MAT1003" for e in g2["edges"])

    # 6. Test branching if revision is published/active
    # Approve and publish revision
    verified_client.post(
        f"/admin/catalog-revisions/{rev_id}/approve", json={"reason": "Phê duyệt để test publish"}
    )
    verified_client.post(
        f"/admin/catalog-revisions/{rev_id}/publish", json={"reason": "Phát hành chính thức"}
    )

    # Now edit course rules on the published revision -> should branch into a new draft revision
    branch_resp = verified_client.put(
        f"/admin/catalog-revisions/{rev_id}/courses/MAT1003/prerequisites",
        json={
            "prerequisites": [["MAT1001"]],
            "reason": "Rút gọn điều kiện MAT1003 trên bản đã phát hành",
        },
    )
    assert branch_resp.status_code == 200
    b_data = branch_resp.json()
    assert b_data["branched"] is True
    assert b_data["revision_id"] != rev_id
    assert b_data["prerequisites"] == [["MAT1001"]]

    # Verify original published revision remains untouched
    orig_rev = verified_client.get(f"/admin/catalog-revisions/{rev_id}").json()
    assert orig_rev["is_active"] is True
    assert orig_rev["status"] == "published"
    c_orig = [c for c in orig_rev["payload"]["courses"] if c["code"] == "MAT1003"][0]
    assert c_orig["prerequisites"] == [["MAT1001"], ["MAT1002"]]
