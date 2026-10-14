import copy
import json
from pathlib import Path

import pytest

from app.catalog_validation import validate_catalog
from app.errors import StorageDataError
from app.infrastructure.json_catalog_repository import load_catalog
from app.models import Catalog, Course, Program
from app.rules import evaluate_eligibility

SAMPLE_ROOT = Path(__file__).resolve().parents[1] / "data" / "curricula"
PROGRAM_ID = "khdl_7460108_2022"


def get_sample_catalog():
    return load_catalog(PROGRAM_ID, SAMPLE_ROOT)


def test_valid_sample_catalog_passes_validation():
    catalog = get_sample_catalog()
    validate_catalog(catalog)


@pytest.mark.parametrize(
    "case,mutation",
    [
        ("empty_or", lambda c: setattr(c.courses[0], "prerequisites", [[]])),
        (
            "duplicate_in_or",
            lambda c: setattr(c.courses[0], "prerequisites", [["MAT101", "MAT101"]]),
        ),
        ("self_cycle", lambda c: setattr(c.courses[0], "prerequisites", [[c.courses[0].code]])),
        (
            "direct_cycle",
            lambda c: (
                setattr(c.courses[0], "prerequisites", [[c.courses[1].code]]),
                setattr(c.courses[1], "prerequisites", [[c.courses[0].code]]),
            ),
        ),
        (
            "invalid_group",
            lambda c: setattr(c.courses[0], "choice_group_ids", ["nonexistent_group"]),
        ),
        (
            "missing_external_code",
            lambda c: (
                setattr(c.courses[0], "prerequisites", [["EXTERNAL999"]]),
                setattr(c.courses[0], "external_prerequisite_codes", []),
            ),
        ),
        (
            "internal_marked_external",
            lambda c: (
                setattr(c.courses[0], "prerequisites", [[c.courses[1].code]]),
                setattr(c.courses[0], "external_prerequisite_codes", [c.courses[1].code]),
            ),
        ),
        (
            "missing_rubric_ref",
            lambda c: (
                setattr(c.courses[0], "difficulty", "easy"),
                c.courses[0].field_evidence.setdefault(
                    "difficulty",
                    [
                        {
                            "source_ref": "ref",
                            "locator": "loc",
                            "method": "curated_mapping",
                            "status": "draft_unverified",
                            "rubric_ref": None,
                        }
                    ],
                ),
            ),
        ),
    ],
)
def test_invalid_catalog_structures_are_rejected(case, mutation):
    catalog = get_sample_catalog()
    mutation(catalog)
    with pytest.raises(StorageDataError):
        validate_catalog(catalog)


def test_conflict_or_unknown_with_empty_prerequisites_is_blocked():
    catalog = get_sample_catalog()
    # Find a course and set empty prerequisites but conflict or unknown status
    c_conflict = copy.deepcopy(catalog.courses[0])
    c_conflict.code = "TEST_CONF"
    c_conflict.prerequisites = []
    c_conflict.prerequisite_status = "conflict"

    c_unknown = copy.deepcopy(catalog.courses[0])
    c_unknown.code = "TEST_UNK"
    c_unknown.prerequisites = []
    c_unknown.prerequisite_status = "unknown"

    test_catalog = Catalog(
        program=catalog.program,
        courses=[c_conflict, c_unknown],
    )

    result = evaluate_eligibility(test_catalog, passed_codes=[])
    assert len(result.eligible_courses) == 0
    assert len(result.blocked_courses) == 2

    blocked_map = {b.code: b for b in result.blocked_courses}
    assert any(r.kind == "source_conflict" for r in blocked_map["TEST_CONF"].reasons)
    assert any(r.kind == "prerequisite_unknown" for r in blocked_map["TEST_UNK"].reasons)


def test_or_group_satisfied_by_internal_passed_course_with_unresolved_external():
    catalog = get_sample_catalog()
    c_target = copy.deepcopy(catalog.courses[0])
    c_target.code = "TARGET"
    c_target.prerequisites = [["INTERNAL_PASSED", "EXTERNAL_UNKNOWN"]]
    c_target.prerequisite_status = "unresolved_external"
    c_target.external_prerequisite_codes = ["EXTERNAL_UNKNOWN"]

    c_internal = copy.deepcopy(catalog.courses[0])
    c_internal.code = "INTERNAL_PASSED"
    c_internal.prerequisites = []
    c_internal.prerequisite_status = "draft_unverified"

    test_catalog = Catalog(
        program=catalog.program,
        courses=[c_target, c_internal],
    )

    # When INTERNAL_PASSED is in passed_codes, TARGET should be eligible!
    result = evaluate_eligibility(test_catalog, passed_codes=["INTERNAL_PASSED"])
    assert any(c.code == "TARGET" for c in result.eligible_courses)
