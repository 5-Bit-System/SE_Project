"""Source-ready board behavior using invented courses, never student records."""

import pytest

from app.academic_context import AcademicContextError
from app.models import Catalog, ChoiceGroup, Course, Program
from app.services.course_status_service import course_board


@pytest.fixture
def curriculum():
    return Catalog(program=Program(
        program_id="invented", name="Invented program", total_credits=15,
        source_file="synthetic-only", source_pages="1",
        choice_groups=[ChoiceGroup(id="choice", name="Invented elective group", required_credits=3)],
    ), courses=[
        Course(code="A", name="Passed", credits=3, block="general"),
        Course(code="B", name="Next", credits=3, block="major", prerequisites=[["A"]]),
        Course(code="C", name="Later", credits=3, block="major", prerequisites=[["B"]]),
        Course(code="D", name="Unknown prerequisite", credits=3, block="major",
               prerequisite_status="unknown"),
        Course(code="E1", name="Alternative 1", credits=3, block="elective",
               requirement_type="elective", choice_group_ids=["choice"]),
        Course(code="E2", name="Alternative 2", credits=3, block="elective",
               requirement_type="elective", choice_group_ids=["choice"]),
        Course(code="X", name="Excluded", credits=2, block="general",
               requirement_type="required_excluded", counted_in_total=False),
    ])


def context(*passed):
    return {"status": "ready", "revision": "synthetic-only", "completed_course_codes": list(passed)}


def test_bundle_consumes_group_quota_without_unlocking_future_prerequisites(curriculum):
    board = course_board(curriculum, context("A"))
    assert [row["code"] for row in board["courses"]["completed"]] == ["A"]
    assert {row["code"] for row in board["courses"]["eligible"]} == {"B", "E1", "E2", "X"}
    assert {row["code"] for row in board["courses"]["blocked"]} == {"C", "D"}
    assert board["plan"]["course_codes"] == ["B", "X", "E1"]
    assert board["plan"]["suggested_credits"] == 8
    reasons = {row["code"]: row["reasons"] for row in board["courses"]["blocked"]}
    assert reasons["C"][0]["missing_prerequisites"] == [["B"]]
    assert reasons["D"][0]["kind"] == "prerequisite_unknown"


def test_semester_budget_only_changes_plan_and_excluded_credits_stay_excluded(curriculum):
    low = course_board(curriculum, context("A", "X"), max_credits=2)
    high = course_board(curriculum, context("A", "X"), max_credits=20)
    for key in ("completed", "eligible", "blocked"):
        assert [row["code"] for row in low["courses"][key]] == [
            row["code"] for row in high["courses"][key]]
    assert low["plan"]["suggested_credits"] == 0
    assert low["progress"]["total"]["earned_credits"] == 3
    assert low["progress"]["total"]["remaining_credits"] == 12


def test_fulfilled_elective_group_is_red_with_explicit_reason(curriculum):
    board = course_board(curriculum, context("A", "E1"))
    alternative = next(row for row in board["courses"]["blocked"] if row["code"] == "E2")
    assert alternative["reasons"][0]["kind"] == "choice_group_full"
    assert "E2" not in board["plan"]["course_codes"]


def test_unready_context_cannot_be_treated_as_an_empty_completed_set(curriculum):
    with pytest.raises(AcademicContextError, match="academic_context_not_ready"):
        course_board(curriculum, {**context(), "status": "needs_policy_review"})
