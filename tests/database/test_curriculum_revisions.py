"""Database tests for versioned curriculum revisions and audit schema."""

import os
import uuid
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine

from app.curriculum.repository import (
    create_revision,
    get_active_revision,
    get_revision,
    list_reviews,
    publish_revision,
    review_revision,
    rollback_revision,
    update_validation,
)

pytestmark = pytest.mark.hus_postgres

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


@pytest.fixture
def db_conn():
    config = dotenv_values(ENV_PATH)
    url = os.environ.get("HUS_TEST_DATABASE_URL") or os.environ.get("DATABASE_URL") or config.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not found in environment or .env")
    engine = create_engine(url)
    with engine.begin() as conn:
        yield conn
    engine.dispose()


def test_create_curriculum_revision(db_conn):
    program_id = f"test_prog_{uuid.uuid4().hex[:6]}"
    revision = create_revision(
        db_conn,
        program_id=program_id,
        version_title="K2026 Chuẩn dự thảo",
        cohort="K2026",
        source_filename="k2026_test.csv",
        source_digest="abc123sha256fake",
        payload={"courses": [{"code": "MAT1001", "name": "Giải tích 1", "credits": 3}]},
        created_by=None,
    )

    assert revision["revision_id"] is not None
    assert revision["program_id"] == program_id
    assert revision["status"] == "draft"
    assert revision["is_active"] is False
    assert revision["payload"]["courses"][0]["code"] == "MAT1001"

    fetched = get_revision(db_conn, revision["revision_id"])
    assert fetched is not None
    assert fetched["revision_id"] == revision["revision_id"]


def test_status_transitions_and_review_audit(db_conn):
    program_id = f"test_prog_{uuid.uuid4().hex[:6]}"
    rev = create_revision(
        db_conn,
        program_id=program_id,
        version_title="K2026 v1",
        source_digest="digest_test_123",
        payload={"courses": []},
    )
    rev_id = rev["revision_id"]

    # 1. Update validation
    summary = {"errors": [], "warnings": ["Missing prereq for MAT1002"], "course_count": 10}
    validated = update_validation(db_conn, rev_id, status="validated", validation_summary=summary)
    assert validated["status"] == "validated"
    assert validated["validation_summary"]["course_count"] == 10

    # 2. Review and approve
    reviewed = review_revision(
        db_conn,
        rev_id,
        reviewer_id=None,
        decision="approved",
        reason="Đã đối chiếu với bản in gốc",
        notes="Cho phép xuất bản",
    )
    assert reviewed["status"] == "approved"
    assert reviewed["review_decision"] == "approved"

    # 3. Publish
    published = publish_revision(
        db_conn,
        rev_id,
        publisher_id=None,
        reason="Ban hành kỳ 1 năm học 2026-2027",
    )
    assert published["status"] == "published"
    assert published["is_active"] is True

    # Check active pointer
    active = get_active_revision(db_conn, program_id)
    assert active["revision_id"] == rev_id

    # Check review history audit
    reviews = list_reviews(db_conn, rev_id)
    actions = [r["action"] for r in reviews]
    assert "created" in actions
    assert "validated" in actions
    assert "approved" in actions
    assert "published" in actions


def test_only_one_active_revision_and_rollback(db_conn):
    program_id = f"test_prog_{uuid.uuid4().hex[:6]}"
    rev1 = create_revision(db_conn, program_id=program_id, version_title="v1", source_digest="d1", payload={"v": 1})
    rev2 = create_revision(db_conn, program_id=program_id, version_title="v2", source_digest="d2", payload={"v": 2})

    # Approve both
    review_revision(db_conn, rev1["revision_id"], reviewer_id=None, decision="approved", reason="OK v1")
    review_revision(db_conn, rev2["revision_id"], reviewer_id=None, decision="approved", reason="OK v2")

    # Publish v1
    publish_revision(db_conn, rev1["revision_id"], publisher_id=None, reason="Publish v1")
    assert get_active_revision(db_conn, program_id)["revision_id"] == rev1["revision_id"]

    # Publish v2 -> v1 is deactivated atomically
    publish_revision(db_conn, rev2["revision_id"], publisher_id=None, reason="Publish v2")
    assert get_active_revision(db_conn, program_id)["revision_id"] == rev2["revision_id"]

    v1_rechecked = get_revision(db_conn, rev1["revision_id"])
    assert v1_rechecked["is_active"] is False

    # Rollback to v1
    rollback_revision(db_conn, program_id, rev1["revision_id"], user_id=None, reason="Phát hiện lỗi ở v2")
    active_now = get_active_revision(db_conn, program_id)
    assert active_now["revision_id"] == rev1["revision_id"]
    assert active_now["is_active"] is True
