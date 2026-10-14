"""Sinh explanation chỉ từ facts đã được backend kiểm tra."""

from app.models import Course, StructuredPreference
from app.recommendation.scoring import fit_reason


def build_grounded_explanation(
    course: Course,
    preference: StructuredPreference,
    eligibility_reasons: list[str],
    score: float,
) -> tuple[str, str]:
    fit = fit_reason(course, preference, score)
    eligibility = "; ".join(eligibility_reasons) if eligibility_reasons else "Đã qua kiểm tra eligibility của backend."
    reason = f"Đủ điều kiện: {eligibility} Phù hợp: {fit}"
    return reason, fit
