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
