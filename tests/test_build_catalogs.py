from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

from tools import build_catalogs
from tools.build_catalogs import build_courses, check_curriculum


ROOT = Path(__file__).resolve().parents[1] / "data" / "curricula"


@pytest.fixture
def curriculum():
    directory = ROOT / "toan_hoc_7460101_2022"
    return tuple(
        json.loads((directory / filename).read_text(encoding="utf-8"))
        for filename in ("curriculum.json", "source_rows.json", "courses.json")
    )


def test_duplicate_catalog_code_cannot_hide_behind_record_count(curriculum):
    program, rows, courses = curriculum
    courses[-1] = deepcopy(courses[0])
    with pytest.raises(ValueError, match=f"Duplicate code.*{courses[0]['code']}"):
        check_curriculum(program, rows, courses)


def test_catalog_code_coverage_is_checked_even_when_count_matches(curriculum):
    program, rows, courses = curriculum
    courses[-1]["code"] = "MAT9999"
    with pytest.raises(ValueError, match="course coverage mismatch.*MAT9999"):
        check_curriculum(program, rows, courses)


def test_repeated_source_entry_cannot_replace_another_b1_option(curriculum):
    program, rows, courses = curriculum
    options = [row for row in rows if row["source_row"] == 8]
    rows[rows.index(options[1])] = deepcopy(options[0])
    with pytest.raises(ValueError, match="Duplicate source entry.*FLF1107.*source_row=8"):
        check_curriculum(program, rows, courses)
    with pytest.raises(ValueError, match="Duplicate source entry"):
        build_courses(program, rows)


def test_missing_b1_option_is_detected_even_with_same_stt_coverage(curriculum):
    program, rows, courses = curriculum
    rows[:] = [row for row in rows if row["code"] != "FLF1207"]
    with pytest.raises(ValueError, match="Source entry count mismatch"):
        check_curriculum(program, rows, courses)


def test_missing_unnumbered_source_course_is_detected(curriculum):
    program, rows, courses = curriculum
    rows[:] = [row for row in rows if row["source_row"] is not None]
    # Keep the total entry count plausible to exercise the unnumbered quota.
    program["digitization"]["source_course_entries"] = len(rows)
    with pytest.raises(ValueError, match="Unnumbered source entry count mismatch"):
        check_curriculum(program, rows, courses)


@pytest.mark.parametrize("value", [0, -1, "1", True])
def test_invalid_numbered_source_row_is_rejected(curriculum, value):
    program, rows, courses = curriculum
    rows[0]["source_row"] = value
    with pytest.raises(ValueError, match="Invalid source row"):
        check_curriculum(program, rows, courses)


@pytest.mark.parametrize("value", [None, 999, "8"])
def test_missing_or_invalid_source_page_identifies_course(curriculum, value):
    program, rows, courses = curriculum
    rows[0]["source_page"] = value
    with pytest.raises(ValueError, match="Missing/invalid source page.*PHI1006.*source_row=1"):
        check_curriculum(program, rows, courses)


@pytest.mark.parametrize("field,value", [("source_rows", [999]), ("source_page", None)])
def test_catalog_source_provenance_must_match_source(curriculum, field, value):
    program, rows, courses = curriculum
    courses[0][field] = value
    with pytest.raises(ValueError, match=f"Catalog {field} differs from source"):
        check_curriculum(program, rows, courses)


def test_duplicate_choice_group_ids_are_rejected(curriculum):
    program, rows, courses = curriculum
    program["choice_groups"].append(deepcopy(program["choice_groups"][0]))
    with pytest.raises(ValueError, match="Duplicate id.*choice groups"):
        check_curriculum(program, rows, courses)


@pytest.mark.parametrize("group_ids,expected", [(["missing"], "Unknown choice group"), (["programming"] * 2, "Duplicate choice group reference")])
def test_course_choice_groups_must_exist_and_be_unique(curriculum, group_ids, expected):
    program, rows, courses = curriculum
    courses[0]["choice_group_ids"] = group_ids
    with pytest.raises(ValueError, match=expected):
        check_curriculum(program, rows, courses)


