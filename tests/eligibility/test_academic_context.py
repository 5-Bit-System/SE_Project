from app.academic_context import AcademicPolicy, build_context, require_ready
from app.models import Catalog, Course, Program


def inputs(catalog_status):
    program_id = "synthetic-program"
    catalog = Catalog(
        program=Program(
            program_id=program_id,
            name="Synthetic program",
            total_credits=3,
            catalog_status=catalog_status,
            source_file="synthetic-only",
            source_pages="1",
        ),
        courses=[Course(
            code="SYN101",
            name="Synthetic course",
            credits=3,
            block="synthetic",
            prerequisite_status="verified",
        )],
    )
    snapshot = {
        "completeness": "complete",
        "unknown_rows": [],
        "digest": "synthetic-digest",
        "schema_version": 1,
        "attempts": [{
            "row_key": "synthetic-row-1",
            "code": "SYN101",
            "credits": "3",
            "grade10": "9",
            "grade4": "4",
            "letter": "A",
            "term": "HỌC KỲ 1 - 2025-2026",
        }],
    }
    binding = {
        "verified": True,
        "evidence_ref": "synthetic-only",
        "program_id": program_id,
        "catalog_revision": "synthetic-revision",
        "policy_version": "synthetic-policy",
    }
    policy = AcademicPolicy(
        version="synthetic-policy",
        source_ref="synthetic-policy-source",
        program_ids=(program_id,),
        letter_bands={"A": (8.5, 10, 4)},
    )
    return catalog, snapshot, binding, policy


def test_draft_catalog_keeps_academic_context_unready():
    catalog, snapshot, binding, policy = inputs("draft_unverified")

    context = build_context(
        snapshot,
        owner_id="synthetic-owner",
        catalog=catalog,
        catalog_revision="synthetic-revision",
        binding=binding,
        policy=policy,
    )

    assert context["status"] == "needs_policy_review"
    assert "catalog_unverified" in context["blocking_reasons"]
    assert context["completed_course_codes"] == []


def test_verified_catalog_can_produce_a_ready_academic_context():
    catalog, snapshot, binding, policy = inputs("verified")

    context = build_context(
        snapshot,
        owner_id="synthetic-owner",
        catalog=catalog,
        catalog_revision="synthetic-revision",
        binding=binding,
        policy=policy,
    )

    assert context["status"] == "ready"
    assert require_ready(context) == {"SYN101"}
