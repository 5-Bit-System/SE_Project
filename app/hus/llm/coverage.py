"""Conservative lexical retention of every source unit, not entailment proof."""

import re
import unicodedata
from dataclasses import dataclass

from .client import HUSLLMError

_BOUNDARY = re.compile(r'[.!?;](?=\s|$)|\r?\n+')


@dataclass(frozen=True)
class EvidenceUnit:
    start: int
    end: int
    text: str


def source_units(quote: str) -> tuple[EvidenceUnit, ...]:
    """Split at deterministic textual boundaries; preserve every nonspace span.

    These are coverage units, not a claim of semantic proposition extraction.
    Abbreviations/soft wraps may create small units; none of their words is dropped.
    """
    units = []
    start = 0
    ends = [match.end() for match in _BOUNDARY.finditer(quote)]
    for end in [*ends, len(quote)]:
        left = start
        while left < end and quote[left].isspace():
            left += 1
        right = end
        while right > left and quote[right - 1].isspace():
            right -= 1
        if left < right:
            units.append(EvidenceUnit(left, right, quote[left:right]))
        start = end
    return tuple(units)


def _tokens(text: str) -> tuple[str, ...]:
    # Preserve accents, negations, conditions and function words. No stopword,
    # synonym or topic-specific rule can silently waive a source idea.
    return tuple(re.findall(r'\w+', unicodedata.normalize('NFKC', text).casefold()))


def _retained(required: tuple[str, ...], text: tuple[str, ...]) -> bool:
    remaining = iter(text)
    return all(any(token == wanted for token in remaining) for wanted in required)


def require_qualitative_coverage(sources: dict, points: list[tuple[str, str, str]]) -> None:
    """Every unit needs actual displayed words plus a supporting full-unit anchor.

    A point can cover multiple units, but a different citation's words/anchor,
    a declared coverage list, or a full anchor without corresponding text cannot
    supply missing content. Valid synonyms/reordered paraphrases may fall back.
    """
    candidates = {}
    for citation_id, text, anchor in points:
        candidates.setdefault(citation_id, []).append((_tokens(text), text, anchor))
    for citation_id, source in sources.items():
        for unit in source_units(source['quote']):
            required = _tokens(unit.text)
            covered = any(unit.text in anchor and (
                _retained(required, tokens) if required else unit.text in text)
                for tokens, text, anchor in candidates.get(citation_id, []))
            if not covered:
                raise HUSLLMError('evidence_coverage')