def test_course_cannot_lose_one_of_its_source_groups(curriculum):
    program, rows, courses = curriculum
    course = next(course for course in courses if course["code"] == "MAT3323")
    course["choice_group_ids"].pop()
    with pytest.raises(ValueError, match="choice_group_ids differs from source.*MAT3323"):
        check_curriculum(program, rows, courses)


@pytest.mark.parametrize("issue,expected", [("unknown_course", "Unknown course"), ("duplicate_course", "Duplicate group member"), ("unknown_row", "Unknown source rows")])
def test_group_members_and_source_rows_are_checked(curriculum, issue, expected):
    program, rows, courses = curriculum
    group = program["choice_groups"][0]
    if issue == "unknown_course":
        group["course_codes"][0] = "MAT9999"
    elif issue == "duplicate_course":
        group["course_codes"].append(group["course_codes"][0])
    else:
        group["source_rows"].append(999)
    with pytest.raises(ValueError, match=expected):
        check_curriculum(program, rows, courses)


def test_unknown_track_group_is_value_error(curriculum):
    program, rows, courses = curriculum
    program["track_selection"]["tracks"][0]["choice_group_ids"] = ["missing"]
    with pytest.raises(ValueError, match="Unknown choice group in track.*missing"):
        check_curriculum(program, rows, courses)


def test_unknown_graduation_course_is_value_error(curriculum):
    program, rows, courses = curriculum
    program["graduation_selection"]["paths"][0]["course_codes"].append("MAT9999")
    with pytest.raises(ValueError, match="Unknown course.*graduation path.*MAT9999"):
        check_curriculum(program, rows, courses)


@pytest.mark.parametrize(
    "field,value",
    [
        ("prerequisite_status", "transcribed"),
        ("prerequisite_variants", [[["MAT2314", "MAT2304"]]]),
        ("prerequisites", []),
        ("prerequisites_raw", ""),
        ("external_prerequisite_codes", ["MAT9999"]),
    ],
)
def test_conflicting_prerequisites_cannot_be_silently_resolved(curriculum, field, value):
    program, rows, courses = curriculum
    course = next(course for course in courses if course["code"] == "MAT3325")
    course[field] = value
    with pytest.raises(ValueError, match=f"Catalog {field} differs from source.*MAT3325"):
        check_curriculum(program, rows, courses)


def test_conflict_report_preserves_each_source_condition_without_mutation(curriculum):
    program, rows, courses = curriculum
    before = deepcopy(curriculum)
    report = check_curriculum(program, rows, courses)
    assert report["conflicting_prerequisite_courses"] == ["MAT3325"]
    conflict, = report["prerequisite_conflicts"]
    assert conflict["code"] == "MAT3325"
    assert conflict["source_rows"] == [56, 72]
    assert conflict["source_entries"] == [
        {key: row[key] for key in ("source_row", "source_page", "prerequisites_raw")}
        for row in rows if row["code"] == "MAT3325"
    ]
    assert len(conflict["prerequisite_variants"]) == 2
    assert curriculum == before
    assert program["catalog_status"] == "draft_unverified"


@pytest.mark.parametrize("field,value", [("name", "Changed"), ("credits", 4), ("hours", {})])
def test_conflicting_source_metadata_requires_review(curriculum, field, value):
    program, rows, courses = curriculum
    occurrences = [row for row in rows if row["code"] == "MAT3323"]
    occurrences[1][field] = value
    before = deepcopy(rows)
    with pytest.raises(ValueError, match="Conflicting course metadata.*MAT3323.*54.*62"):
        build_courses(program, rows)
    assert rows == before


