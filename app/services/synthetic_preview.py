"""Synthetic recommendation preview service for administrative simulation.

Allows administrators to simulate and inspect course recommendations, eligibility trees,
and prerequisite blocks with synthetic student profiles.
Strictly read-only and memory-only. Never touches student records or persists data.
"""

from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.catalog import load_catalog
from app.models import RecommendationRequest
from app.recommendation.llm import configured_adapters
from app.rules import evaluate_eligibility
from app.services.recommendation_service import recommend


class SyntheticPreviewRequest(BaseModel):
    """Synthetic input profile for administrative recommendation simulation."""

    program_id: str
    passed_course_codes: list[str] = Field(default_factory=list)
    failed_course_codes: list[str] = Field(default_factory=list)
    selected_track_id: str | None = None
    selected_graduation_path_id: str | None = None
    max_credits: int = Field(default=18, ge=1, le=35)
    goal: str = Field(default="", max_length=500)
    allow_unverified_preview: bool = Field(
        default=True,
        description="Cho phép xem trước giải thuật trên bản thảo chưa kiểm định",
    )

    model_config = {"extra": "allow"}

    @model_validator(mode="before")
    @classmethod
    def reject_student_identifiers(cls, data: Any) -> Any:
        if isinstance(data, dict):
            forbidden = {"student_id", "vnu_id", "user_id", "transcript_id", "mssv", "account_id"}
            present = forbidden.intersection(k.lower() for k in data.keys())
            if present:
                raise ValueError(
                    f"Student identifiers are not permitted in synthetic preview: {', '.join(present)}"
                )
        return data


def run_synthetic_recommendation_preview(req: SyntheticPreviewRequest) -> dict[str, Any]:
    """Execute recommendation engine against a synthetic profile without mutating state."""
    catalog = load_catalog(req.program_id)

    # 1. Evaluate deterministic eligibility on the synthetic profile
    eligibility = evaluate_eligibility(
        catalog,
        set(req.passed_course_codes),
        max_credits=req.max_credits,
        selected_track_id=req.selected_track_id,
        selected_graduation_path_id=req.selected_graduation_path_id,
        preview_unverified_metadata=req.allow_unverified_preview,
    )

    # 2. Run ranking and recommendation
    rec_req = RecommendationRequest(
        program_id=req.program_id,
        passed_course_codes=req.passed_course_codes,
        goal=req.goal,
        max_credits=req.max_credits,
        selected_track_id=req.selected_track_id,
        selected_graduation_path_id=req.selected_graduation_path_id,
    )
    pref_extractor, llm_ranker = configured_adapters()
    rec_response = recommend(
        catalog,
        rec_req,
        preference_extractor=pref_extractor,
        llm_ranker=llm_ranker,
        eligibility=eligibility,
    )

    is_unverified = catalog.program.catalog_status == "draft_unverified"
    warning = (
        "Chương trình đào tạo này đang ở trạng thái Bản thảo chưa kiểm định (draft_unverified). "
        "Các gợi ý học phần mang tính chất thử nghiệm nội bộ."
        if is_unverified
        else None
    )

    return {
        "is_simulated": True,
        "simulation_disclaimer": "Kết quả mô phỏng dựa trên hồ sơ giả định. Tuyệt đối không lưu trữ hoặc can thiệp học bạ thực tế.",
        "catalog": {
            "program_id": catalog.program.program_id,
            "name": catalog.program.name,
            "status": catalog.program.catalog_status,
            "is_unverified": is_unverified,
            "warning": warning,
        },
        "synthetic_profile": {
            "passed_count": len(req.passed_course_codes),
            "passed_courses": req.passed_course_codes,
            "failed_courses": req.failed_course_codes,
            "max_credits": req.max_credits,
            "selected_track_id": req.selected_track_id,
            "selected_graduation_path_id": req.selected_graduation_path_id,
        },
        "recommendations": [c.model_dump() for c in rec_response.recommendations],
        "eligible_courses": [c.model_dump() for c in eligibility.eligible_courses],
        "blocked_courses": [c.model_dump() for c in eligibility.blocked_courses],
        "total_eligible": len(eligibility.eligible_courses),
        "total_blocked": len(eligibility.blocked_courses),
    }
