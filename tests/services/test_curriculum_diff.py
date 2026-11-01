"""Unit tests for curriculum diff computation."""

import pytest
from app.curriculum.diff_service import compute_curriculum_diff


def test_compute_diff_added_removed_modified():
    base_courses = [
        {"code": "MAT1001", "name": "Giải tích 1", "credits": 3, "prerequisites": []},
        {"code": "MAT1002", "name": "Giải tích 2", "credits": 3, "prerequisites": ["MAT1001"]},
        {"code": "OLD9999", "name": "Môn cũ bỏ", "credits": 2, "prerequisites": []},
    ]

    target_courses = [
        {"code": "MAT1001", "name": "Giải tích 1", "credits": 4, "prerequisites": []},  # credits changed 3 -> 4
        {"code": "MAT1002", "name": "Giải tích 2 (Mới)", "credits": 3, "prerequisites": ["MAT1001"]},  # name changed
        {"code": "NEW1001", "name": "Môn mới thêm", "credits": 3, "prerequisites": ["MAT1001"]},  # added
    ]

    diff = compute_curriculum_diff(base_courses, target_courses)

    assert diff["summary"]["added_count"] == 1
    assert diff["summary"]["removed_count"] == 1
    assert diff["summary"]["modified_count"] == 2
    assert diff["summary"]["unchanged_count"] == 0

    assert diff["changes"]["added"][0]["code"] == "NEW1001"
    assert diff["changes"]["removed"][0]["code"] == "OLD9999"

    mod_codes = {m["code"]: m for m in diff["changes"]["modified"]}
    assert "MAT1001" in mod_codes
    assert any(c["field"] == "credits" and c["before"] == 3 and c["after"] == 4 for c in mod_codes["MAT1001"]["field_changes"])

    assert "MAT1002" in mod_codes
    assert any(c["field"] == "name" and c["before"] == "Giải tích 2" for c in mod_codes["MAT1002"]["field_changes"])
