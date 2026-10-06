from typing import Protocol

from app.models import Course


class Ranker(Protocol):
    def rank(self, candidates: list[Course], goal: str) -> list[str]:
        """Return course codes only; service validates every code."""


class KeywordRanker:
    """Deterministic baseline until an optional LLM ranker is configured."""

    def rank(self, candidates: list[Course], goal: str) -> list[str]:
        words = {word.casefold() for word in goal.split() if len(word) > 2}
        ordered = sorted(
            candidates,
            key=lambda course: (
                -sum(word in course.name.casefold() for word in words),
                course.code,
            ),
        )
        return [course.code for course in ordered]