def test_equivalent_prerequisite_order_does_not_create_conflict(curriculum):
    program, rows, _ = curriculum
    occurrences = [row for row in rows if row["code"] == "MAT3323"]
    occurrences[0]["prerequisites_raw"] = "MAT2301/MAT2302"
    occurrences[1]["prerequisites_raw"] = "MAT2302 / MAT2301"
    course = next(course for course in build_courses(program, rows) if course["code"] == "MAT3323")
    assert course["prerequisite_status"] == "transcribed"
    assert len(course["prerequisite_variants"]) == 1
    assert course["source_rows"] == [54, 62]


def test_invalid_prerequisite_expression_identifies_source(curriculum):
    program, rows, _ = curriculum
    row = next(row for row in rows if row["source_row"] == 56)
    row["prerequisites_raw"] = "MAT2301/"
    with pytest.raises(ValueError, match="MAT3325.*source_row=56.*page=12"):
        build_courses(program, rows)


def test_cycles_in_alternative_source_prerequisites_are_checked(curriculum):
    program, rows, _ = curriculum
    row = next(row for row in rows if row["source_row"] == 72)
    row["prerequisites_raw"] = "MAT3325"
    courses = build_courses(program, rows)
    with pytest.raises(ValueError, match="Prerequisite cycle involving MAT3325"):
        check_curriculum(program, rows, courses)


def test_check_cli_validates_stored_catalog_and_leaves_files_unchanged(curriculum, tmp_path, monkeypatch, capsys):
    program, rows, courses = curriculum
    courses[-1] = deepcopy(courses[0])
    directory = tmp_path / program["program_id"]
    directory.mkdir()
    for filename, data in zip(("curriculum.json", "source_rows.json", "courses.json"), curriculum):
        (directory / filename).write_text(json.dumps(data), encoding="utf-8")
    before = {path: path.read_bytes() for path in directory.iterdir()}
    monkeypatch.setattr(build_catalogs, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["build_catalogs.py", "--check"])
    with pytest.raises(SystemExit) as error:
        build_catalogs.main()
    assert error.value.code == 1
    assert "Duplicate code" in capsys.readouterr().err
    assert {path: path.read_bytes() for path in directory.iterdir()} == before


@pytest.mark.parametrize("action", ["--check", "--write"])
def test_cli_preserves_source_conflicts_and_review_status(curriculum, tmp_path, monkeypatch, capsys, action):
    program, rows, courses = curriculum
    directory = tmp_path / program["program_id"]
    directory.mkdir()
    for filename, data in zip(("curriculum.json", "source_rows.json", "courses.json"), curriculum):
        (directory / filename).write_text(json.dumps(data), encoding="utf-8")
    source_files = [directory / "curriculum.json", directory / "source_rows.json"]
    before = {path: path.read_bytes() for path in source_files}
    monkeypatch.setattr(build_catalogs, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["build_catalogs.py", action, "--report"])
    build_catalogs.main()
    report = json.loads(capsys.readouterr().out)["programs"][0]
    assert report["conflicting_prerequisite_courses"] == ["MAT3325"]
    assert report["review_status"] == "pending_peer_review"
    assert json.loads((directory / "courses.json").read_text(encoding="utf-8")) == courses
    assert {path: path.read_bytes() for path in source_files} == before


def test_write_cli_does_not_overwrite_catalog_when_source_metadata_conflicts(curriculum, tmp_path, monkeypatch, capsys):
    program, rows, _ = curriculum
    row = next(row for row in rows if row["source_row"] == 62)
    row["credits"] = 999
    directory = tmp_path / program["program_id"]
    directory.mkdir()
    for filename, data in zip(("curriculum.json", "source_rows.json", "courses.json"), curriculum):
        (directory / filename).write_text(json.dumps(data), encoding="utf-8")
    before = {path: path.read_bytes() for path in directory.iterdir()}
    monkeypatch.setattr(build_catalogs, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["build_catalogs.py", "--write"])
    with pytest.raises(SystemExit) as error:
        build_catalogs.main()
    assert error.value.code == 1
    assert "Conflicting course metadata" in capsys.readouterr().err
    assert {path: path.read_bytes() for path in directory.iterdir()} == before
