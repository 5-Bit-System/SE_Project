"""Tests ensuring no auto-approval heuristics exist in document seeding,

and verifying all approved documents in data/hus/document_reviews.json
have a verified genuine reviewer_id.
"""

import json
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.crawler.document_review_service import export_git_reviews_from_db
from tools.seed_real_crawled_documents import create_initial_git_reviews_if_empty


def _write_seed_document(docs_dir: Path) -> None:
    docs_dir.mkdir()
    (docs_dir / "curriculum.md").write_text(
        "---\ntitle: Curriculum\nurl: https://example.com/curriculum\n"
        "type: curriculum\n---\nCurriculum awaiting human review.",
        encoding="utf-8",
    )


@pytest.mark.parametrize("review_count", [1, 3, 29])
def test_initializer_preserves_small_existing_review_snapshots(tmp_path, review_count):
    docs_dir = tmp_path / "docs"
    _write_seed_document(docs_dir)
    reviews_file = tmp_path / "reviews.json"
    decisions = {
        f"doc_{index}": {
            "doc_id": f"doc_{index}",
            "review_status": "approved" if index % 2 == 0 else "rejected",
            "reviewer_id": "57e9a52b-7365-4fe2-b9ce-1320ef48dc02",
            "review_reason": "A genuine recorded decision",
            "reviewed_at": "2026-11-09T00:00:00+00:00",
        }
        for index in range(review_count)
    }
    original = (json.dumps(decisions, indent=4) + "\n").encode("utf-8")
    reviews_file.write_bytes(original)

    create_initial_git_reviews_if_empty(docs_dir, reviews_file)

    assert reviews_file.read_bytes() == original


def test_small_db_export_survives_initializer_without_losing_decisions(tmp_path):
    docs_dir = tmp_path / "docs"
    _write_seed_document(docs_dir)
    reviews_file = tmp_path / "reviews.json"
    conn = MagicMock()
    rows = [
        SimpleNamespace(_mapping={
            "id": f"doc_export_{index}",
            "url": f"https://example.com/approved-{index}",
            "content_hash": f"hash-{index}",
            "title": f"Reviewed curriculum {index}",
            "major": "computer_science",
            "doc_type": "curriculum",
            "review_status": "approved",
            "review_reason": "Verified source content",
            "reviewer_id": "57e9a52b-7365-4fe2-b9ce-1320ef48dc02",
            "reviewed_at": "2026-11-09T00:00:00+00:00",
            "metadata_json": {},
        })
        for index in range(3)
    ]
    conn.execute.return_value.fetchall.return_value = rows
    export_git_reviews_from_db(conn, file_path=reviews_file)
    exported_bytes = reviews_file.read_bytes()
    assert len(json.loads(exported_bytes)) == 3

    create_initial_git_reviews_if_empty(docs_dir, reviews_file)

    assert reviews_file.read_bytes() == exported_bytes
    assert all(
        decision["review_status"] == "approved"
        for decision in json.loads(reviews_file.read_text(encoding="utf-8")).values()
    )


@pytest.mark.parametrize("invalid_content", ["", " \n", '{"doc":', "[]", "null", '{"doc": 1}'])
def test_initializer_rejects_invalid_snapshot_without_overwriting(tmp_path, invalid_content):
    docs_dir = tmp_path / "docs"
    _write_seed_document(docs_dir)
    reviews_file = tmp_path / "reviews.json"
    original = invalid_content.encode("utf-8")
    reviews_file.write_bytes(original)

    with pytest.raises(ValueError, match="Invalid review snapshot"):
        create_initial_git_reviews_if_empty(docs_dir, reviews_file)

    assert reviews_file.read_bytes() == original


@pytest.mark.parametrize("existing_empty_object", [False, True])
def test_initializer_bootstraps_only_missing_or_empty_object(tmp_path, existing_empty_object):
    docs_dir = tmp_path / "docs"
    _write_seed_document(docs_dir)
    reviews_file = tmp_path / "reviews.json"
    if existing_empty_object:
        reviews_file.write_text("{}", encoding="utf-8")

    create_initial_git_reviews_if_empty(docs_dir, reviews_file)

    decisions = json.loads(reviews_file.read_text(encoding="utf-8"))
    assert len(decisions) == 1
    decision = next(iter(decisions.values()))
    assert decision["review_status"] == "pending"
    assert decision["reviewer_id"] is None
    assert decision["reviewed_at"] is None


