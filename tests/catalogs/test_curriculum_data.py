import json

import pytest

from app.catalog import load_catalog as load_file_catalog
from app.rules import eligible_courses
from tests.support import hus_acceptance as hus
from tools.build_catalogs import build_courses, check_curriculum

pytestmark = pytest.mark.full_catalog_acceptance
EXPECTED = [
    ("toan_hoc_7460101_2022", 89, 1, 90, 135),
    ("toan_tin_7460117_2022", 63, 0, 68, 132),
    ("khmtt_7480113qtd_2022", 61, 0, 67, 129),
    ("khdl_7460108_2022", 59, 0, 65, 127),
]


def load_catalog(program_id, root):
    return hus.catalog(program_id) if hus.is_hus(root) else load_file_catalog(program_id, root)


@pytest.mark.parametrize("program_id,numbered,unnumbered,count,credits", EXPECTED)
def test_complete_source_table_and_generated_catalog(
    program_id, numbered, unnumbered, count, credits, full_catalog_root
):
    ROOT = full_catalog_root
    if hus.is_hus(ROOT):
        spec = hus.expectations(ROOT)["programs"][program_id]
        rows = hus.assert_inventory(ROOT, program_id)
        assert (numbered, unnumbered, count, credits) == (
            spec["last_numbered_row"], spec["unnumbered"], spec["courses"], spec["credits"]
        )
        assert {r["source_row_number"] for r in rows if r["source_row_number"] is not None} == set(range(1, numbered + 1))
        assert sum(r["source_row_number"] is None for r in rows) == unnumbered
        catalog = load_catalog(program_id, ROOT)
        assert len(catalog.courses) == count
        assert len({c.code for c in catalog.courses}) == count
        assert catalog.program.total_credits == credits
        expected_status = "verified" if program_id == "khmtt_7480113qtd_2022" else "draft_unverified"
        assert catalog.program.catalog_status == expected_status
        assert all("sources" not in c.model_dump() for c in catalog.courses)
        assert sum(len(c.source_occurrences) for c in catalog.courses) == len(rows)
        return
    directory = ROOT / program_id
    program = json.loads((directory / "curriculum.json").read_text(encoding="utf-8"))
    rows = json.loads((directory / "source_rows.json").read_text(encoding="utf-8"))
    document = json.loads((directory / "courses.json").read_text(encoding="utf-8"))
    courses = document["courses"] if isinstance(document, dict) else document
    assert {row["source_row"] for row in rows if row["source_row"] is not None} == set(
        range(1, numbered + 1)
    )
    assert sum(row["source_row"] is None for row in rows) == unnumbered
    assert len(courses) == count
    assert len({course["code"] for course in courses}) == count
    assert all("sources" not in course for course in courses)
    assert all(
        "sources" not in course.model_dump() for course in load_catalog(program_id, ROOT).courses
    )
    assert program["total_credits"] == credits
    assert program["digitization"]["status"] == "complete"
    from tools.build_catalogs import merge_source_fields

    generated = build_courses(program, rows)
    if isinstance(document, dict):
        assert merge_source_fields(document, generated).model_dump() == document
    else:
        assert generated == courses
    assert check_curriculum(program, rows, courses)["status"] == "passed"


def test_language_options_and_excluded_credits_are_preserved(full_catalog_root):
    ROOT = full_catalog_root
    for program_id, *_ in EXPECTED:
        catalog = load_catalog(program_id, ROOT)
        language = next(
            group for group in catalog.program.choice_groups
            if group.id == ("language" if hus.is_hus(ROOT) else "foreign_language_b1")
        )
        assert len(language.course_codes) == 7
        assert language.required_credits == 5
        assert sum(c.credits for c in catalog.courses if c.code in language.course_codes) == 35
        assert set(language.course_codes) == {f"FLF1{i}07" for i in range(1, 8)}
        excluded = {course.code for course in catalog.courses if not course.counted_in_total}
        assert excluded == {"CME1000", "PES1000", "HUS1012"}


def test_same_code_keeps_different_program_memberships(full_catalog_root):
    ROOT = full_catalog_root
    math = next(
        course
        for course in load_catalog("toan_hoc_7460101_2022", ROOT).courses
        if course.code == "MAT2505"
    )
    cs = next(
        course
        for course in load_catalog("khmtt_7480113qtd_2022", ROOT).courses
        if course.code == "MAT2505"
    )
    assert math.block == "group" and math.choice_group_ids == [
        "IV.2" if hus.is_hus(ROOT) else "programming"
    ]
    assert cs.block == "discipline" and cs.choice_group_ids == []
    assert math.source_page == 10 and cs.source_page == 10


