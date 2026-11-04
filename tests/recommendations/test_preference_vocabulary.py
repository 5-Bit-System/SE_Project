"""Shared intent vocabulary must not become invented course metadata."""

import json

import pytest

from app.recommendation.feature_extractor import CatalogFeatureExtractor, fallback_preference
from app.recommendation.scoring import score_course
from app.recommendation.vocabulary import metadata_preferences, preference_vocabulary
from tests.recommendations.test_recommendations import sample_catalog


@pytest.mark.parametrize("message", [
    "tôi muốn 1 kì liên quan đến phát triển phần mềm, có được không ?",
    "software development",
])
def test_software_intent_uses_metadata_id_without_mutating_catalog(message):
    catalog = sample_catalog()
    before = catalog.model_dump()

    def provider(prompt):
        assert "software_engineering" in prompt
        assert "phát triển phần mềm" in prompt
        assert message in prompt
        return '{"interest_topics":["software_engineering"]}'

    result = CatalogFeatureExtractor(catalog, provider).extract(message)
    assert result.interest_topics == ["software_engineering"]
    assert result.career_paths == []
    assert result.target_course_count is None
    assert metadata_preferences(result)["topics"] == ["software_engineering"]
    assert catalog.model_dump() == before


def test_fallback_normalizes_software_alias_and_negation():
    catalog = sample_catalog()
    assert fallback_preference("phát triển phần mềm", catalog).interest_topics == ["software_engineering"]
    assert fallback_preference("không thích phát triển phần mềm", catalog).interest_topics == []


def test_extensions_do_not_leak_across_programs():
    catalog = sample_catalog()
    catalog.vocabulary = {"topics": ["local_topic"]}
    assert "local_topic" in preference_vocabulary(catalog)["topics"]
    assert "local_topic" not in preference_vocabulary(sample_catalog())["topics"]
    result = CatalogFeatureExtractor(
        sample_catalog(), lambda _: '{"interest_topics":["local_topic"]}',
    ).extract("hello")
    assert result.interest_topics == []


def test_metadata_view_and_missing_metadata_do_not_manufacture_matches():
    catalog = sample_catalog()
    result = CatalogFeatureExtractor(catalog, lambda _: json.dumps({
        "interest_topics": ["software_engineering"], "course_type": "elective",
    })).extract("phát triển phần mềm")
    assert metadata_preferences(result)["requirement_type"] == "elective"
    # Isolate topic scoring from name/keyword and requirement-type scoring.
    from app.models import RankingWeights

    weights = RankingWeights(topic=1, career=0, keyword=0, course_type=0,
                             orientation=0, difficulty=0, workload=0)
    course = catalog.courses[0].model_copy(update={"topics": None, "name": "Unrelated course"})
    assert score_course(course, result, weights) == 0
    matching = course.model_copy(update={"topics": ["software_engineering"]})
    assert score_course(matching, result, weights) > 0