def test_create_initial_git_reviews_never_auto_approves(tmp_path: Path):
    """create_initial_git_reviews_if_empty must never auto-approve documents based on

    keywords or doc_type. All non-duplicate documents must default to 'pending'
    with reviewer_id=None and reviewed_at=None.
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Official curriculum file with "chuẩn", "ctdt", "clc" keywords
    (docs_dir / "104.-KHMTTT-chuẩn-04.11.2023.docx.md").write_text(
        "---\ntitle: CTĐT Chuẩn KHMTTT 2023\nurl: http://mim.hus.vnu.edu.vn/vi/ctdt-chuan\ntype: curriculum\n---\n# CTĐT Chuẩn",
        encoding="utf-8",
    )

    # 2. Another curriculum document with "nganh-"
    (docs_dir / "nganh-khoa-hoc-may-tinh.md").write_text(
        "---\ntitle: Ngành KHMT\nurl: http://mim.hus.vnu.edu.vn/vi/nganh-khmt\ntype: curriculum\n---\n# Ngành KHMT",
        encoding="utf-8",
    )

    # 3. An administrative form
    (docs_dir / "bieu-mau-sinh-vien.md").write_text(
        "---\ntitle: Biểu mẫu sinh viên\nurl: http://mim.hus.vnu.edu.vn/vi/bieu-mau\ntype: form\n---\n# Biểu mẫu",
        encoding="utf-8",
    )

    # 4. Standard document
    (docs_dir / "thong-tin-chung.md").write_text(
        "---\ntitle: Thông tin chung\nurl: http://mim.hus.vnu.edu.vn/vi/thong-tin\ntype: general_info\n---\n# Nội dung chung gốc",
        encoding="utf-8",
    )

    # 5. Duplicate of document 4
    (docs_dir / "thong-tin-trung-lap.md").write_text(
        "---\ntitle: Thông tin trùng lặp\nurl: http://mim.hus.vnu.edu.vn/vi/thong-tin-2\ntype: general_info\n---\n# Nội dung chung gốc",
        encoding="utf-8",
    )

    reviews_file = tmp_path / "test_reviews.json"
    create_initial_git_reviews_if_empty(docs_dir, reviews_file)

    assert reviews_file.is_file(), "Reviews file must be created"
    reviews = json.loads(reviews_file.read_text(encoding="utf-8"))
    assert len(reviews) == 5, f"Expected 5 reviews, got {len(reviews)}"

    # CRITICAL CHECK: No review must EVER be auto-approved
    approved_reviews = [r for r in reviews.values() if r.get("review_status") == "approved"]
    assert len(approved_reviews) == 0, (
        f"Detected {len(approved_reviews)} auto-approved reviews! "
        "No document should be auto-approved without genuine admin review."
    )

    # Non-duplicate documents must all be pending
    pending_reviews = [r for r in reviews.values() if r.get("review_status") == "pending"]
    assert len(pending_reviews) == 4, f"Expected 4 pending reviews, got {len(pending_reviews)}"

    for r in pending_reviews:
        assert r["reviewer_id"] is None, "Pending review must have reviewer_id=None"
        assert r["reviewed_at"] is None, "Pending review must have reviewed_at=None"
        assert r["review_reason"] == "Chờ kiểm định thực tế bởi quản trị viên", (
            f"Expected standard pending reason, got: {r['review_reason']}"
        )

    # Duplicate document must be rejected due to duplication
    rejected_reviews = [r for r in reviews.values() if r.get("review_status") == "rejected"]
    assert len(rejected_reviews) == 1, f"Expected 1 rejected duplicate, got {len(rejected_reviews)}"
    assert "trùng khớp" in rejected_reviews[0]["review_reason"]


def test_document_reviews_json_has_no_orphan_approved_reviews():
    """Verify that data/hus/document_reviews.json contains ZERO orphan approvals.

    - Every 'approved' document MUST have a genuine, valid reviewer_id (UUID) and reviewed_at timestamp.
    - Every document with reviewer_id=null MUST have review_status='pending',
      review_reason='Chờ kiểm định thực tế bởi quản trị viên', and reviewed_at=null.
    """
    reviews_file = Path("data/hus/document_reviews.json")
    assert reviews_file.is_file(), f"Reviews file not found: {reviews_file}"

    reviews = json.loads(reviews_file.read_text(encoding="utf-8"))
    assert len(reviews) > 0, "Reviews file cannot be empty"

    orphan_approved = []
    orphan_non_pending = []
    valid_approved = []

    for doc_id, r in reviews.items():
        reviewer_id = r.get("reviewer_id")
        status = r.get("review_status")
        reviewed_at = r.get("reviewed_at")

        if reviewer_id is None:
            if status == "approved":
                orphan_approved.append(doc_id)
            if status != "pending":
                orphan_non_pending.append((doc_id, status))
        else:
            # Genuine review: verify valid UUID and valid reviewed_at
            assert uuid.UUID(str(reviewer_id)), f"Reviewer ID {reviewer_id} is not a valid UUID"
            assert reviewed_at is not None, f"Reviewed document {doc_id} missing reviewed_at"
            if status == "approved":
                valid_approved.append(doc_id)

    assert len(orphan_approved) == 0, (
        f"Found {len(orphan_approved)} orphan approved reviews in document_reviews.json: {orphan_approved[:5]}"
    )
    assert len(orphan_non_pending) == 0, (
        f"Found {len(orphan_non_pending)} records with reviewer_id=null that are not pending: {orphan_non_pending[:5]}"
    )

    # Verify that the 3 genuine admin-reviewed documents remain approved
    assert len(valid_approved) >= 3, (
        f"Expected at least 3 genuine admin approved reviews, found {len(valid_approved)}"
    )
