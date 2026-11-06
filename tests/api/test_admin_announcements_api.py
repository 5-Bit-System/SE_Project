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


def test_academic_announcements_audience_policy(verified_client, fake_accounts):
    """Enforce audience scoping: public only gets 'all', authenticated gets role matching."""
    # Use admin session to publish 3 announcements with different audiences
    for session in fake_accounts.sessions.values():
        session["role"] = "admin"

    now = datetime.now(timezone.utc)
    future = now + timedelta(days=30)

    # Create & publish public 'all' announcement
    r_all = verified_client.post(
        "/admin/announcements",
        json={
            "title": "Thông báo chung cho toàn trường",
            "content": "Nội dung chung",
            "source_url": "https://hus.vnu.edu.vn/tb-chung.html",
            "audience": "all",
            "effective_date": now.isoformat(),
            "expiry_date": future.isoformat(),
        },
    )
    all_id = r_all.json()["id"]
    verified_client.post(f"/admin/announcements/{all_id}/publish")

    # Create & publish 'students' announcement
    r_stu = verified_client.post(
        "/admin/announcements",
        json={
            "title": "Thông báo sinh viên học bổng",
            "content": "Nội dung học bổng sinh viên",
            "source_url": "https://hus.vnu.edu.vn/tb-sinh-vien.html",
            "audience": "students",
            "effective_date": now.isoformat(),
            "expiry_date": future.isoformat(),
        },
    )
    stu_id = r_stu.json()["id"]
    verified_client.post(f"/admin/announcements/{stu_id}/publish")

    # Create & publish 'faculty' announcement
    r_fac = verified_client.post(
        "/admin/announcements",
        json={
            "title": "Thông báo giảng viên hội đồng khoa học",
            "content": "Nội dung giảng viên",
            "source_url": "https://hus.vnu.edu.vn/tb-giang-vien.html",
            "audience": "faculty",
            "effective_date": now.isoformat(),
            "expiry_date": future.isoformat(),
        },
    )
    fac_id = r_fac.json()["id"]
    verified_client.post(f"/admin/announcements/{fac_id}/publish")

    # A. Anonymous requests
    with TestClient(app, base_url="http://127.0.0.1:8000") as anon_client:
        anon_client.headers["origin"] = "http://127.0.0.1:8000"

        # 1. Anonymous with no param or audience=all gets ONLY audience='all'
        resp_anon = anon_client.get("/academic/announcements")
        assert resp_anon.status_code == 200
        items = resp_anon.json()
        assert any(x["id"] == all_id for x in items)
        assert not any(x["id"] == stu_id for x in items)
        assert not any(x["id"] == fac_id for x in items)

        resp_anon_all = anon_client.get("/academic/announcements?audience=all")
        assert resp_anon_all.status_code == 200
        items_all = resp_anon_all.json()
        assert any(x["id"] == all_id for x in items_all)
        assert not any(x["id"] == stu_id for x in items_all)
        assert not any(x["id"] == fac_id for x in items_all)

        # 2. Anonymous requesting audience=students is rejected with 401
        resp_anon_stu = anon_client.get("/academic/announcements?audience=students")
        assert resp_anon_stu.status_code == 401

        # 3. Anonymous requesting audience=faculty is rejected with 401
        resp_anon_fac = anon_client.get("/academic/announcements?audience=faculty")
        assert resp_anon_fac.status_code == 401

        # 4. Anonymous requesting invalid audience is rejected with 400
        resp_anon_inv = anon_client.get("/academic/announcements?audience=secret_vip")
        assert resp_anon_inv.status_code == 400

    # B. Authenticated student requests
    for session in fake_accounts.sessions.values():
        session["role"] = "student"

    # 1. Student requesting audience=students gets student + all
    resp_stu = verified_client.get("/academic/announcements?audience=students")
    assert resp_stu.status_code == 200
    items_stu = resp_stu.json()
    assert any(x["id"] == all_id for x in items_stu)
    assert any(x["id"] == stu_id for x in items_stu)
    assert not any(x["id"] == fac_id for x in items_stu)

    # 2. Student requesting audience=all gets only all
    resp_stu_all = verified_client.get("/academic/announcements?audience=all")
    assert resp_stu_all.status_code == 200
    items_stu_all = resp_stu_all.json()
    assert any(x["id"] == all_id for x in items_stu_all)
    assert not any(x["id"] == stu_id for x in items_stu_all)
    assert not any(x["id"] == fac_id for x in items_stu_all)

    # 3. Student requesting audience=faculty is forbidden with 403
    resp_stu_fac = verified_client.get("/academic/announcements?audience=faculty")
    assert resp_stu_fac.status_code == 403

    # 4. Student requesting invalid audience is rejected with 400
    resp_stu_inv = verified_client.get("/academic/announcements?audience=invalid_aud")
    assert resp_stu_inv.status_code == 400
