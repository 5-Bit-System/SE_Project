import copy
import json

import pytest

from app.config import PROJECT_ROOT
from app.errors import StorageDataError
from app.infrastructure.json_catalog_repository import load_catalog

SAMPLE_ROOT = PROJECT_ROOT / "data" / "curricula"
PROGRAM_ID = "khdl_7460108_2022"


def sample_documents():
    directory = SAMPLE_ROOT / PROGRAM_ID
    return tuple(
        json.loads((directory / name).read_text(encoding="utf-8"))
        for name in ("curriculum.json", "courses.json", "vocabulary.json")
    )


def write_documents(root, program, envelope, vocabulary):
    directory = root / PROGRAM_ID
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in zip(
        ("curriculum.json", "courses.json", "vocabulary.json"),
        (program, envelope, vocabulary),
    ):
        (directory / name).write_text(json.dumps(value), encoding="utf-8")


def test_envelope_loads_65_courses_without_losing_evidence():
    _, envelope, _ = sample_documents()
    catalog = load_catalog(PROGRAM_ID, SAMPLE_ROOT)
    assert len(catalog.courses) == 65
    assert catalog.program.catalog_revision == envelope["catalog_revision"]
    assert catalog.metadata_schema_version == "1.0"
    for actual, source in zip(catalog.courses, envelope["courses"]):
        assert actual.model_dump()["field_evidence"] == source["field_evidence"]
        assert actual.topics is None
        assert actual.workload is None
        assert actual.prerequisite_status == source["prerequisite_status"]


@pytest.mark.parametrize("change", ["program", "revision", "schema", "vocabulary", "missing"])
def test_envelope_identity_and_versions_must_agree(tmp_path, change):
    program, envelope, vocabulary = sample_documents()
    if change == "program":
        envelope["program_id"] = "other"
    elif change == "revision":
        envelope["catalog_revision"] = "other"
    elif change == "schema":
        envelope["metadata_schema_version"] = "99"
    elif change == "vocabulary":
        vocabulary["vocabulary_version"] = "99"
    else:
        del envelope["courses"][0]["prerequisite_status"]
    write_documents(tmp_path, program, envelope, vocabulary)
    with pytest.raises(StorageDataError):
        load_catalog(PROGRAM_ID, tmp_path)


def test_null_is_not_empty(tmp_path):
    program, envelope, vocabulary = sample_documents()
    first = envelope["courses"][0]
    first["topics"] = []
    first["field_evidence"]["topics"] = copy.deepcopy(first["field_evidence"]["code"])
    write_documents(tmp_path, program, envelope, vocabulary)
    result = load_catalog(PROGRAM_ID, tmp_path)
    assert result.courses[0].topics == []
    assert result.courses[1].topics is None
    assert result.courses[0].model_dump()["topics"] == []


@pytest.mark.parametrize("change", ["enum", "evidence", "review", "rubric", "topic"])
def test_invalid_enum_or_verified_without_review_is_rejected(tmp_path, change):
    program, envelope, vocabulary = sample_documents()
    first = envelope["courses"][0]
    if change == "enum":
        first["orientation"] = "invented"
    elif change == "evidence":
        first["topics"] = ["computer_vision"]
    elif change == "review":
        first["field_evidence"]["code"][0]["status"] = "verified"
    elif change == "rubric":
        first["difficulty"] = "easy"
        first["field_evidence"]["difficulty"] = copy.deepcopy(first["field_evidence"]["code"])
    else:
        first["topics"] = ["invented"]
        first["field_evidence"]["topics"] = copy.deepcopy(first["field_evidence"]["code"])
    write_documents(tmp_path, program, envelope, vocabulary)
    with pytest.raises(StorageDataError):
        load_catalog(PROGRAM_ID, tmp_path)


def test_legacy_list_stays_readable_without_inventing_evidence(tmp_path):
    program, envelope, _ = sample_documents()
    legacy = []
    for source in envelope["courses"]:
        item = copy.deepcopy(source)
        item["prerequisite_status"] = "transcribed"
        del item["field_evidence"]
        legacy.append(item)
    directory = tmp_path / PROGRAM_ID
    directory.mkdir()
    (directory / "curriculum.json").write_text(json.dumps(program), encoding="utf-8")
    (directory / "courses.json").write_text(json.dumps(legacy), encoding="utf-8")
    catalog = load_catalog(PROGRAM_ID, tmp_path)
    assert catalog.courses[0].prerequisite_status == "draft_unverified"
    assert catalog.courses[0].field_evidence == {}


@pytest.mark.parametrize(
    "change",
    [
        "missing_prerequisites",
        "missing_counting",
        "negative_hours",
        "fractional_credits",
        "empty_name",
        "excluded_counted",
        "unknown_career",
        "review_timezone",
        "blank_source",
        "conflicting_advisory",
        "legacy_status",
        "unknown_vocabulary",
        "missing_evidence",
        "empty_or",
        "self_reference",
        "missing_external",
        "prerequisite_evidence_conflict",
        "membership_mismatch",
        "path_mismatch",
    ],
)
def test_runtime_loader_rejects_contract_and_structure_holes(tmp_path, change):
    program, envelope, vocabulary = sample_documents()
    first = envelope["courses"][0]
    if change == "missing_prerequisites":
        del first["prerequisites"]
    elif change == "missing_counting":
        del first["counted_in_total"]
    elif change == "negative_hours":
        first["hours"] = {"lecture": -1}
    elif change == "fractional_credits":
        first["credits"] = "3"
    elif change == "empty_name":
        first["name"] = " "
    elif change == "excluded_counted":
        first["requirement_type"] = "required_excluded"
        first["counted_in_total"] = True
    elif change == "unknown_career":
        first["career_paths"] = ["invented"]
        first["field_evidence"]["career_paths"] = copy.deepcopy(first["field_evidence"]["code"])
    elif change == "review_timezone":
        first["field_evidence"]["code"][0].update(
            status="verified", reviewed_by="reviewer", reviewed_at="2026-10-14T10:00:00"
        )
    elif change == "blank_source":
        first["field_evidence"]["code"][0]["source_ref"] = " "
    elif change == "conflicting_advisory":
        first["topics"] = ["computer_vision"]
        first["field_evidence"]["topics"] = copy.deepcopy(first["field_evidence"]["code"])
        first["field_evidence"]["topics"][0]["status"] = "conflict"
    elif change == "legacy_status":
        first["prerequisite_status"] = "transcribed"
    elif change == "unknown_vocabulary":
        vocabulary["vocabulary_version"] = envelope["vocabulary_version"] = "99"
    elif change == "missing_evidence":
        del first["field_evidence"]["credits"]
    elif change == "empty_or":
        first["prerequisites"] = [[]]
    elif change == "self_reference":
        first["prerequisites"] = [[first["code"]]]
    elif change == "missing_external":
        first["prerequisites"] = [["EXT9999"]]
    elif change == "prerequisite_evidence_conflict":
        first["field_evidence"]["prerequisites"][0]["status"] = "conflict"
    elif change == "membership_mismatch":
        target = next(c for c in envelope["courses"] if c["choice_group_ids"])
        target["choice_group_ids"] = []
    else:
        target = next(c for c in envelope["courses"] if c["graduation_path_ids"])
        target["graduation_path_ids"] = []
    write_documents(tmp_path, program, envelope, vocabulary)
    with pytest.raises(StorageDataError):
        load_catalog(PROGRAM_ID, tmp_path)
