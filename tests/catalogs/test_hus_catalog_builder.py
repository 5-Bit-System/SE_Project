"""Offline checks for the HUS export boundary and safety rules."""

import copy
import json

import pytest

from app.config import PROJECT_ROOT
from app.progress import calculate_progress
from app.rules import evaluate_eligibility
from database.hus_db.catalog_builder import build_catalogs

SOURCE = PROJECT_ROOT / "database" / "data" / "hus_source.json"


@pytest.fixture(scope="module")
def bundle():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def catalogs(bundle):
    return {catalog.program.program_id: catalog for catalog in build_catalogs(bundle)}


def test_four_stable_source_preserving_drafts(bundle, catalogs):
    assert set(catalogs) == {
        "toan_hoc_7460101_2022", "toan_tin_7460117_2022",
        "khmtt_7480113qtd_2022", "khdl_7460108_2022",
    }
    assert sum(len(c.courses) for c in catalogs.values()) == 290
    assert sum(len(course.source_occurrences) for c in catalogs.values() for course in c.courses) == 297
    assert all(c.program.catalog_status == "draft_unverified" and c.program.catalog_revision is None
               for c in catalogs.values())
    assert all(c.metadata_schema_version == "1.0" for c in catalogs.values())
    assert all(course.difficulty is None and course.topics is None and course.workload is None
               for c in catalogs.values() for course in c.courses)
    changed = copy.deepcopy(bundle)
    for row in changed["tables"]["curricula"]:
        old = row["curriculum_id"]
        row["curriculum_id"] = old + 100
    for table in ("curriculum_courses", "course_prerequisites", "official_curriculum_groups", "official_curriculum_entries"):
        for row in changed["tables"][table]:
            row["curriculum_id"] += 100
    assert [c.program.program_id for c in build_catalogs(changed)] == sorted(catalogs)


def test_unknown_prerequisite_never_unlocks(catalogs):
    math = catalogs["toan_hoc_7460101_2022"]
    course = next(c for c in math.courses if c.code == "MAT3359")
    assert course.prerequisite_status == "unknown"
    assert course.prerequisites_raw
    all_other = {c.code for c in math.courses if c.code != course.code}
    outcome = evaluate_eligibility(math, all_other)
    blocked = next(c for c in outcome.blocked_courses if c.code == course.code)
    assert any(reason.kind == "prerequisite_unknown" for reason in blocked.reasons)
    with pytest.raises(ValueError):
        evaluate_eligibility(math, {"MAT4083"})  # belongs to another major


def test_selections_and_excluded_credits(catalogs):
    math = catalogs["toan_hoc_7460101_2022"]
    groups = {g.id: g for g in math.program.choice_groups}
    assert len(groups["language"].course_codes) == 7
    assert groups["language"].required_credits == 5
    assert {t.id for t in math.program.track_selection.tracks} == {"V.2.1", "V.2.2", "V.2.3"}
    assert math.program.graduation_selection.mode == "exactly_one_path"
    assert len(math.program.graduation_selection.paths) == 3
    selected = evaluate_eligibility(math, set(), selected_track_id="V.2.3", selected_graduation_path_id="V.3.3")
    other = next(c for c in selected.blocked_courses if c.code == "MAT4071")
    assert any(r.kind == "graduation_path_mismatch" for r in other.reasons)
    passed = {"CME1000", "PES1000", "HUS1012", "FLF1107"}
    progress = calculate_progress(math, passed)
    assert progress.total.earned_credits == 5
    full = evaluate_eligibility(math, passed)
    another_language = next(c for c in full.blocked_courses if c.code == "FLF1207")
    assert any(r.kind == "choice_group_full" for r in another_language.reasons)
    for code in passed - {"FLF1107"}:
        course = next(c for c in math.courses if c.code == code)
        assert course.requirement_type == "required_excluded" and not course.counted_in_total


@pytest.mark.parametrize("mutate", [
    lambda t: t["courses"].append(copy.deepcopy(t["courses"][0])),
    lambda t: t["official_curriculum_entries"][0].update(credits_in_source=99),
    lambda t: t["curriculum_courses"].pop(),
    lambda t: t["course_prerequisites"][0].update(group_no=0),
])
def test_rejects_inconsistent_export(bundle, mutate):
    changed = copy.deepcopy(bundle)
    mutate(changed["tables"])
    with pytest.raises(ValueError):
        build_catalogs(changed)
