"""Enrichment must survive publication without weakening academic rules."""

import copy
import json

import pytest

from app.config import PROJECT_ROOT
from app.errors import StorageDataError
from database.hus_db.catalog_builder import build_catalogs
from database.tools.audit_metadata import value_state


@pytest.fixture(scope="module")
def source():
    return json.loads((PROJECT_ROOT / "database/data/hus_source.json").read_text(encoding="utf-8"))


def test_enrichment_preserves_eligibility_and_bilingual_source_values(source):
    bare = copy.deepcopy(source)
    bare.pop("course_metadata")
    bare.pop("metadata_review", None)
    before = build_catalogs(bare)
    after = build_catalogs(source)
    for original, enriched in zip(before, after, strict=True):
        for old, new in zip(original.courses, enriched.courses, strict=True):
            assert (new.credits, new.prerequisites, new.prerequisite_status,
                    new.prerequisite_variants, new.external_prerequisite_codes) == (
                old.credits, old.prerequisites, old.prerequisite_status,
                old.prerequisite_variants, old.external_prerequisite_codes)
            assert new.name_en and new.field_evidence["name_en"]
            assert new.hours is not None or new.code in {"CME1000", "PES1000"}
            assert new.difficulty is None and new.workload is None
    computer = next(c for c in after if c.program.program_id.startswith("khmtt_"))
    embedded = next(c for c in computer.courses if c.code == "MAT1208")
    assert embedded.hours == {"lecture": 0, "practice": 30, "self_study": 70}
    math = next(c for c in after if c.program.program_id.startswith("toan_hoc_"))
    assert next(c for c in math.courses if c.code == "HUS1011").name_en == "General to Informatics"
    assert next(c for c in computer.courses if c.code == "HUS1011").name_en == "General Informatics"
    math_info = next(c for c in after if c.program.program_id.startswith("toan_tin_"))
    assert next(c for c in math_info.courses if c.code == "MAT3366").name == "Hệ thống máy tính"


@pytest.mark.parametrize("mutation", [
    "duplicate", "foreign", "core_override", "missing_evidence", "bad_hours", "language_without_evidence",
])
def test_reject_invalid_enrichment(source, mutation):
    changed = copy.deepcopy(source)
    row = changed["course_metadata"][0]
    if mutation == "duplicate":
        changed["course_metadata"].append(copy.deepcopy(row))
    elif mutation == "foreign":
        row["program_id"] = "different_cohort"
    elif mutation == "core_override":
        row["values"]["prerequisites"] = []
    elif mutation == "missing_evidence":
        row["field_evidence"].pop("name_en")
    elif mutation == "bad_hours":
        row["values"]["hours"] = {"lecture": -1}
        row["field_evidence"]["hours"] = row["field_evidence"]["name_en"]
    else:
        row["values"]["instruction_language"] = "en"
    with pytest.raises((ValueError, StorageDataError)):
        build_catalogs(changed)


@pytest.mark.parametrize(("value", "expected"), [
    (None, "null"), ("  ", "blank_string"), ([], "empty_list"),
    (0, "present"), (False, "present"), ({"lecture": None}, "unknown_object"),
    ({"lecture": 0}, "present"),
])
def test_completeness_does_not_misclassify_zero_or_false(value, expected):
    assert value_state(value) == expected


def test_api_preserves_both_names_and_hours(source, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    catalog = next(c for c in build_catalogs(source) if c.program.program_id.startswith("toan_tin_"))
    monkeypatch.setattr("app.api.routes.load_catalog", lambda program_id: catalog)
    response = TestClient(app).get("/courses", params={"program_id": catalog.program.program_id})
    assert response.status_code == 200
    row = next(c for c in response.json() if c["code"] == "MAT3366")
    assert row["name"] == "Hệ thống máy tính"
    assert row["name_en"] == "Overview of Computer Systems for Non-Majors"
    assert row["hours"] == {"lecture": 40, "practice": 10, "self_study": 100}
    assert row["field_evidence"]["name_en"]
    assert row["difficulty"] is None
    assert next(g for g in catalog.program.choice_groups if g.id == "V.2.2").name.endswith("Tính toán khoa học")
