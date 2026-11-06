"""Offline lexical retrieval over one packaged snapshot, filtered before scoring.

This retrieves evidence; a relevance score is not academic verification or an answer.
F2 remains an exact structured lookup on HUSRAGData rather than a ranked text corpus.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
from pathlib import Path
import re
import unicodedata

from app.hus.rag_loader import (
    ChunkDataset, DEFAULT_RAG_ROOT, HUSRAGData, RAGChunk, RAGDataError,
)


# Keep domain words (including 'hoc', 'may', 'toan') searchable. These are query glue.
STOP_WORDS = frozenset("a an the is are of and for to la gi nao nhung cac ve cua cho voi va hay "
                       "toi minh ban xin cho biet co the duoc khong trong o mot".split())
COURSE_CODE = re.compile(r"[a-z]{3}\d{4}[a-z]?")
FIELD_LABELS = {
    "introduction": "giới thiệu tổng quan",
    "careers": "nghề nghiệp việc làm",
    "further_study": "học tiếp sau đại học",
    "objectives": "mục tiêu chuẩn đầu ra",
    "content": "nội dung chủ đề",
    "suggested_assessment": "gợi ý đánh giá thi kiểm tra",
}


def _tokens(value: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFD", value.casefold()).replace("đ", "d")
    normalized = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return tuple(re.findall(r"[a-z0-9]+", normalized))


def _body(chunk: RAGChunk) -> str:
    if chunk.dataset == "f1":
        return chunk.metadata.get("source_quote", chunk.text)
    # Rank the actual field text rather than repeating the AI warning/course context.
    locator = chunk.metadata.get("locator", {})
    if locator.get("offset_scope") == "rendered_field_text_excluding_repeated_context":
        start, end = locator.get("start_char"), locator.get("end_char")
        if type(start) is int and type(end) is int and 0 <= start < end:
            size = end - start
            if size <= len(chunk.text):
                return chunk.text[-size:]
    warning = chunk.metadata.get("warning", "")
    return chunk.text.removeprefix(warning).lstrip()


def _terms(chunk: RAGChunk) -> Counter[str]:
    body = Counter(t for t in _tokens(_body(chunk)) if t not in STOP_WORDS)
    title = chunk.metadata.get("course_name") if chunk.dataset == "f3" else chunk.metadata.get("title")
    if title:
        body.update(t for t in _tokens(title) for _ in range(3) if t not in STOP_WORDS)
    if chunk.metadata.get("course_code"):
        body.update(_tokens(chunk.metadata["course_code"]))
    body.update(t for t in _tokens(FIELD_LABELS.get(chunk.metadata.get("field"), ""))
                if t not in STOP_WORDS)
    return body


@dataclass(frozen=True)
class RetrievalHit:
    chunk: RAGChunk
    score: float
    matched_terms: tuple[str, ...]


class HUSRAGRetriever:
    """BM25 keyword search, Vietnamese accent-insensitive, deterministic tie ordering.

    Only HUSRAGData is read. No directory scan, origin/qa read, embedding, external
    service or persisted index is involved. Reload the snapshot after data changes.
    """

    def __init__(self, data: HUSRAGData):
        self._data = data

    @classmethod
    def load(cls, root: Path = DEFAULT_RAG_ROOT, *, source: str = "current") -> HUSRAGRetriever:
        if source not in {"current", "legacy"}:
            raise RAGDataError("source must be current or legacy")
        data = HUSRAGData.load_current(root) if source == "current" else HUSRAGData.load(root)
        return cls(data)

    def search(
        self, query: str, *, dataset: ChunkDataset, major: str, version: str | None = None,
        course_code: str | None = None, field: str | None = None,
        program_variant: str | None = None, top_k: int = 5, allow_generated: bool = False,
    ) -> tuple[RetrievalHit, ...]:
        """Filter first, then rank positive keyword matches within that exact scope.

        An explicit version never matches 'unknown'; without one, versions remain
        separate in returned metadata. Course codes in the query restrict F3 even
        when a generic topic also matches. No matches return an empty tuple.
        """
        if not isinstance(query, str):
            raise RAGDataError("query must be a string")
        if type(top_k) is not int or not 1 <= top_k <= 50:
            raise RAGDataError("top_k must be an integer between 1 and 50")
        candidates = self._data.chunks(dataset, major=major, version=version,
                                       course_code=course_code, field=field,
                                       program_variant=program_variant, allow_generated=allow_generated)
        query_terms = set(_tokens(query)) - STOP_WORDS
        codes = {term.upper() for term in query_terms if COURSE_CODE.fullmatch(term)}
        if codes:
            candidates = tuple(c for c in candidates if c.metadata.get("course_code") in codes)
        if not candidates or not query_terms:
            return ()

        # Remove identical source slices within a scope before term statistics. This
        # does not collapse distinct courses/versions/variants or different source URLs.
        unique = {}
        for chunk in candidates:
            identity = (chunk.dataset, chunk.major, chunk.version,
                        chunk.metadata.get("program_variant"), chunk.metadata.get("course_code"),
                        chunk.metadata.get("field"), chunk.metadata.get("source_url"),
                        _body(chunk))
            unique.setdefault(identity, chunk)
        candidates = tuple(unique.values())
        documents = [_terms(c) for c in candidates]
        lengths = [sum(terms.values()) for terms in documents]
        average_length = sum(lengths) / len(lengths)
        if not average_length:
            return ()
        frequencies = Counter(term for terms in documents for term in query_terms if term in terms)
        hits = []
        for chunk, terms, length in zip(candidates, documents, lengths):
            matched = tuple(sorted(query_terms & terms.keys()))
            if not matched:
                continue
            # BM25: k1=1.2, b=0.75. Scores are local to this filtered candidate set.
            score = 0.0
            for term in matched:
                count = terms[term]
                idf = math.log1p((len(candidates) - frequencies[term] + 0.5) / (frequencies[term] + 0.5))
                score += idf * count * 2.2 / (count + 1.2 * (0.25 + 0.75 * length / average_length))
            hits.append(RetrievalHit(chunk, score, matched))
        return tuple(sorted(hits, key=lambda h: (-h.score, h.chunk.chunk_id))[:top_k])
