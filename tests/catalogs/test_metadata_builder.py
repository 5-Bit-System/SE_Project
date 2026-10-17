import copy
import json
import shutil
import subprocess
import sys

import pytest

from app.config import PROJECT_ROOT
from app.schemas.metadata import CourseEnvelope
from tools.build_catalogs import build_courses, merge_source_fields

SAMPLE_ROOT = PROJECT_ROOT / "data" / "curricula"
PROGRAM_ID = "khdl_7460108_2022"


@pytest.fixture
def temp_catalog_dir(tmp_path):
    dest = tmp_path / PROGRAM_ID
    shutil.copytree(SAMPLE_ROOT / PROGRAM_ID, dest)
    return dest


def test_merge_source_fields_preserves_envelope_and_advisory_metadata(temp_catalog_dir):
    envelope_data = json.loads((temp_catalog_dir / "courses.json").read_text(encoding="utf-8"))
    existing_envelope = CourseEnvelope.model_validate(envelope_data)

    # Enrich first course with advisory metadata and field evidence
    first = existing_envelope.courses[0]
    first.topics = ["artificial_intelligence"]
    first.difficulty = "moderate"
    first.field_evidence["topics"] = copy.deepcopy(first.field_evidence["code"])
    first.field_evidence["difficulty"] = copy.deepcopy(first.field_evidence["code"])
    first.field_evidence["difficulty"][0].rubric_ref = "rubric_v1"

    program = json.loads((temp_catalog_dir / "curriculum.json").read_text(encoding="utf-8"))
    rows = json.loads((temp_catalog_dir / "source_rows.json").read_text(encoding="utf-8"))
    generated = build_courses(program, rows)

    merged = merge_source_fields(existing_envelope, generated)

    # Verify envelope header preserved
    assert merged.metadata_schema_version == existing_envelope.metadata_schema_version
    assert merged.vocabulary_version == existing_envelope.vocabulary_version
    assert merged.program_id == existing_envelope.program_id
    assert merged.catalog_revision == existing_envelope.catalog_revision

    # Verify first course kept advisory metadata and evidence
    merged_first = next(c for c in merged.courses if c.code == first.code)
    assert merged_first.topics == ["artificial_intelligence"]
    assert merged_first.difficulty == "moderate"
    assert "topics" in merged_first.field_evidence
    assert "difficulty" in merged_first.field_evidence


def test_merge_source_fields_handles_null_hours_without_comparing_to_numbers(temp_catalog_dir):
    envelope_data = json.loads((temp_catalog_dir / "courses.json").read_text(encoding="utf-8"))
    existing_envelope = CourseEnvelope.model_validate(envelope_data)

    program = json.loads((temp_catalog_dir / "curriculum.json").read_text(encoding="utf-8"))
    rows = json.loads((temp_catalog_dir / "source_rows.json").read_text(encoding="utf-8"))

    # Set hours with null in rows
    rows[0]["hours"] = {"lecture": None, "practice": 10, "self_study": None}
    generated = build_courses(program, rows)

    merged = merge_source_fields(existing_envelope, generated)
    merged_first = next(c for c in merged.courses if c.code == rows[0]["code"])
    assert merged_first.hours.lecture is None
    assert merged_first.hours.practice == 10
    assert merged_first.hours.self_study is None


def test_builder_check_does_not_modify_target_file(temp_catalog_dir):
    courses_file = temp_catalog_dir / "courses.json"
    original_bytes = courses_file.read_bytes()

    build_script = PROJECT_ROOT / "tools" / "build_catalogs.py"
    # Run build_catalogs --check pointing to temp directory's parent
    result = subprocess.run(
        [sys.executable, str(build_script), "--check", "--root", str(temp_catalog_dir.parent)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"build_catalogs --check failed:\n{result.stderr}\n{result.stdout}"
    )
    assert courses_file.read_bytes() == original_bytes


def test_builder_write_preserves_metadata_evidence_and_envelope_extensions(temp_catalog_dir):
    target = temp_catalog_dir / "courses.json"
    document = json.loads(target.read_text(encoding="utf-8"))
    document["handoff_note"] = "Preserve this extension"
    course = document["courses"][0]
    course["topics"] = ["programming"]
    course["description"] = "Synthetic test description, not product metadata"
    for field in ("topics", "description"):
        course["field_evidence"][field] = copy.deepcopy(course["field_evidence"]["code"])
    target.write_text(json.dumps(document), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.build_catalogs",
            "--write",
            "--root",
            str(temp_catalog_dir.parent),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    actual = json.loads(target.read_text(encoding="utf-8"))
    assert actual == document


@pytest.mark.parametrize("change", ["remove", "add", "conflict", "verified_name"])
def test_builder_rejects_changes_that_need_source_review(temp_catalog_dir, change):
    envelope = CourseEnvelope.model_validate_json(
        (temp_catalog_dir / "courses.json").read_text(encoding="utf-8")
    )
    program = json.loads((temp_catalog_dir / "curriculum.json").read_text(encoding="utf-8"))
    rows = json.loads((temp_catalog_dir / "source_rows.json").read_text(encoding="utf-8"))
    generated = build_courses(program, rows)
    if change == "remove":
        generated.pop(0)
    elif change == "add":
        generated.append({**generated[0], "code": "NEW9999"})
    elif change == "conflict":
        generated[0].update(
            prerequisite_status="source_conflict",
            prerequisites=[["EXT9999"]],
            prerequisite_variants=[[], [["EXT9999"]]],
        )
    else:
        envelope.courses[0].field_evidence["name"][0].status = "verified"
        envelope.courses[0].field_evidence["name"][0].reviewed_by = "reviewer"
        envelope.courses[0].field_evidence["name"][0].reviewed_at = "2026-10-14T10:00:00+07:00"
        generated[0]["name"] = "Changed"
    with pytest.raises(ValueError):
        merge_source_fields(envelope, generated)
