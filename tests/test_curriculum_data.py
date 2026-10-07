import json
from pathlib import Path

import pytest

from app.catalog import load_catalog
from app.rules import eligible_courses
from tools.build_catalogs import build_courses, check_curriculum, prerequisite_clauses


ROOT = Path(__file__).resolve().parents[1] / "data" / "curricula"
EXPECTED = [
    ("toan_hoc_7460101_2022", 89, 1, 90, 135),
    ("toan_tin_7460117_2022", 63, 0, 68, 132),
    ("khmtt_7480113qtd_2022", 61, 0, 67, 129),
    ("khdl_7460108_2022", 59, 0, 65, 127),
]


@pytest.mark.parametrize("program_id,numbered,unnumbered,count,credits", EXPECTED)
def test_complete_source_table_and_generated_catalog(program_id, numbered, unnumbered, count, credits):
    directory = ROOT / program_id
    program = json.loads((directory / "curriculum.json").read_text(encoding="utf-8"))
    rows = json.loads((directory / "source_rows.json").read_text(encoding="utf-8"))
    courses = json.loads((directory / "courses.json").read_text(encoding="utf-8"))
    assert {row["source_row"] for row in rows if row["source_row"] is not None} == set(range(1, numbered + 1))
    assert sum(row["source_row"] is None for row in rows) == unnumbered
    assert len(courses) == count
    assert len({course["code"] for course in courses}) == count
    assert all("sources" not in course for course in courses)
    assert all("sources" not in course.model_dump() for course in load_catalog(program_id).courses)
    assert program["total_credits"] == credits
    assert program["digitization"]["status"] == "complete"
    assert build_courses(program, rows) == courses
    assert check_curriculum(program, rows, courses)["status"] == "passed"


def test_language_options_and_excluded_credits_are_preserved():
    for program_id, *_ in EXPECTED:
        catalog = load_catalog(program_id)
        language = next(group for group in catalog.program.choice_groups if group.id == "foreign_language_b1")
        assert len(language.course_codes) == 7
        assert language.required_credits == 5
        assert language.listed_credits == 35
        excluded = {course.code for course in catalog.courses if not course.counted_in_total}
        assert excluded == {"CME1000", "PES1000", "HUS1012"}


def test_same_code_keeps_different_program_memberships():
    math = next(course for course in load_catalog("toan_hoc_7460101_2022").courses if course.code == "MAT2505")
    cs = next(course for course in load_catalog("khmtt_7480113qtd_2022").courses if course.code == "MAT2505")
    assert math.block == "group" and math.choice_group_ids == ["programming"]
    assert cs.block == "discipline" and cs.choice_group_ids == []
    assert math.source_page == 10 and cs.source_page == 10


def test_duplicated_math_course_keeps_both_groups_and_source_rows():
    course = next(course for course in load_catalog("toan_hoc_7460101_2022").courses if course.code == "MAT3323")
    assert course.source_rows == [54, 62]
    assert course.choice_group_ids == ["theoretical_mathematics", "applied_mathematics"]


def test_parenthesized_and_or_prerequisites_preserve_meaning():
    clauses = prerequisite_clauses("(MAT3507\nMAT1202)/\nMAT3304")
    for passed, expected in [
        ({"MAT3507"}, False),
        ({"MAT1202"}, False),
        ({"MAT3507", "MAT1202"}, True),
        ({"MAT3304"}, True),
    ]:
        assert all(any(code in passed for code in group) for group in clauses) is expected


def test_source_conflict_is_preserved_and_not_recommended():
    catalog = load_catalog("toan_hoc_7460101_2022")
    history = next(course for course in catalog.courses if course.code == "MAT3325")
    assert history.source_rows == [56, 72]
    assert history.prerequisite_status == "source_conflict"
    assert len(history.prerequisite_variants) == 2
    assert history.code not in {course.code for course in eligible_courses(catalog, {"MAT2314", "MAT2304"}, 18)}


def test_source_anomalies_are_not_silently_corrected():
    ds = load_catalog("khdl_7460108_2022")
    assert ds.program.major_credit_structure["source_elective_credit_expression"] == "28/63"
    assert sum(group.listed_credits for group in ds.program.choice_groups if group.id not in {"foreign_language_b1", "field_electives"}) == 57
    assert next(course for course in ds.courses if course.code == "MAT3508").credits == 3
    tt = load_catalog("toan_tin_7460117_2022")
    thesis = next(course for course in tt.courses if course.code == "MAT4082")
    assert thesis.hours == {"lecture": 75, "practice": 62, "self_study": 275}
    math = load_catalog("toan_hoc_7460101_2022")
    assert next(course for course in math.courses if course.code == "MAT4070").source_rows == []
    rows = json.loads((ROOT / "toan_hoc_7460101_2022" / "source_rows.json").read_text(encoding="utf-8"))
    assert any(row["source_row"] is None and row["code"] == "MAT4070" for row in rows)


def test_incomplete_source_coverage_fails_validation():
    directory = ROOT / "khdl_7460108_2022"
    program = json.loads((directory / "curriculum.json").read_text(encoding="utf-8"))
    rows = json.loads((directory / "source_rows.json").read_text(encoding="utf-8"))
    courses = build_courses(program, rows)
    with pytest.raises(ValueError, match="source rows"):
        check_curriculum(program, [row for row in rows if row["source_row"] != 42], courses)
