"""ZIP-backed lookup, source exceptions and non-personal planning contracts."""

import json
from collections import Counter

import pytest
from fastapi.testclient import TestClient

from app.catalog_contracts import EXPECTED_PROGRAM_IDS
from app.curriculum_reference import (
    TALENT,
    ReferenceError,
    current_cohort,
    list_references,
    plan_reference,
    reference,
    source_pdf,
)
from app.main import app

TALENT_ID = "toan_hoc_tai_nang_7460101_2022"
MATH_ID = "toan_hoc_7460101_2022"


@pytest.fixture
def client():
    with TestClient(app, base_url="http://127.0.0.1:8000") as value:
        yield value


def test_all_five_zip_programs_are_available_without_altering_runtime_registry():
    index = list_references()
    assert {value["program_id"] for value in index["programs"]} == EXPECTED_PROGRAM_IDS | {TALENT_ID}
    assert len(EXPECTED_PROGRAM_IDS) == 4
    assert {value["program_id"]: value["course_count"] for value in index["programs"]} == {
        "khdl_7460108_2022": 65, "khmtt_7480113qtd_2022": 67,
        MATH_ID: 90, "toan_tin_7460117_2022": 68, TALENT_ID: 96,
    }
    assert sum(value["source_occurrence_count"] for value in index["programs"]) == 394
    assert index["default_max_credits"] == 20
    assert index["cohorts"][0] == {"number": 67, "admission_year": 2022}
    assert index["cohorts"][-1]["number"] == current_cohort()
    for program in index["programs"]:
        for cohort in index["cohorts"]:
            value = reference(program["program_id"], cohort["number"])
            assert value["academic_eligibility"] == "not_evaluated"
            assert value["admission_year"] == cohort["admission_year"]
            assert value["applicability"]["later_amendments_reviewed"] is False


def test_talented_visual_inventory_and_source_anomalies_are_preserved():
    doc = json.loads(TALENT.read_text(encoding="utf-8"))
    assert len(doc["rows"]) == 97
    assert set(row[0] for row in doc["rows"]) == set(range(1, 86))
    assert Counter(row[6] for row in doc["rows"]) == {
        8: 14, 9: 17, 10: 13, 11: 16, 12: 12, 13: 13, 14: 12,
    }
    value = reference(TALENT_ID)
    assert value["total_credits"] == 168
    courses = {row["code"]: row for row in value["courses"]}
    assert courses["MAT2320"]["credits"] == 5
    assert courses["MAT4074"]["credits"] == 10
    assert courses["MAT3339"]["name"] == "Đại số tuyến tính 3"
    assert courses["MAT3341"]["name"] == "Giải tích điều hòa"
    assert courses["MAT3344"]["credits"] == 4
    assert {row["pdf_page"] for row in courses["MAT3325"]["source_occurrences"]} == {12, 13}
    assert courses["MAT3359"]["prerequisites"] == [["MAT1202", "MAT3304"], ["MAT3304", "MAT3507"]]
    assert courses["MAT3423"]["external_prerequisite_codes"] == ["MAT3402"]
    assert len(value["issues"]) >= 4
    assert value["tracks"] == []  # Source says two tracks but prints three: no invented rule.


@pytest.mark.parametrize("program_id", [*sorted(EXPECTED_PROGRAM_IDS), TALENT_ID])
def test_source_download_is_allowlisted_and_matches_the_pdf_hash(program_id):
    import hashlib

    path = source_pdf(program_id)
    assert path.parent.name == "pdf"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == reference(program_id)["source_sha256"]


def test_earlier_and_future_cohorts_are_not_silently_mapped():
    for cohort in (66, current_cohort() + 1):
        with pytest.raises(ReferenceError, match="cohort_outside_source_scope"):
            reference(MATH_ID, cohort)
    with pytest.raises(ReferenceError, match="reference_program_not_found"):
        source_pdf("../../.env")


def test_reference_values_are_not_mutable_shared_state():
    value = reference(TALENT_ID)
    value["courses"].clear()
    assert reference(TALENT_ID)["course_count"] == len(reference(TALENT_ID)["courses"]) == 96


def test_plan_budget_defaults_to_20_and_can_be_adjusted_without_student_outcomes():
    result = plan_reference(TALENT_ID, course_codes=["MAT2320", "MAT2302"])
    assert result["max_credits"] == 20
    assert result["selected_credits"] == 10
    assert result["remaining_budget"] == 10
    assert result["academic_eligibility"] == "not_evaluated"
    assert "completed_course_codes" not in result
    assert plan_reference(TALENT_ID, max_credits=12, course_codes=result["course_codes"])["remaining_budget"] == 2
    with pytest.raises(ReferenceError, match="planning_budget_exceeded"):
        plan_reference(TALENT_ID, max_credits=9, course_codes=result["course_codes"])


def test_same_term_selection_never_satisfies_prerequisites():
    result = plan_reference(TALENT_ID, course_codes=["MAT2302", "MAT2303"])
    assert {item["course_code"] for item in result["warnings"]} == {"MAT2303"}
    assert result["warnings"][0]["code"] == "prerequisites_not_verified"


@pytest.mark.parametrize("program_id", [*sorted(EXPECTED_PROGRAM_IDS), TALENT_ID])
def test_source_only_suggestion_stays_within_budget_and_has_no_unmet_assumptions(program_id):
    for budget in (1, 12, 20, 30):
        value = plan_reference(program_id, max_credits=budget, suggest=True)
        courses = {row["code"]: row for row in reference(program_id)["courses"]}
        assert value["selected_credits"] <= budget
        for code in value["course_codes"]:
            assert not courses[code]["prerequisites"]
            assert not courses[code]["prerequisites_raw"]
            assert courses[code]["requirement_type"] not in {"graduation", "required_excluded"}
        assert value["academic_eligibility"] == "not_evaluated"


def test_languages_duplicates_and_foreign_program_courses_are_rejected():
    cases = [(["FLF1107", "FLF1207"], "multiple_languages_in_same_level"),
             (["PHI1006", "PHI1006"], "duplicate_planned_course"),
             (["NOT_IN_PROGRAM"], "planned_course_outside_program")]
    for codes, error in cases:
        with pytest.raises(ReferenceError, match=error):
            plan_reference(TALENT_ID, course_codes=codes)


def test_public_api_works_without_login_and_rejects_personal_context(client):
    assert len(client.get("/curricula/reference").json()["programs"]) == 5
    assert client.get(f"/curricula/reference/{TALENT_ID}?cohort=67").json()["total_credits"] == 168
    assert client.get(f"/curricula/reference/{TALENT_ID}?cohort=66").status_code == 422
    assert client.get("/curricula/reference/unknown").status_code == 404
    url = f"/curricula/reference/{TALENT_ID}/plan"
    assert client.post(url, json={}).json()["max_credits"] == 20
    for field in ("owner", "records", "passed_course_codes", "policy", "verified"):
        assert client.post(url, json={field: []}).status_code == 422
    for budget in (0, 31):
        assert client.post(url, json={"max_credits": budget}).status_code == 422
    result = client.post(url, json={"suggest": True, "max_credits": 12})
    assert result.status_code == 200
    assert result.json()["selected_credits"] <= 12
    assert client.get("/me/course-status").status_code == 401


def test_pdf_http_response_keeps_original_document_bytes(client):
    response = client.get(f"/curricula/reference/{TALENT_ID}/source")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("inline;")
    assert response.content.startswith(b"%PDF")
