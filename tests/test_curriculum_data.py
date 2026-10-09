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
MATH_REVIEW = json.loads((Path(__file__).parent / "fixtures" / "math_p1_review.json").read_text(encoding="utf-8"))
REVIEWED_MATH_ROWS = [dict(zip(MATH_REVIEW["fields"], values)) for values in MATH_REVIEW["reviewed_rows"]]


@pytest.fixture(scope="module")
def math_source_rows():
    return json.loads((ROOT / "toan_hoc_7460101_2022" / "source_rows.json").read_text(encoding="utf-8"))


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


@pytest.mark.parametrize(
    "reviewed",
    REVIEWED_MATH_ROWS,
    ids=[f"row-{row['source_row']}-{row['code']}" for row in REVIEWED_MATH_ROWS],
)
def test_math_source_row_matches_visually_reviewed_pdf_baseline(math_source_rows, reviewed):
    matching = [row for row in math_source_rows if (row["source_row"], row["code"]) == (reviewed["source_row"], reviewed["code"])]
    assert len(matching) == 1
    assert {field: matching[0][field] for field in MATH_REVIEW["fields"]} == reviewed


def test_math_review_covers_entire_assigned_scope_and_correct_source(math_source_rows):
    program = load_catalog("toan_hoc_7460101_2022").program
    assert program.source_file == MATH_REVIEW["source_file"]
    assert program.source_sha256 == MATH_REVIEW["source_sha256"]
    assert len(REVIEWED_MATH_ROWS) == 62
    assert {row["source_row"] for row in REVIEWED_MATH_ROWS if row["source_row"] is not None} == set(range(1, 56))
    assert [row["code"] for row in REVIEWED_MATH_ROWS if row["source_row"] is None] == ["MAT4070"]
    actual = {
        (row["source_row"], row["code"])
        for row in math_source_rows
        if (row["source_row"] is not None and 1 <= row["source_row"] <= 55)
        or (row["source_row"] is None and row["code"] == "MAT4070")
    }
    assert actual == {(row["source_row"], row["code"]) for row in REVIEWED_MATH_ROWS}


def test_math_b1_row_keeps_all_seven_reviewed_options(math_source_rows):
    options = [row for row in math_source_rows if row["source_row"] == 8]
    assert {row["code"] for row in options} == {"FLF1107", "FLF1207", "FLF1307", "FLF1407", "FLF1507", "FLF1607", "FLF1707"}
    assert all(row["source_page"] == 8 and row["credits"] == 5 for row in options)
    assert all(row["hours"] == {"lecture": 25, "practice": 50, "self_study": 175} for row in options)
    group = next(group for group in load_catalog("toan_hoc_7460101_2022").program.choice_groups if group.id == "foreign_language_b1")
    assert group.source_credit_expression == "5/35"


def test_math_blank_hours_and_unnumbered_thesis_are_not_inferred(math_source_rows):
    assert next(row for row in math_source_rows if row["code"] == "CME1000")["hours"] is None
    assert next(row for row in math_source_rows if row["code"] == "PES1000")["hours"] is None
    thesis = next(course for course in load_catalog("toan_hoc_7460101_2022").courses if course.code == "MAT4070")
    assert thesis.source_rows == [] and thesis.source_page == 14
    assert thesis.credits == 7 and thesis.hours == {"lecture": 75, "practice": 60, "self_study": 215}
    assert thesis.prerequisites == []
    assert thesis.graduation_path_ids == ["thesis"]


def test_math_complex_analysis_code_and_external_reference_are_not_guessed():
    catalog = load_catalog("toan_hoc_7460101_2022")
    assert "MAT3344" in {course.code for course in catalog.courses}
    assert "MAT3340" not in {course.code for course in catalog.courses}
    equation = next(course for course in catalog.courses if course.code == "MAT3317")
    assert equation.prerequisites_raw == "MAT3301/\nMAT3340\nMAT3307"
    assert equation.external_prerequisite_codes == ["MAT3340"]


@pytest.mark.parametrize(
    "passed,expected",
    [({"MAT1202"}, False), ({"MAT3507"}, False), ({"MAT1202", "MAT3507"}, True), ({"MAT3304"}, True), (set(), False)],
)
def test_reviewed_math_internship_parentheses_keep_source_meaning(passed, expected):
    course = next(course for course in load_catalog("toan_hoc_7460101_2022").courses if course.code == "MAT3359")
    assert course.prerequisites_raw == "(MAT1202\nMAT3507)/\nMAT3304"
    assert all(any(code in passed for code in clause) for clause in course.prerequisites) is expected


@pytest.mark.parametrize("program_id", [program_id for program_id, *_ in EXPECTED])
def test_all_programs_keep_pending_review_and_declared_external_references(program_id):
    catalog = load_catalog(program_id)
    assert catalog.program.catalog_status == "draft_unverified"
    assert catalog.program.digitization["review_status"] == "pending_peer_review"
    issues = {code for issue in catalog.program.source_issues if issue["kind"] == "external_reference" for code in issue["referenced_codes"]}
    references = {code for course in catalog.courses for code in course.external_prerequisite_codes}
    assert references == issues
