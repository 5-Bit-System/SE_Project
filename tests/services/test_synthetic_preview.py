"""Unit tests for synthetic recommendation preview service."""

import pytest

from app.catalog import list_catalogs
from app.services.synthetic_preview import (
    SyntheticPreviewRequest,
    run_synthetic_recommendation_preview,
)


def test_synthetic_preview_basic_flow():
    catalogs = list_catalogs()
    assert len(catalogs) > 0
    program_id = catalogs[0].program.program_id

    req = SyntheticPreviewRequest(
        program_id=program_id,
        passed_course_codes=[],
        max_credits=18,
    )
    result = run_synthetic_recommendation_preview(req)

    assert result["is_simulated"] is True
    assert "simulation_disclaimer" in result
    assert result["catalog"]["program_id"] == program_id
    assert "recommendations" in result
    assert "eligible_courses" in result
    assert "blocked_courses" in result
    assert result["total_eligible"] >= 1
    # Check that warning is present for draft_unverified catalog
    if result["catalog"]["status"] == "draft_unverified":
        assert result["catalog"]["is_unverified"] is True
        assert result["catalog"]["warning"] is not None


def test_synthetic_preview_prerequisite_unlocking():
    # Test that passing prerequisites properly unlocks downstream courses
    catalogs = list_catalogs()
    # Find a catalog with courses that have prerequisites
    cat = next((c for c in catalogs if any(len(crs.prerequisites) > 0 for crs in c.courses)), catalogs[0])
    target_course = next(crs for crs in cat.courses if len(crs.prerequisites) > 0)
    prereq_code = target_course.prerequisites[0][0]

    # 1. When prerequisite is NOT passed: target course should be blocked
    req_without = SyntheticPreviewRequest(
        program_id=cat.program.program_id,
        passed_course_codes=[],
        max_credits=20,
    )
    result_without = run_synthetic_recommendation_preview(req_without)
    blocked_codes = [c["code"] for c in result_without["blocked_courses"]]
    assert target_course.code in blocked_codes

    # Verify blocked course has explanation
    blocked_obj = next(c for c in result_without["blocked_courses"] if c["code"] == target_course.code)
    assert len(blocked_obj["reasons"]) > 0

    # 2. When prerequisite IS passed: target course should be eligible (or eligible if other prereqs met)
    req_with = SyntheticPreviewRequest(
        program_id=cat.program.program_id,
        passed_course_codes=[prereq_code],
        max_credits=20,
    )
    result_with = run_synthetic_recommendation_preview(req_with)
    # The prerequisite course itself should no longer be in eligible or recommended (already completed)
    eligible_codes = [c["code"] for c in result_with["eligible_courses"]]
    assert prereq_code not in eligible_codes


def test_synthetic_preview_rejection_of_student_identifiers():
    with pytest.raises(ValueError, match="Student identifiers are not permitted"):
        SyntheticPreviewRequest(
            program_id="test",
            passed_course_codes=[],
            student_id="23001939",  # Explicitly rejected
        )
