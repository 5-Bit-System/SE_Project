from typing import Protocol

from app.models import Course, RankingWeights, StructuredPreference
from app.recommendation.preference import extract_structured_preference
from app.recommendation.scoring import score_course


class Ranker(Protocol):
    def rank(self, candidates: list[Course], goal: str) -> list[str]:
        """Return course codes only; service validates every code."""


class KeywordRanker:
    """Bộ xếp hạng deterministic dùng được khi không có LLM."""

    def rank(
        self,
        candidates: list[Course],
        goal: str,
        preference: StructuredPreference | None = None,
        weights: RankingWeights | None = None,
    ) -> list[str]:
        preference = preference or extract_structured_preference(goal)
        ordered = sorted(
            candidates,
            key=lambda course: (
                -score_course(course, preference, weights),
                course.code,
            ),
        )
        return [course.code for course in ordered]
