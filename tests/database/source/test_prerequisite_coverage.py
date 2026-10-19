"""Compare normalized prerequisites to raw source cells, independently of the builder."""

import re
from collections import defaultdict

import pytest

from app.rules import evaluate_eligibility
from database.hus_db.catalog_builder import PROGRAM_IDS

MAJORS = sorted(PROGRAM_IDS)


@pytest.fixture(params=MAJORS, ids=[m[0] for m in MAJORS])
def prerequisite_major(request, source_bundle, source_catalogs):
    identity = request.param
    tables = source_bundle["tables"]
    curriculum, = [c for c in tables["curricula"]
                   if (c["major_code"], c["cohort_year"], c["curriculum_version"]) == identity]
    cid = curriculum["curriculum_id"]
    entries = [e for e in tables["official_curriculum_entries"] if e["curriculum_id"] == cid]
    clauses = defaultdict(lambda: defaultdict(set))
    for row in tables["course_prerequisites"]:
        if row["curriculum_id"] == cid:
            clauses[row["course_code"]][row["group_no"]].add(row["prerequisite_course_code"])
    return source_catalogs[PROGRAM_IDS[identity]], entries, clauses


def test_normalized_clauses_match_raw_cells_without_dropping_and_or(prerequisite_major):
    _, entries, clauses = prerequisite_major
    for entry in entries:
        if entry["prerequisite_parse_status"] != "normalized":
            continue
        if entry["course_code"] in {"MAT3359", "MAT3325"}:
            # Parenthesized and conflicting rules have dedicated PDF regression cases.
            continue
        raw = entry["prerequisite_source_text"].strip()
        # In the SQL transcription, '/' separates alternatives and a newline
        # separates required groups. A slash may wrap onto the next PDF line.
        unwrapped = re.sub(r"\s*/\s*", "/", raw)
        assert re.fullmatch(r"[A-Z]{3}\d{4}[A-Z]?(?:[/\s]+[A-Z]{3}\d{4}[A-Z]?)*", unwrapped)
        expected = {frozenset(group.split("/")) for group in unwrapped.split()}
        actual = {frozenset(refs) for refs in clauses[entry["course_code"]].values()}
        assert actual == expected, (entry["course_code"], raw, expected, actual)


def test_unresolved_conditions_block_even_after_all_other_courses_pass(prerequisite_major):
    catalog, entries, _ = prerequisite_major
    unresolved = {e["course_code"] for e in entries if e["prerequisite_parse_status"]
                  in {"unlisted_prerequisite", "complex_expression", "needs_review"}}
    unresolved |= {course.code for course in catalog.courses
                   if course.prerequisite_status == "conflict"}
    courses = {course.code: course for course in catalog.courses}
    for code in unresolved:
        status = courses[code].prerequisite_status
        assert status in {"unknown", "conflict"}
        result = evaluate_eligibility(catalog, set(courses) - {code})
        blocked = next(course for course in result.blocked_courses if course.code == code)
        reason_kind = "source_conflict" if status == "conflict" else "prerequisite_unknown"
        assert any(reason.kind == reason_kind for reason in blocked.reasons)
        assert code not in {course.code for course in result.eligible_courses}


def test_raw_unresolved_cells_and_parse_statuses_are_preserved(prerequisite_major):
    catalog, entries, _ = prerequisite_major
    courses = {course.code: course for course in catalog.courses}
    for entry in entries:
        if entry["prerequisite_parse_status"] not in {
            "unlisted_prerequisite", "complex_expression", "needs_review"
        }:
            continue
        course = courses[entry["course_code"]]
        assert entry in course.source_occurrences
        assert entry["prerequisite_source_text"] in course.prerequisites_raw
        assert entry["prerequisite_parse_status"] in course.source_prerequisite_parse_statuses
