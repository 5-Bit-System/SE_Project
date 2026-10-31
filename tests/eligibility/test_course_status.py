"""Source-ready board behavior using invented courses, never student records."""

import copy

import pytest

from app.academic_context import AcademicContextError
from app.models import Catalog, ChoiceGroup, Course, Program
from app.services.course_status_service import (
    course_board,
    course_board_display,
    reviewed_course_board,
    validate_plan_courses,
)


@pytest.fixture
def curriculum():
    return Catalog(program=Program(
        program_id="invented", name="Invented program", total_credits=15,
        catalog_status="verified",
        source_file="synthetic-only", source_pages="1",
        choice_groups=[ChoiceGroup(id="choice", name="Invented elective group", required_credits=3)],
    ), courses=[
        Course(code="A", name="Passed", credits=3, block="general", prerequisite_status="verified", source_status="verified"),
        Course(code="B", name="Next", credits=3, block="major", prerequisites=[["A"]], prerequisite_status="verified", source_status="verified"),
        Course(code="C", name="Later", credits=3, block="major", prerequisites=[["B"]], prerequisite_status="verified", source_status="verified"),
        Course(code="D", name="Unknown prerequisite", credits=3, block="major",
               prerequisite_status="unknown", source_status="verified"),
        Course(code="E1", name="Alternative 1", credits=3, block="elective",
               requirement_type="elective", choice_group_ids=["choice"], prerequisite_status="verified", source_status="verified"),
        Course(code="E2", name="Alternative 2", credits=3, block="elective",
               requirement_type="elective", choice_group_ids=["choice"], prerequisite_status="verified", source_status="verified"),
        Course(code="X", name="Excluded", credits=2, block="general",
               requirement_type="required_excluded", counted_in_total=False, prerequisite_status="verified", source_status="verified"),
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


def test_unverified_catalog_cannot_supply_a_course_plan(curriculum):
    curriculum.program.catalog_status = "draft_unverified"

    board = course_board(curriculum, context("A"))

    assert board["courses"]["eligible"] == []
    assert all(
        any(reason["kind"] == "catalog_unverified" for reason in row["reasons"])
        for row in board["courses"]["blocked"]
    )


def test_unready_context_cannot_be_treated_as_an_empty_completed_set(curriculum):
    with pytest.raises(AcademicContextError, match="academic_context_not_ready"):
        course_board(curriculum, {**context(), "status": "needs_policy_review"})


def pending_context(*, outside=False):
    return {
        "status": "needs_policy_review", "revision": "synthetic-review",
        "blocking_reasons": ["course_outcomes_unresolved"],
        "outcomes": [
            {"code": "A", "state": "completed"},
            {"code": "B", "state": "unresolved"},
            {"code": "E1", "state": "unresolved"},
            {"code": "X", "state": "unresolved"},
            *([{"code": "OUTSIDE", "state": "out_of_catalog"}] if outside else []),
        ],
    }


@pytest.mark.parametrize("exclusion", ["course", "program"])
def test_pending_no_prerequisite_and_excluded_courses_remain_available(curriculum, exclusion):
    excluded = next(course for course in curriculum.courses if course.code == "X")
    excluded.prerequisites = [["A"]]
    if exclusion == "program":
        excluded.counted_in_total = True
        curriculum.program.excluded_from_total = ["X"]
    pending = pending_context()
    before = copy.deepcopy(pending)
    board = reviewed_course_board(curriculum, pending, max_credits=5)
    available = {row["code"]: row for row in board["courses"]["eligible"]}
    assert set(available) == {"E1", "E2", "X"}
    assert available["E1"]["eligibility_basis"] == "no_prerequisites"
    assert available["X"]["eligibility_basis"] == "excluded_from_total"
    assert available["X"]["counted_in_total"] is False
    assert available["E1"]["result_pending"] is True
    assert available["E2"]["result_pending"] is False
    assert board["plan"]["course_codes"] == ["X", "E1"]
    assert board["plan"]["suggested_credits"] == 5
    assert [row["code"] for row in board["courses"]["completed"]] == ["A"]
    assert board["progress"]["total"]["earned_credits"] == 3
    blocked = {row["code"]: row for row in board["courses"]["blocked"]}
    assert blocked["B"]["reasons"][0]["kind"] == "academic_review_required"
    assert blocked["C"]["reasons"][0]["missing_prerequisites"] == [["B"]]
    assert blocked["D"]["reasons"][0]["kind"] == "prerequisite_unknown"
    assert pending == before


@pytest.mark.parametrize("gate", ["selection", "outside", "program"])
def test_defaults_stay_visible_but_global_gate_pauses_all_planning(curriculum, gate):
    if gate == "program":
        curriculum.program.planning_blockers = ["synthetic-rule-conflict"]
    board = reviewed_course_board(
        curriculum, pending_context(outside=gate == "outside"),
        selection_blockers=["graduation_selection_required"] if gate == "selection" else None,
    )
    assert {row["code"] for row in board["courses"]["eligible"]} == {"E1", "E2", "X"}
    assert board["can_plan"] is False
    assert board["plan"]["course_codes"] == []
    assert board["plan"]["suggested_credits"] == 0
    assert not any(row["suggested"] for row in board["courses"]["eligible"])


def test_default_never_bypasses_missing_prerequisites_or_completed_facts(curriculum):
    excluded = next(course for course in curriculum.courses if course.code == "X")
    excluded.prerequisites = [["B"]]
    board = reviewed_course_board(curriculum, pending_context())
    blocked = {row["code"]: row for row in board["courses"]["blocked"]}
    assert blocked["X"]["reasons"][0]["missing_prerequisites"] == [["B"]]
    assert "X" not in board["plan"]["course_codes"]
    ready = course_board(curriculum, context("A", "B", "X", "E1"))
    assert {row["code"] for row in ready["courses"]["completed"]} == {"A", "B", "X", "E1"}
    assert ready["progress"]["total"]["earned_credits"] == 9
    assert "E2" in {row["code"] for row in ready["courses"]["blocked"]}


def test_defaults_require_verified_collection_and_program_context(curriculum):
    with pytest.raises(AcademicContextError, match="academic_context_not_ready"):
        reviewed_course_board(curriculum, {
            **pending_context(), "blocking_reasons": ["source_incomplete"],
        })


@pytest.mark.parametrize("prerequisite, expected_state", [("A", "eligible"), ("B", "blocked")])
def test_explicit_internship_default_still_requires_completed_prerequisites(
        curriculum, prerequisite, expected_state):
    curriculum.courses.append(Course(
        code="MAT3374", name="Synthetic requested internship", credits=3, block="major",
        prerequisites=[[prerequisite]], prerequisite_status="verified", source_status="verified",
    ))
    pending = pending_context()
    pending["outcomes"].append({"code": "MAT3374", "state": "unresolved"})
    board = reviewed_course_board(curriculum, pending)
    row = next(row for row in board["courses"][expected_state] if row["code"] == "MAT3374")
    if expected_state == "eligible":
        assert row["eligibility_basis"] == "requested_default"
        assert row["result_pending"] is True
    else:
        assert row["reasons"][0]["missing_prerequisites"] == [["B"]]
    assert board["progress"]["total"]["earned_credits"] == 3


@pytest.mark.parametrize("state", ["completed", "eligible", "blocked"])
@pytest.mark.parametrize("exclusion", ["course", "program"])
def test_map_hides_excluded_courses_from_every_column(curriculum, state, exclusion):
    excluded = next(course for course in curriculum.courses if course.code == "X")
    if exclusion == "program":
        excluded.counted_in_total = True
        curriculum.program.excluded_from_total = ["X"]
    if state == "blocked":
        excluded.prerequisites = [["D"]]
    board = course_board(curriculum, context("A", *(["X"] if state == "completed" else [])))
    assert "X" in {row["code"] for row in board["courses"][state]}
    before = copy.deepcopy(board)
    view = course_board_display(board)
    assert all(row["counted_in_total"] and row["code"] != "X"
               for courses in view["courses"].values() for row in courses)
    assert "X" not in view["plan"]["course_codes"]
    assert view["progress"] == board["progress"]
    assert view["progress"]["total"]["earned_credits"] == 3
    assert board == before


def test_map_follows_available_prerequisite_chains_without_completing_or_planning_them(curriculum):
    curriculum.courses.append(Course(
        code="CHAIN", name="Synthetic follow-up", credits=3, block="major",
        prerequisites=[["C"]], prerequisite_status="verified", source_status="verified"))
    board = course_board(curriculum, context("A"))
    before = copy.deepcopy(board)
    view = course_board_display(board)
    available = {row["code"]: row for row in view["courses"]["eligible"]}
    assert {"B", "C", "CHAIN"} <= available.keys()
    assert available["C"]["eligibility_basis"] == "available_prerequisites"
    assert available["C"]["prerequisite_clauses"] == [["B"]]
    assert available["CHAIN"]["prerequisite_clauses"] == [["C"]]
    assert available["C"]["suggested"] is False
    assert [row["code"] for row in view["courses"]["completed"]] == ["A"]
    assert view["progress"]["total"]["earned_credits"] == 3
    assert view["plan"]["course_codes"] == ["B", "E1"]
    assert view["plan"]["suggested_credits"] == 6
    for candidate in (board, view):
        with pytest.raises(AcademicContextError, match="course_unavailable"):
            validate_plan_courses(candidate, ["B", "C"], 20)
    assert board == before
    assert course_board_display(view) == view


def test_map_requires_every_and_clause_but_accepts_either_or_alternative(curriculum):
    for code, prerequisites in (
        ("OR", [["D", "B"]]), ("AND", [["B"], ["D"]]),
        ("FOREIGN", [["OUTSIDE"]]), ("LOOP1", [["LOOP2"]]),
        ("LOOP2", [["LOOP1"]]), ("SELF", [["SELF"]]),
    ):
        curriculum.courses.append(Course(
            code=code, name=code, credits=3, block="major", prerequisites=prerequisites,
            prerequisite_status="verified", source_status="verified"))
    view = course_board_display(course_board(curriculum, context("A")))
    assert "OR" in {row["code"] for row in view["courses"]["eligible"]}
    assert {"AND", "FOREIGN", "LOOP1", "LOOP2", "SELF", "D"} <= {
        row["code"] for row in view["courses"]["blocked"]}


@pytest.mark.parametrize("blocker", ["source", "unknown", "conflict", "quota", "catalog"])
def test_map_does_not_override_other_blocking_rules(curriculum, blocker):
    dependent = next(course for course in curriculum.courses if course.code == "C")
    passed = ["A"]
    if blocker == "source":
        dependent.source_status = "draft_unverified"
    elif blocker in {"unknown", "conflict"}:
        dependent.prerequisite_status = blocker
    elif blocker == "quota":
        dependent.choice_group_ids = ["choice"]
        passed.append("E1")
    else:
        curriculum.program.catalog_status = "draft_unverified"
    view = course_board_display(course_board(curriculum, context(*passed)))
    assert "C" in {row["code"] for row in view["courses"]["blocked"]}


def test_map_hiding_excluded_default_does_not_seed_its_dependents(curriculum):
    curriculum.courses.append(Course(
        code="FOLLOWX", name="After excluded course", credits=3, block="major",
        prerequisites=[["X"]], prerequisite_status="verified", source_status="verified"))
    view = course_board_display(course_board(curriculum, context("A")))
    assert "FOLLOWX" in {row["code"] for row in view["courses"]["blocked"]}
    completed = course_board_display(course_board(curriculum, context("A", "X")))
    assert "FOLLOWX" in {row["code"] for row in completed["courses"]["eligible"]}


def test_map_pending_results_and_global_pause_remain_separate_from_reachability(curriculum):
    curriculum.courses.append(Course(
        code="FOLLOW", name="After available elective", credits=3, block="major",
        prerequisites=[["E1"]], prerequisite_status="verified", source_status="verified"))
    pending = pending_context()
    pending["outcomes"].append({"code": "FOLLOW", "state": "unresolved"})
    before = copy.deepcopy(pending)
    board = reviewed_course_board(curriculum, pending,
                                 selection_blockers=["graduation_selection_required"])
    view = course_board_display(board)
    available = {row["code"]: row for row in view["courses"]["eligible"]}
    assert available["FOLLOW"]["eligibility_basis"] == "available_prerequisites"
    assert available["FOLLOW"]["result_pending"] is True
    assert available["B"]["eligibility_basis"] == "completed_prerequisites"
    assert available["B"]["result_pending"] is True
    assert available["C"]["eligibility_basis"] == "available_prerequisites"
    assert view["can_plan"] is False
    assert view["plan"]["course_codes"] == []
    assert not any(row["suggested"] for row in available.values())
    assert pending == before


@pytest.mark.parametrize("gate", ["selection", "outside", "program", "metadata", "pending"])
def test_planning_review_never_shrinks_the_available_prerequisite_sequence(curriculum, gate):
    ready = course_board_display(course_board(curriculum, context("A")))
    pending = pending_context(outside=gate == "outside")
    if gate == "program":
        curriculum.program.planning_blockers = ["synthetic-rule-review"]
    elif gate == "metadata":
        curriculum.program.catalog_status = "draft_unverified"
        pending["blocking_reasons"].append("catalog_unverified")
    before = copy.deepcopy(pending)
    board = reviewed_course_board(curriculum, pending,
        selection_blockers=["graduation_selection_required"] if gate == "selection" else None)
    view = course_board_display(board)
    available = {row["code"]: row for row in view["courses"]["eligible"]}
    assert set(available) == {row["code"] for row in ready["courses"]["eligible"]}
    assert {"B", "C"} <= available.keys()
    assert available["B"]["eligibility_basis"] == "completed_prerequisites"
    assert available["B"]["planning_eligible"] is False
    assert available["C"]["prerequisite_clauses"] == [["B"]]
    assert available["C"]["planning_eligible"] is False
    assert {row["code"] for row in view["courses"]["blocked"]} == {"D"}
    assert view["courses"]["completed"] == ready["courses"]["completed"]
    assert view["progress"]["total"]["earned_credits"] == 3
    assert not {"B", "C", "X"} & set(view["plan"]["course_codes"])
    assert course_board_display(view) == view
    if gate == "pending":
        assert view["can_plan"] is True
        for code in ("B", "C"):
            with pytest.raises(AcademicContextError, match="course_unavailable"):
                validate_plan_courses(view, [code], 20)
    else:
        assert view["can_plan"] is False
        assert view["plan"]["course_codes"] == []
    assert pending == before
