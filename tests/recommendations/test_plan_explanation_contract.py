"""Phase 1 contract tests for PlanExplanation schema and /me/recommendations boundary."""

import pytest
from pydantic import ValidationError

from app.models import (
    Catalog,
    Course,
    PlanExplanation,
    Program,
    RecommendationRequest,
    RecommendationResponse,
)
from app.schemas import recommendation as recommendation_schema
from app.services.recommendation_service import recommend
from tests.integrations.conftest import client, ready_context  # noqa: F401


def _sample_catalog() -> Catalog:
    return Catalog(
        program=Program(
            program_id="demo",
            name="Chuong trinh kiem thu",
            total_credits=12,
            catalog_status="verified",
            source_file="synthetic",
            source_pages="none",
        ),
        courses=[
            Course(
                code="A",
                name="Nhap mon",
                credits=3,
                block="required",
                prerequisite_status="verified",
                source_status="verified",
            ),
            Course(
                code="B",
                name="Du lieu",
                credits=3,
                block="required",
                prerequisites=[["A"]],
                prerequisite_status="verified",
                source_status="verified",
            ),
        ],
    )


def test_plan_explanation_defaults_and_exports():
    assert recommendation_schema.PlanExplanation is PlanExplanation
    assert "PlanExplanation" in recommendation_schema.__all__

    explanation = PlanExplanation(
        headline="Lo trinh hoc ky toi uu",
        bundle_rationale="Can bang giua mon bat buoc va dung luong tin chi.",
    )
    assert explanation.highlights == []
    assert explanation.caveats == []
    assert explanation.explanation_source == "deterministic_fallback"

    llm_explanation = PlanExplanation(
        headline="A" * 200,
        bundle_rationale="B" * 1000,
        highlights=[f"H{i}" for i in range(5)],
        caveats=[f"C{i}" for i in range(5)],
        explanation_source="llm_grounded",
    )
    assert llm_explanation.explanation_source == "llm_grounded"
    assert len(llm_explanation.highlights) == 5
    assert len(llm_explanation.caveats) == 5


def test_plan_explanation_forbids_extra_and_enforces_bounds():
    with pytest.raises(ValidationError):
        PlanExplanation(
            headline="Hop le",
            bundle_rationale="Hop le",
            unexpected="forbidden",
        )

    for invalid_kwargs in [
        {"headline": "", "bundle_rationale": "Hop le"},
        {"headline": "A" * 201, "bundle_rationale": "Hop le"},
        {"headline": "Hop le", "bundle_rationale": ""},
        {"headline": "Hop le", "bundle_rationale": "B" * 1001},
        {"headline": "Hop le", "bundle_rationale": "Hop le", "highlights": ["x"] * 6},
        {"headline": "Hop le", "bundle_rationale": "Hop le", "caveats": ["x"] * 6},
        {"headline": "Hop le", "bundle_rationale": "Hop le", "explanation_source": "custom"},
    ]:
        with pytest.raises(ValidationError):
            PlanExplanation(**invalid_kwargs)


def test_recommendation_request_include_narrative_strict_bool():
    default_req = RecommendationRequest(program_id="demo")
    assert default_req.include_narrative is False

    enabled_req = RecommendationRequest(program_id="demo", include_narrative=True)
    assert enabled_req.include_narrative is True

    for invalid_value in ("true", "false", "yes", 1, 0):
        with pytest.raises(ValidationError):
            RecommendationRequest(program_id="demo", include_narrative=invalid_value)


def test_recommendation_response_plan_explanation_and_service_compat():
    default_resp = RecommendationResponse(
        program_id="demo",
        catalog_status="verified",
        recommendations=[],
        eligible_count=0,
    )
    assert default_resp.plan_explanation is None

    explanation = PlanExplanation(
        headline="Goi y hoc ky",
        bundle_rationale="Phu hop voi tien do hien tai.",
    )
    with_explanation = RecommendationResponse(
        program_id="demo",
        catalog_status="verified",
        recommendations=[],
        eligible_count=0,
        plan_explanation=explanation,
    )
    assert with_explanation.plan_explanation == explanation

    service_resp = recommend(
        _sample_catalog(),
        RecommendationRequest(program_id="demo"),
    )
    assert service_resp.intent.status == "ready"
    assert service_resp.plan_explanation is not None
    assert service_resp.plan_explanation.explanation_source == "deterministic_fallback"

    clarification_resp = recommend(
        _sample_catalog(),
        RecommendationRequest(program_id="demo", goal="không biết nên học gì kỳ tới"),
    )
    assert clarification_resp.intent.status == "needs_clarification"
    assert clarification_resp.plan_explanation is None


def test_me_recommendations_omitting_include_narrative_defaults_false(
    client, ready_context, monkeypatch  # noqa: F811
):
    from app.api import academic

    real_recommend = academic.recommend
    seen_requests: list[RecommendationRequest] = []

    def spy_recommend(catalog, req, *args, **kwargs):
        seen_requests.append(req)
        return real_recommend(catalog, req, *args, **kwargs)

    monkeypatch.setattr(academic, "recommend", spy_recommend)

    response = client.post(
        "/me/recommendations",
        json={
            "program_id": "khdl",
            "expected_revision": ready_context["revision"],
            "goal": "",
            "limit": 5,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    parsed = PlanExplanation.model_validate(payload["plan_explanation"])
    assert parsed.explanation_source == "deterministic_fallback"
    assert len(seen_requests) == 1
    assert seen_requests[0].include_narrative is False


def test_me_recommendations_forwards_include_narrative_true(
    client, ready_context, monkeypatch  # noqa: F811
):
    from app.api import academic

    real_recommend = academic.recommend
    seen_requests: list[RecommendationRequest] = []

    def spy_recommend(catalog, req, *args, **kwargs):
        seen_requests.append(req)
        return real_recommend(catalog, req, *args, **kwargs)

    monkeypatch.setattr(academic, "recommend", spy_recommend)

    response = client.post(
        "/me/recommendations",
        json={
            "program_id": "khdl",
            "expected_revision": ready_context["revision"],
            "goal": "",
            "limit": 5,
            "include_narrative": True,
        },
    )
    assert response.status_code == 200, response.text
    assert len(seen_requests) == 1
    assert seen_requests[0].include_narrative is True


@pytest.mark.parametrize(
    "extra_payload",
    [
        {"include_narrative": "yes"},
        {"include_narrative": 1},
        {"unknown_extra_field": True},
    ],
)
def test_me_recommendations_rejects_invalid_include_narrative_and_extra_fields(
    client, ready_context, extra_payload  # noqa: F811
):
    response = client.post(
        "/me/recommendations",
        json={
            "program_id": "khdl",
            "expected_revision": ready_context["revision"],
            **extra_payload,
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "invalid_academic_request"