def test_duplicated_math_course_keeps_both_groups_and_source_rows(full_catalog_root):
    ROOT = full_catalog_root
    course = next(
        course
        for course in load_catalog("toan_hoc_7460101_2022", ROOT).courses
        if course.code == "MAT3323"
    )
    assert course.source_rows == [54, 62]
    assert course.choice_group_ids == (
        ["V.2.1", "V.2.2"] if hus.is_hus(ROOT)
        else ["theoretical_mathematics", "applied_mathematics"]
    )


def test_source_conflict_is_preserved_and_not_recommended(full_catalog_root):
    ROOT = full_catalog_root
    catalog = load_catalog("toan_hoc_7460101_2022", ROOT)
    history = next(course for course in catalog.courses if course.code == "MAT3325")
    assert history.source_rows == [56, 72]
    assert history.prerequisite_status in {"source_conflict", "conflict"}
    assert len(history.prerequisite_variants) == 2
    assert history.code not in {
        course.code for course in eligible_courses(catalog, {"MAT2314", "MAT2304"}, 18)
    }
    if hus.is_hus(ROOT):
        unknown = next(c for c in catalog.courses if c.code == "MAT3423")
        assert unknown.prerequisite_status == "unknown"
        assert "MAT3402" in unknown.prerequisites_raw
        assert unknown.code not in {c.code for c in eligible_courses(catalog, {"MAT2314"}, 18)}
        phi = next(c for c in catalog.courses if c.code == "PHI1002")
        assert phi.prerequisites == [["PHI1006"]]


def test_source_anomalies_are_not_silently_corrected(full_catalog_root):
    ROOT = full_catalog_root
    ds = load_catalog("khdl_7460108_2022", ROOT)
    if hus.is_hus(ROOT):
        groups = {g["group_key"]: g for g in ds.program.source_group_rules}
        assert groups["V.2"]["group_note"].startswith("28/63")
        assert groups["V.2"]["min_credits_if_selected"] == 28
        assert groups["V.2"]["offered_credits"] == 63
        assert sum(g["offered_credits"] for k, g in groups.items() if k.startswith("V.2.")) == 57
        assert groups["V.2.4"]["source_heading"] == "V.2.3"
        assert next(c for c in ds.courses if c.code == "MAT3508").credits == 3
        tt = load_catalog("toan_tin_7460117_2022", ROOT)
        assert next(c for c in tt.courses if c.code == "MAT4082").hours == {
            "lecture": 75, "practice": 62, "self_study": 275
        }
        math = load_catalog("toan_hoc_7460101_2022", ROOT)
        thesis = next(c for c in math.courses if c.code == "MAT4070")
        assert thesis.source_rows == []
        assert thesis.source_occurrences[0]["source_row_number"] is None
        assert thesis.source_page == 14
        return
    assert ds.program.major_credit_structure["source_elective_credit_expression"] == "28/63"
    assert (
        sum(
            group.listed_credits
            for group in ds.program.choice_groups
            if group.id not in {"foreign_language_b1", "field_electives"}
        )
        == 57
    )
    assert next(course for course in ds.courses if course.code == "MAT3508").credits == 3
    tt = load_catalog("toan_tin_7460117_2022", ROOT)
    thesis = next(course for course in tt.courses if course.code == "MAT4082")
    assert thesis.hours == {"lecture": 75, "practice": 62, "self_study": 275}
    math = load_catalog("toan_hoc_7460101_2022", ROOT)
    assert next(course for course in math.courses if course.code == "MAT4070").source_rows == []
    rows = json.loads(
        (ROOT / "toan_hoc_7460101_2022" / "source_rows.json").read_text(encoding="utf-8")
    )
    assert any(row["source_row"] is None and row["code"] == "MAT4070" for row in rows)


def test_incomplete_source_coverage_fails_validation(full_catalog_root):
    ROOT = full_catalog_root
    if hus.is_hus(ROOT):
        bundle = hus.source_bundle()
        curriculum = next(c for c in bundle["tables"]["curricula"] if c["curriculum_version"] == "QD3569-2023")
        bundle["tables"]["official_curriculum_entries"] = [
            e for e in bundle["tables"]["official_curriculum_entries"]
            if not (e["curriculum_id"] == curriculum["curriculum_id"] and e["source_row_number"] == 42)
        ]
        with pytest.raises(AssertionError, match="missing"):
            hus.assert_inventory(ROOT, "khdl_7460108_2022", bundle)
        from database.hus_db.catalog_builder import build_catalogs

        with pytest.raises(ValueError, match="source occurrence"):
            build_catalogs(bundle)
        return
    directory = ROOT / "khdl_7460108_2022"
    program = json.loads((directory / "curriculum.json").read_text(encoding="utf-8"))
    rows = json.loads((directory / "source_rows.json").read_text(encoding="utf-8"))
    courses = build_courses(program, rows)
    with pytest.raises(ValueError, match="source rows"):
        check_curriculum(program, [row for row in rows if row["source_row"] != 42], courses)
