"""API authorization and contract tests for /admin/announcements and /academic/announcements."""

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app


def test_announcements_anonymous_rejected():
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        client.headers["origin"] = "http://127.0.0.1:8000"
        response = client.get("/admin/announcements")
        assert response.status_code == 401


def test_announcements_student_forbidden(verified_client):
    response = verified_client.get("/admin/announcements")
    assert response.status_code == 403


def test_announcements_admin_crud(verified_client, fake_accounts):
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=15)

    # 1. Create announcement
    create_resp = verified_client.post(
        "/admin/announcements",
        json={
            "title": "Thông báo thi cuối kỳ ĐHQGHN",
            "content": "Lịch thi chi tiết được đăng tải tại cổng thông tin.",
            "source_url": "https://hus.vnu.edu.vn/thi-cuoi-ky.pdf",
            "audience": "students",
            "effective_date": now.isoformat(),
            "expiry_date": future.isoformat(),
        },
    )
    assert create_resp.status_code == 201
    ann = create_resp.json()
    ann_id = ann["id"]
    assert ann["status"] == "draft"

    # 2. List announcements
    list_resp = verified_client.get("/admin/announcements")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert any(x["id"] == ann_id for x in items)

    # 3. Publish announcement
    pub_resp = verified_client.post(f"/admin/announcements/{ann_id}/publish")
    assert pub_resp.status_code == 200
    assert pub_resp.json()["status"] == "published"

    # 4. Check public endpoint returns it
    public_resp = verified_client.get("/academic/announcements")
    assert public_resp.status_code == 200
    pub_items = public_resp.json()
    assert any(x["id"] == ann_id for x in pub_items)

    # 5. Expire announcement
    exp_resp = verified_client.post(f"/admin/announcements/{ann_id}/expire")
    assert exp_resp.status_code == 200
    assert exp_resp.json()["status"] == "expired"

    # 6. Delete announcement
    del_resp = verified_client.delete(f"/admin/announcements/{ann_id}")
    assert del_resp.status_code == 200
