"""Independent regression expectations transcribed from the supplied PDF scans."""

from copy import deepcopy
from itertools import product

import pytest

from app.rules import evaluate_eligibility
from database.hus_db.catalog_builder import build_catalogs
from database.hus_db.prerequisites import parse_prerequisites


@pytest.mark.parametrize("raw,expected", [
    (None, []),
    ("MAT2300/\nMAT2320\nMAT2302", [["MAT2300", "MAT2320"], ["MAT2302"]]),
    ("MAT3374\nMAT3552E\nMAT1207", [["MAT3374"], ["MAT3552E"], ["MAT1207"]]),
    ("(MAT1202\nMAT3507)/\nMAT3304",
     [["MAT1202", "MAT3304"], ["MAT3304", "MAT3507"]]),
    ("MAT2301/\nMAT2321/\nMAT2400\nMAT2303/\nMAT2502",
     [["MAT2301", "MAT2321", "MAT2400"], ["MAT2303", "MAT2502"]]),
])
def test_pdf_notation_preserves_grouping(raw, expected):
    assert parse_prerequisites(raw) == expected


@pytest.mark.parametrize("raw", [
    "/MAT1202", "MAT1202/", "(MAT1202", "MAT1202)", "()",
    "MAT1202 AND MAT3507", "MAT1202//MAT3507", "MAT1202, MAT3507",
])
def test_unrecognized_notation_requires_review(raw):
    with pytest.raises(ValueError):
        parse_prerequisites(raw)


@pytest.mark.parametrize("a,b,c", list(product([False, True], repeat=3)))
def test_internship_condition_truth_table(a, b, c):
    parsed = parse_prerequisites("(MAT1202\nMAT3507)/\nMAT3304")
    passed = {code for code, present in zip(("MAT1202", "MAT3507", "MAT3304"), (a, b, c))
              if present}
    assert all(any(code in passed for code in clause) for clause in parsed) == ((a and b) or c)


@pytest.mark.parametrize("code,name,credits", [
    ("MAT2320", "Đại số tuyến tính 1", 5),
    ("MAT2321", "Đại số tuyến tính 2", 5),
    ("MAT2322", "Giải tích 3", 5),
    ("MAT2313", "Phương trình đạo hàm riêng 1", 4),
    ("MAT3340", "Giải tích hàm", 4),
])
def test_honors_references_do_not_become_major_memberships(source_bundle, source_catalogs,
                                                          code, name, credits):
    course, = [r for r in source_bundle["tables"]["courses"] if r["course_code"] == code]
    assert (course["course_name"], course["credits"]) == (name, credits)
    assert all(code not in {c.code for c in catalog.courses}
               for catalog in source_catalogs.values())
    assert len(source_catalogs) == 4


@pytest.mark.parametrize("program,passed,incomplete_passed", [
    ("toan_hoc_7460101_2022", {"MAT2301", "MAT2303"}, {"MAT2301"}),
    ("toan_hoc_7460101_2022", {"MAT2301", "MAT2303"}, {"MAT2303"}),
    ("toan_tin_7460117_2022", {"MAT2301", "MAT2303"}, {"MAT2301"}),
    ("toan_tin_7460117_2022", {"MAT2301", "MAT2303"}, {"MAT2303"}),
    ("khmtt_7480113qtd_2022", {"MAT2400", "MAT2502"}, {"MAT2400"}),
    ("khmtt_7480113qtd_2022", {"MAT2400", "MAT2502"}, {"MAT2502"}),
    ("khdl_7460108_2022", {"MAT2400", "MAT2502"}, {"MAT2400"}),
    ("khdl_7460108_2022", {"MAT2400", "MAT2502"}, {"MAT2502"}),
])
def test_optimization_unlocks_using_own_major_alternatives(
    source_catalogs, program, passed, incomplete_passed
):
    catalog = source_catalogs[program]
    assert "MAT2407" in {c.code for c in evaluate_eligibility(catalog, passed).eligible_courses}
    result = evaluate_eligibility(catalog, incomplete_passed)
    assert "MAT2407" not in {c.code for c in result.eligible_courses}
    with pytest.raises(ValueError, match="unknown_passed_course_codes"):
        evaluate_eligibility(catalog, {"MAT2321"})


@pytest.mark.parametrize("program,passed", [
    ("toan_hoc_7460101_2022", {"MAT3304"}),
    ("toan_tin_7460117_2022", {"MAT1202", "MAT3507"}),
])
def test_internship_unlocks_only_when_complete_branch_passed(source_catalogs, program, passed):
    catalog = source_catalogs[program]
    assert "MAT3359" in {c.code for c in evaluate_eligibility(catalog, passed).eligible_courses}
    assert "MAT3359" not in {c.code for c in evaluate_eligibility(catalog, set()).eligible_courses}


def test_history_retains_both_track_rules_and_stays_blocked(source_catalogs):
    catalog = source_catalogs["toan_hoc_7460101_2022"]
    course = next(c for c in catalog.courses if c.code == "MAT3325")
    assert course.prerequisite_status == "conflict"
    variants = {tuple(sorted(tuple(sorted(c)) for c in v)) for v in course.prerequisite_variants}
    assert variants == {
        (("MAT2304",), ("MAT2314",)),
        (("MAT2304", "MAT2322"), ("MAT2314",)),
    }
    assert {r["group_key"] for r in course.source_prerequisite_rules} == {"V.2.1", "V.2.2"}
    result = evaluate_eligibility(catalog, {c.code for c in catalog.courses} - {course.code})
    blocked = next(c for c in result.blocked_courses if c.code == course.code)
    assert any(r.kind == "source_conflict" for r in blocked.reasons)


def test_undefined_reference_remains_unknown_and_is_not_invented(source_bundle, source_catalogs):
    assert "MAT3402" not in {c["course_code"] for c in source_bundle["tables"]["courses"]}
    catalog = source_catalogs["toan_hoc_7460101_2022"]
    course = next(c for c in catalog.courses if c.code == "MAT3423")
    assert course.prerequisite_status == "unknown"
    assert "MAT3402" in course.prerequisites_raw


@pytest.mark.parametrize("major,code,page", [(2, "MAT3327", 11), (4, "MAT2034", 10)])
def test_source_page_corrections(source_bundle, major, code, page):
    entry, = [e for e in source_bundle["tables"]["official_curriculum_entries"]
              if e["curriculum_id"] == major and e["course_code"] == code]
    assert entry["pdf_page"] == page


def test_missing_normalized_relation_fails_before_publication(source_bundle):
    broken = deepcopy(source_bundle)
    broken["tables"]["course_prerequisites"] = [
        r for r in broken["tables"]["course_prerequisites"]
        if (r["curriculum_id"], r["course_code"], r["prerequisite_course_code"])
        != (1, "MAT2308", "MAT2320")
    ]
    with pytest.raises(ValueError, match="clauses do not match source"):
        build_catalogs(broken)
