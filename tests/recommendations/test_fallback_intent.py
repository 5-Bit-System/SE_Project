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
