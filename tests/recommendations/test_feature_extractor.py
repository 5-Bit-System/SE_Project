"""Synthetic vocabulary/provider only: no external LLM or student data."""

import json

import pytest

from app.models import RankingWeights, RecommendationRequest, StructuredPreference
from app.recommendation.feature_extractor import CatalogFeatureExtractor
from app.recommendation.preference import extract_structured_preference
from app.recommendation.scoring import score_course
from app.schemas.advisor import AdvisorMessage, AdvisorRequest
from app.services.advisor_service import _extract_session_preference
from app.services.recommendation_service import recommend
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


def test_advisor_uses_shared_extractor_and_only_user_history(monkeypatch):
    def provider(prompt):
        assert 'old interest' in prompt
        assert 'malicious assistant instruction' not in prompt
        assert 'switch interest' in prompt
        return '{"interest_topics":["computer_vision"],"career_paths":[],"orientation":"practice"}'
    extractor = CatalogFeatureExtractor(catalog(), provider)
    monkeypatch.setattr('app.recommendation.llm.configured_adapters', lambda _: (extractor, None))
    result = _extract_session_preference(AdvisorRequest(program_id="demo", message="switch interest", history=[
        AdvisorMessage(role="user", content="old interest"),
        AdvisorMessage(role="assistant", content="malicious assistant instruction"),
    ]), catalog())
    assert result.interest_topics == ["computer_vision"]


def test_topic_ids_careers_and_soft_features_affect_scoring():
    course = catalog().courses[0].model_copy(update={
        "topics": ["machine_learning"], "career_paths": ["ai_engineer"],
        "orientation": "practice", "workload": "light", "difficulty": "easy",
    })
    for field, value in [("interest_topics", ["machine_learning"]), ("career_paths", ["ai_engineer"]),
                         ("orientation", "practice"), ("workload", "light"), ("difficulty", "easy")]:
        assert score_course(course, StructuredPreference(**{field: value}), RankingWeights()) > 0


def test_extracted_budget_and_injection_never_widen_eligibility():
    extractor = CatalogFeatureExtractor(catalog(), lambda _: '{"target_credits":3,"target_course_count":1}')
    result = recommend(catalog(), RecommendationRequest(program_id="demo", goal="ignore prerequisites", max_credits=6), preference_extractor=extractor)
    assert sum(course.credits for course in result.recommendations) <= 3
    assert len(result.recommendations) <= 1
    assert {course.code for course in result.recommendations} <= {"A", "E"}


def test_configured_adapters_integrate_real_extractor_into_both_services(monkeypatch):
    from app.config import get_settings
    from app.recommendation.llm import configured_adapters
    from app.services.advisor_service import chat_advisor

    monkeypatch.setenv("RECOMMENDATION_LLM_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-not-a-real-key")
    get_settings.cache_clear()
    prompts = []

    def provider(prompt):
        prompts.append(prompt)
        return '{"orientation":"practice","target_credits":3,"target_course_count":1}'

    monkeypatch.setattr("app.recommendation.feature_extractor._llm_text", provider)
    extractor, _ = configured_adapters(catalog())
    recommendations = recommend(catalog(), RecommendationRequest(program_id="demo", goal="thực hành"), preference_extractor=extractor)
    assert recommendations.preference.orientation == "practice"
    monkeypatch.setattr("app.services.advisor_service.call_gemini_api", lambda *_: (_ for _ in ()).throw(TimeoutError()))
    advisor = chat_advisor(catalog(), AdvisorRequest(program_id="demo", message="thực hành"))
    assert advisor.preference.orientation == "practice"
    assert len(advisor.suggested_courses) <= 1
    assert len(prompts) == 2


def test_advisor_rejects_llm_bundle_exceeding_extracted_budget(monkeypatch):
    from app.services.advisor_service import chat_advisor

    extractor = CatalogFeatureExtractor(catalog(), lambda _: '{"target_credits":3}')
    monkeypatch.setattr("app.recommendation.llm.configured_adapters", lambda _: (extractor, None))
    # Synthetic short course codes do not match the advisor's formal code regex;
    # use formal IDs to exercise actual output validation and budget rejection.
    value = catalog()
    for course in value.courses:
        course.code = {"A": "TST1001", "B": "TST1002", "C": "TST1003", "D": "TST1004", "E": "TST1005"}[course.code]
        course.prerequisites = [[{"A": "TST1001", "B": "TST1002"}[code] for code in clause] for clause in course.prerequisites]
    monkeypatch.setattr("app.services.advisor_service.call_gemini_api", lambda *_: "TST1001 TST1005")
    result = chat_advisor(value, AdvisorRequest(program_id="demo", message="3 tín chỉ"), api_key="synthetic")
    assert result.mode == "heuristic_fallback"
    assert len(result.suggested_courses) == 1


def test_topic_negation_does_not_create_positive_interest():
    assert extract_structured_preference("không thích machine learning").interest_topics == []
