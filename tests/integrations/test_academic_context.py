"""Academic source contract tests; invented catalog/policies only."""

import copy
import importlib
import importlib.util

import pytest


def module():
    assert importlib.util.find_spec("app.academic_context") is not None, (
        "Missing source-owned AcademicContext; legacy TranscriptRecord cannot safely ingest portal"
    )
    return importlib.import_module("app.academic_context")


def row(key="1", code="TOY101", grade="4,2", letter="D", grade4="1", credits="3"):
    return {"row_key": key, "code": code, "name": "Invented course", "credits": credits,
            "grade10": grade, "letter": letter, "grade4": grade4,
            "term": "HỌC KỲ 1 - 2099-2100"}


def source(rows=None):
    return {"schema_version": 1, "digest": "synthetic-snapshot", "completeness": "complete",
            "unknown_rows": [], "attempts": [row()] if rows is None else rows,
            "source_summary": [["Synthetic official summary kept unchanged"]]}


def inputs(toy_catalog):
    policy = module().AcademicPolicy(
        version="synthetic-policy-v1", source_ref="synthetic-only:test-spec",
        program_ids=("toy",), letter_bands={"D": (4.0, 4.9, 1.0),
        "B": (7.0, 7.9, 3.0), "F": (0.0, 3.9, 0.0)})
    return {"owner_id": "owner-a", "catalog": toy_catalog, "catalog_revision": "catalog-v1",
            "binding": {"program_id": "toy", "catalog_revision": "catalog-v1",
                        "policy_version": policy.version, "verified": True,
                        "evidence_ref": "synthetic-only:binding"}, "policy": policy}


def test_ready_context_uses_explicit_policy_not_legacy_grade_threshold(toy_catalog):
    result = module().build_context(source(), **inputs(toy_catalog))
    assert result["status"] == "ready"
    assert result["completed_course_codes"] == ["TOY101"]
    assert result["outcomes"][0]["state"] == "completed"
    assert result["project_gpa"] is None


@pytest.mark.parametrize("changes,reason", [
    ({"completeness": "unknown"}, "source_incomplete"),
    ({"completeness": "partial"}, "source_incomplete"),
    ({"unknown_rows": [{"cells": ["unparsed"]}]}, "unparsed_source_rows"),
])
def test_unproven_source_cannot_enable_recommendations(toy_catalog, changes, reason):
    raw = source()
    raw.update(changes)
    result = module().build_context(raw, **inputs(toy_catalog))
    assert result["status"] != "ready"
    assert reason in result["blocking_reasons"]
    with pytest.raises(module().AcademicContextError, match="academic_context_not_ready"):
        module().require_ready(result)


def test_no_binding_or_wrong_catalog_never_uses_shared_course_codes(toy_catalog):
    kwargs = inputs(toy_catalog)
    for binding in (None, {**kwargs["binding"], "program_id": "foreign"},
                    {**kwargs["binding"], "catalog_revision": "old"},
                    {**kwargs["binding"], "verified": False}):
        result = module().build_context(source(), **{**kwargs, "binding": binding})
        assert result["status"] == "needs_program_binding"
        assert result["completed_course_codes"] == []


def test_retakes_and_unmapped_suffix_stay_unresolved(toy_catalog):
    rows = [row(), row(key="2", grade="7", letter="B", grade4="3"),
            row(key="3", code="TOY102E")]
    original = copy.deepcopy(rows)
    result = module().build_context(source(rows), **inputs(toy_catalog))
    assert result["status"] == "needs_policy_review"
    assert result["completed_course_codes"] == []
    assert result["outcomes"][0]["reason"] == "retake_policy_unresolved"
    assert result["outcomes"][1]["state"] == "out_of_catalog"
    assert sum(len(outcome["row_keys"]) for outcome in result["outcomes"]) == 3
    assert rows == original


@pytest.mark.parametrize("attempt", [row(grade="", letter="", grade4=""),
    row(grade="", letter="I", grade4=""), row(grade="9", letter="D", grade4="1"),
    row(grade="4.2", letter="D", grade4="3"), row(credits="4"),
    row(grade="NaN"), row(grade="-1"), row(grade="Miễn", letter="P", grade4="")])
def test_missing_conflicting_or_unsupported_grades_do_not_default_to_passed(toy_catalog, attempt):
    result = module().build_context(source([attempt]), **inputs(toy_catalog))
    assert result["outcomes"][0]["state"] == "unresolved"
    assert result["status"] == "needs_policy_review"
    assert result["completed_course_codes"] == []


def test_zero_fail_is_distinct_from_unknown(toy_catalog):
    result = module().build_context(source([row(grade="0", letter="F", grade4="0")]),
                                    **inputs(toy_catalog))
    assert result["status"] == "ready"
    assert result["outcomes"][0]["state"] == "not_completed"
    assert result["completed_course_codes"] == []


def test_revision_binds_owner_snapshot_catalog_and_policy(toy_catalog):
    kwargs = inputs(toy_catalog)
    original = module().build_context(source(), **kwargs)
    for change in ({"owner_id": "owner-b"}, {"catalog_revision": "catalog-v2"},
                   {"binding": {**kwargs["binding"], "evidence_ref": "new-review"}}):
        result = module().build_context(source(), **{**kwargs, **change})
        assert result["revision"] != original["revision"]
    changed = module().build_context({**source(), "digest": "new-source"}, **kwargs)
    assert changed["revision"] != original["revision"]
    with pytest.raises(module().AcademicContextError, match="context_changed"):
        module().require_ready(original, "wrong-revision")


def test_policy_missing_or_not_applicable_never_reuses_project_defaults(toy_catalog):
    kwargs = inputs(toy_catalog)
    for policy in (None, module().AcademicPolicy("other", "synthetic", ("foreign",), {})):
        result = module().build_context(source(), **{**kwargs, "policy": policy})
        assert result["status"] == "needs_policy_review"
        assert result["completed_course_codes"] == []


@pytest.mark.parametrize("changes,reason", [
    ({"schema_version": 99}, "source_schema_unsupported"),
    ({"attempts": []}, "source_empty_unverified"),
    ({"attempts": [row(key="same"), row(key="same", code="TOY102")]},
     "source_row_keys_invalid"),
])
def test_source_integrity_gates_cannot_be_bypassed_with_complete_flag(toy_catalog, changes, reason):
    result = module().build_context({**source(), **changes}, **inputs(toy_catalog))
    assert result["status"] != "ready"
    assert reason in result["blocking_reasons"]
    assert result["completed_course_codes"] == []


@pytest.mark.parametrize("changes,reason", [
    ({"digest": None}, "source_digest_missing"),
    ({"unknown_rows": None}, "source_rows_invalid"),
])
def test_incomplete_source_envelope_is_not_academic_evidence(toy_catalog, changes, reason):
    result = module().build_context({**source(), **changes}, **inputs(toy_catalog))
    assert result["status"] != "ready"
    assert reason in result["blocking_reasons"]
    assert result["completed_course_codes"] == []


def test_non_gpa_grade_cannot_hide_numeric_zero(toy_catalog):
    kwargs = inputs(toy_catalog)
    kwargs["policy"] = module().AcademicPolicy(
        "synthetic-policy-v1", "synthetic-only:test-spec", ("toy",), {"P": (5, 10, None)})
    result = module().build_context(source([row(grade="6", letter="P", grade4=0)]), **kwargs)
    assert result["status"] != "ready"
