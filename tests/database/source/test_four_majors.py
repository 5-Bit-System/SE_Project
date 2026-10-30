"""Regression checks for the export, not acceptance against official PDFs."""

import pytest


@pytest.fixture(params=[
    ("toan_hoc_7460101_2022", "7460101", 90, 96, 135),
    ("toan_tin_7460117_2022", "7460117", 68, 69, 132),
    ("khmtt_7480113qtd_2022", "7480113QTD", 67, 67, 129),
    ("khdl_7460108_2022", "7460108", 65, 65, 127),
], ids=["mathematics", "math-informatics", "computer-science", "data-science"])
def major(request, source_bundle, source_catalogs):
    program_id, major_code, count, occurrences, credits = request.param
    tables = source_bundle["tables"]
    curriculum, = [c for c in tables["curricula"] if c["major_code"] == major_code]
    cid = curriculum["curriculum_id"]
    return (
        source_catalogs[program_id], curriculum,
        [m for m in tables["curriculum_courses"] if m["curriculum_id"] == cid],
        [e for e in tables["official_curriculum_entries"] if e["curriculum_id"] == cid],
        count, occurrences, credits,
    )


def test_major_coverage_and_credit_target(major):
    catalog, curriculum, memberships, entries, count, occurrences, credits = major
    codes = [m["course_code"] for m in memberships]
    assert len(codes) == len(set(codes)) == count
    assert len(entries) == occurrences
    assert {e["course_code"] for e in entries} == set(codes)
    assert {c.code for c in catalog.courses} == set(codes)
    assert catalog.program.total_credits == curriculum["credits_required"] == credits
    expected_status = (
        "verified" if catalog.program.program_id == "khmtt_7480113qtd_2022" else "draft_unverified"
    )
    assert catalog.program.catalog_status == expected_status


def test_all_source_occurrences_and_memberships_survive_conversion(major, source_bundle):
    catalog, _, memberships, entries, *_ = major
    originals = {c["course_code"]: c for c in source_bundle["tables"]["courses"]}
    member_by_code = {m["course_code"]: m for m in memberships}
    for course in catalog.courses:
        assert course.source_course == originals[course.code]
        assert course.source_membership == member_by_code[course.code]
        expected = [e for e in entries if e["course_code"] == course.code]
        assert sorted(course.source_occurrences, key=lambda e: e["entry_id"]) == sorted(
            expected, key=lambda e: e["entry_id"]
        )
        assert course.credits == originals[course.code]["credits"]
        assert course.name == originals[course.code]["course_name"]
        assert all(e["pdf_document"] and e["pdf_page"] > 0 for e in expected)


def test_prerequisites_preserve_clauses_and_external_references(major, source_bundle):
    catalog, curriculum, *_ = major
    codes = {c.code for c in catalog.courses}
    rows = [r for r in source_bundle["tables"]["course_prerequisites"]
            if r["curriculum_id"] == curriculum["curriculum_id"]]
    for course in catalog.courses:
        clauses = {}
        for row in rows:
            if row["course_code"] == course.code:
                clauses.setdefault(row["group_no"], set()).add(row["prerequisite_course_code"])
        assert course.prerequisites == [sorted(clauses[n]) for n in sorted(clauses)]
        refs = {ref for variant in [course.prerequisites, *course.prerequisite_variants]
                for clause in variant for ref in clause}
        assert course.external_prerequisite_codes == sorted(refs - codes)
        assert course.code not in refs


def test_language_choices_and_excluded_credits_for_each_major(major):
    catalog, *_ = major
    excluded = {"CME1000", "PES1000", "HUS1012"}
    assert {c.code for c in catalog.courses if not c.counted_in_total} == excluded
    language = next(g for g in catalog.program.choice_groups if g.id == "language")
    assert set(language.course_codes) == {f"FLF1{i}07" for i in range(1, 8)}
    assert language.required_credits == 5
    for group in catalog.program.choice_groups:
        assert set(group.course_codes) <= {c.code for c in catalog.courses}
