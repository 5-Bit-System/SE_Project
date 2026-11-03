"""Unit tests for academic announcements repository and service."""

from datetime import datetime, timedelta, timezone

import pytest

from app.announcements.service import (
    create_announcement,
    delete_announcement,
    expire_announcement,
    get_announcement,
    get_public_announcements,
    publish_announcement,
)


def test_announcement_lifecycle():
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=30)

    # 1. Create Draft
    ann = create_announcement(
        title="Thông báo đăng ký học phần Học kỳ 1 2026-2027",
        content="Sinh viên đăng ký các học phần theo đúng khung CTĐT.",
        source_url="https://hus.vnu.edu.vn/dao-tao/thong-bao-dang-ky.html",
        audience="students",
        effective_date=now.isoformat(),
        expiry_date=future.isoformat(),
        created_by="admin",
    )
    assert ann["id"] is not None
    assert ann["status"] == "draft"
    assert ann["source_url"].startswith("https://hus.vnu.edu.vn")

    # 2. Public view must NOT show draft
    public_before = get_public_announcements(audience="students")
    assert not any(a["id"] == ann["id"] for a in public_before)

    # 3. Publish announcement
    published = publish_announcement(ann["id"], actor_id="admin")
    assert published["status"] == "published"
    assert published["published_at"] is not None

    # 4. Public view must now show the published announcement
    public_after = get_public_announcements(audience="students")
    assert any(a["id"] == ann["id"] for a in public_after)

    # 5. Expire announcement
    expired = expire_announcement(ann["id"], actor_id="admin")
    assert expired["status"] == "expired"

    # 6. Public view must NOT show expired announcement
    public_expired = get_public_announcements(audience="students")
    assert not any(a["id"] == ann["id"] for a in public_expired)

    # 7. Delete announcement
    deleted = delete_announcement(ann["id"])
    assert deleted is True
    assert get_announcement(ann["id"]) is None


def test_announcement_validation_rules():
    now = datetime.now(timezone.utc)
    past = now - timedelta(days=1)

    # Missing/invalid source URL rejected
    with pytest.raises(ValueError, match="source_url"):
        create_announcement(
            title="Thông báo không nguồn",
            content="Nội dung",
            source_url="ftp://invalid-source",
            audience="all",
            effective_date=now.isoformat(),
            created_by="admin",
        )

    # Expiry before effective date rejected
    with pytest.raises(ValueError, match="expiry_date"):
        create_announcement(
            title="Thời gian không hợp lệ",
            content="Nội dung",
            source_url="https://hus.vnu.edu.vn/doc.pdf",
            audience="all",
            effective_date=now.isoformat(),
            expiry_date=past.isoformat(),
            created_by="admin",
        )



def test_announcement_audit_failure_rolls_back_mutation(monkeypatch):
    import app.announcements.service as ann_svc

    # Normal create first to have a valid baseline record
    now = datetime.now(timezone.utc)
    future = now + timedelta(days=30)

    base_ann = ann_svc.create_announcement(
        title="Thông báo chuẩn bị kiểm tra audit",
        content="Nội dung kiểm tra",
        source_url="https://hus.vnu.edu.vn/tb-audit.html",
        audience="students",
        effective_date=now.isoformat(),
        expiry_date=future.isoformat(),
        created_by="admin",
    )
    base_id = base_ann["id"]
    assert ann_svc.get_announcement(base_id)["status"] == "draft"

    # Now simulate audit failure
    def failing_audit(*args, **kwargs):
        raise RuntimeError("Simulated audit disk failure")

    monkeypatch.setattr(ann_svc, "log_admin_action", failing_audit)

    # 1. Audit failure during create must fail and rollback creation
    with pytest.raises(RuntimeError, match="Simulated audit disk failure"):
        ann_svc.create_announcement(
            title="Thông báo không thể ghi log kiểm toán",
            content="Nội dung sẽ bị hoàn tác",
            source_url="https://hus.vnu.edu.vn/tb-audit-fail.html",
            audience="students",
            effective_date=now.isoformat(),
            expiry_date=future.isoformat(),
            created_by="admin",
        )

    # 2. Audit failure during publish must fail and retain draft status
    with pytest.raises(RuntimeError, match="Simulated audit disk failure"):
        ann_svc.publish_announcement(base_id, actor_id="admin")
    assert ann_svc.get_announcement(base_id)["status"] == "draft"

    # Unpatch audit temporarily to publish legitimately
    monkeypatch.undo()
    ann_svc.publish_announcement(base_id, actor_id="admin")
    assert ann_svc.get_announcement(base_id)["status"] == "published"

    # Re-apply failing audit
    monkeypatch.setattr(ann_svc, "log_admin_action", failing_audit)

    # 3. Audit failure during expire must fail and retain published status
    with pytest.raises(RuntimeError, match="Simulated audit disk failure"):
        ann_svc.expire_announcement(base_id, actor_id="admin")
    assert ann_svc.get_announcement(base_id)["status"] == "published"

    # 4. Audit failure during delete must fail and retain record
    with pytest.raises(RuntimeError, match="Simulated audit disk failure"):
        ann_svc.delete_announcement(base_id, actor_id="admin")
    assert ann_svc.get_announcement(base_id) is not None


def test_audit_redaction_and_attribution():
    from app.audit.service import log_admin_action, redact_sensitive_payload

    # Sensitive patterns are redacted
    payload = {
        "title": "Học phí",
        "secret_token": "super-secret-token",
        "password": "plain-password",
        "cookie": "session=abc",
        "nested": {"access_token": "jwt.token.here", "normal": "safe_value"},
    }
    redacted = redact_sensitive_payload(payload)
    assert redacted["secret_token"] == "[REDACTED]"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["cookie"] == "[REDACTED]"
    assert redacted["nested"]["access_token"] == "[REDACTED]"
    assert redacted["nested"]["normal"] == "safe_value"
    assert redacted["title"] == "Học phí"

    # log_admin_action records attribution
    entry = log_admin_action(
        conn=None,
        actor_id="admin-user-uuid",
        actor_email="admin@hus.edu.vn",
        action="admin:announcement:create",
        target_type="announcement",
        target_id="ann-1234",
        details=payload,
    )
    assert entry["actor_id"] == "admin-user-uuid"
    assert entry["actor_email"] == "admin@hus.edu.vn"
    assert entry["action"] == "admin:announcement:create"
    assert entry["target_type"] == "announcement"
    assert entry["target_id"] == "ann-1234"
    assert entry["details"]["password"] == "[REDACTED]"
