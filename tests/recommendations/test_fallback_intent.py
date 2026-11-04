"""Regression examples for deterministic fallback, not model accuracy tests."""

import pytest

from app.recommendation.feature_extractor import CatalogFeatureExtractor
from app.recommendation.preference import extract_structured_preference
from tests.recommendations.test_recommendations import sample_catalog


@pytest.mark.parametrize(("message", "credits", "count"), [
    ("Tôi không muốn 12 tín chỉ, chỉ 9 tín chỉ thôi", 9, None),
    ("Không quá 12 tín chỉ và 4 môn", 12, 4),
    ("No more than 9 credits and 3 courses", 9, 3),
    ("Tôi không muốn 4 môn, chỉ 3 môn", None, 3),
    ("9 tín chỉ, đổi thành 12 tín chỉ", 12, None),
    ("12 tín chỉ, đổi thành 99 tín chỉ", None, None),
    ("Tôi muốn 112 tín chỉ", None, None),
    ("Tôi muốn ít nhất 9 tín chỉ", None, None),
    ("Tối đa 12 tín chỉ, tối đa 9 tín chỉ", 9, None),
])
def test_numeric_limits(message, credits, count):
    result = extract_structured_preference(message)
    assert result.target_credits == credits
    assert result.target_course_count == count


@pytest.mark.parametrize(("message", "expected"), [
    ("Tôi không muốn môn tự chọn", None),
    ("Không chọn môn bắt buộc", None),
    ("Avoid elective courses", None),
    ("Tôi không muốn môn tự chọn, ưu tiên môn bắt buộc", "required"),
    ("Tôi muốn môn tự chọn", "elective"),
])
def test_negated_course_type(message, expected):
    assert extract_structured_preference(message).course_type == expected


@pytest.mark.parametrize("message", [
    "Tôi muốn học thực hành", "Tôi muốn làm bài tập", "Tôi không muốn làm kỹ sư phần mềm",
])
def test_study_request_is_not_a_career_goal(message):
    assert extract_structured_preference(message).career_goal is None


def test_explicit_career_intent_is_preserved_and_bounded():
    message = "Tôi muốn trở thành kỹ sư phần mềm"
    assert extract_structured_preference(message).career_goal == message
    assert len(extract_structured_preference(message + " a" * 200).career_goal) <= 200


def test_provider_failure_uses_corrected_fallback():
    def timeout(_):
        raise TimeoutError()

    result = CatalogFeatureExtractor(sample_catalog(), timeout).extract(
        "Tôi không muốn 12 tín chỉ, chỉ 9 tín chỉ thôi; không muốn môn tự chọn"
    )
    assert result.target_credits == 9
    assert result.course_type is None
    assert result.career_goal is None
