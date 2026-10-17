"""Typed metadata must remain visible to pre-existing ranking adapters."""

from app.models import Course, StructuredPreference
from app.recommendation.llm import LLMRanker
from app.recommendation.scoring import score_course


def test_typed_metadata_remains_visible_to_legacy_scoring_and_llm_payload():
    course = Course(code="DEMO101", name="Demo", credits=3, block="major", topics=["programming"])
    assert "topics" not in course.model_extra
    assert score_course(course, StructuredPreference(interest_topics=["programming"])) > 0
    received = []

    def provider(candidates, context):
        received.extend(candidates)
        return [course.code]

    assert LLMRanker(provider).rank([course], "") == ["DEMO101"]
    assert received[0]["metadata"]["topics"] == ["programming"]
