"""Synthetic feature extraction and metadata scoring; no external provider."""

import json

import pytest

from app.models import RankingWeights, StructuredPreference
from app.recommendation.feature_extractor import CatalogFeatureExtractor
from app.recommendation.preference import extract_structured_preference
from app.recommendation.scoring import score_course
from tests.recommendations.test_recommendations import sample_catalog


def catalog():
    value = sample_catalog()
    value.vocabulary = {"topics": ["machine_learning", "computer_vision"], "career_paths": ["ai_engineer"]}
    return value


@pytest.mark.parametrize("message", ["Computer Vision", "thị giác máy tính"])
def test_bilingual_prompt_and_catalog_labels(message):
    def provider(prompt):
        assert message in prompt
        assert "computer_vision" in prompt
        return json.dumps({"interest_topics": ["computer_vision"], "orientation": "practice"})
    result = CatalogFeatureExtractor(catalog(), provider).extract(message)
    assert result.interest_topics == ["computer_vision"]
    assert result.orientation == "practice"


@pytest.mark.parametrize("output", [
    'broken', '{"interest_topics":["invented"]}', '{"career_paths":["invented"]}',
    '{"target_credits":true}', '{"target_credits":"12"}', '{"target_credits":99}',
    '{"eligible_courses":["C"]}',
])
def test_invalid_provider_output_falls_back(output):
    result = CatalogFeatureExtractor(catalog(), lambda _: output).extract("thực hành 12 tín chỉ")
    assert result.orientation == "practice"
    assert result.target_credits == 12
    assert result.interest_topics == []


def test_timeout_and_empty_vocabulary_are_safe():
    def timeout(_):
        raise TimeoutError()
    result = CatalogFeatureExtractor(sample_catalog(), timeout).extract("machine learning")
    assert result.interest_topics == []
    result = CatalogFeatureExtractor(sample_catalog(), lambda _: '{"interest_topics":["machine_learning"]}').extract("học máy")
    assert result.interest_topics == []


def test_negation_and_invalid_numbers_in_fallback():
    result = extract_structured_preference("Tôi không thích môn khó, muốn 99 tín chỉ")
    assert result.difficulty is None
    assert result.target_credits is None


def test_topic_ids_careers_and_soft_features_affect_scoring():
    course = catalog().courses[0].model_copy(update={
        "topics": ["machine_learning"], "career_paths": ["ai_engineer"],
        "orientation": "practice", "workload": "light", "difficulty": "easy",
    })
    for field, value in [("interest_topics", ["machine_learning"]), ("career_paths", ["ai_engineer"]),
                         ("orientation", "practice"), ("workload", "light"), ("difficulty", "easy")]:
        assert score_course(course, StructuredPreference(**{field: value}), RankingWeights()) > 0


def test_topic_negation_does_not_create_positive_interest():
    assert extract_structured_preference("không thích machine learning").interest_topics == []
