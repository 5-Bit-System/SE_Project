"""Pinned parent-rank RRF and V5 comparators over canonical scoped evidence."""
from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass

from app.hus.rag_loader import HUSRAGData, RAGDataError
from app.hus.retrieval import COURSE_CODE, HUSRAGRetriever, RetrievalHit, _tokens
from app.hus.vector_contract import digest_json, encoded
from app.hus.vector_query import VectorQueryError, VectorTrace, _canonical_signature

LOGGER = logging.getLogger(__name__)
MODEL_REVISION = '614241f622f53c4eeff9890bdc4f31cfecc418b3'


@dataclass(frozen=True)
class HybridPolicy:
    schema_version: str = 'hus-hybrid-policy-5.0'
    lexical_k: int = 20
    vector_passage_k: int = 20
    rrf_constant: int = 60
    final_k: int = 5
    lexical_weight: int = 1
    vector_weight: int = 1
    rank_basis: str = 'one_based_compact_parent_after_dedup'
    tie_break: str = 'canonical_parent_id'

    @property
    def sha256(self) -> str:
        return digest_json(asdict(self))


POLICY = HybridPolicy()


@dataclass(frozen=True)
class ParentRank:
    parent_id: str
    rank: int
    raw_score: float


@dataclass(frozen=True)
class FusedParent:
    parent_id: str
    lexical_rank: int | None
    vector_rank: int | None
    rrf_score: float


@dataclass(frozen=True)
class HybridTrace:
    requested_mode: str
    actual_mode: str
    release_id: str
    release_sha256: str
    filter_json: str
    policy_json: str
    policy_sha256: str
    lexical: tuple[ParentRank, ...] = ()
    vector: tuple[ParentRank, ...] = ()
    vector_trace: VectorTrace | None = None
    candidate_union: tuple[str, ...] = ()
    fused: tuple[FusedParent, ...] = ()
    final_top5: tuple[str, ...] = ()
    fallback_reason: str | None = None
    declared_model_revision: str = MODEL_REVISION


@dataclass(frozen=True)
class HybridSearchResult:
    hits: tuple[RetrievalHit, ...]
    trace: HybridTrace


def _unique(hits):
    seen = {}
    for hit in hits:
        pid = hit.chunk.chunk_id
        if pid in seen and encoded(asdict(seen[pid].chunk)) != encoded(asdict(hit.chunk)):
            raise RAGDataError('Conflicting canonical parent identity')
        seen.setdefault(pid, hit)
    return tuple(seen.values())


def _ranks(hits):
    return tuple(ParentRank(h.chunk.chunk_id, i, h.score) for i, h in enumerate(_unique(hits), 1))


def _fusion(lexical, vector):
    lex = {r.parent_id: r.rank for r in _ranks(lexical)}
    vec = {r.parent_id: r.rank for r in _ranks(vector)}
    rows = [FusedParent(pid, lex.get(pid), vec.get(pid),
                       (1 / (60 + lex[pid]) if pid in lex else 0)
                       + (1 / (60 + vec[pid]) if pid in vec else 0)) for pid in lex.keys() | vec.keys()]
    return tuple(sorted(rows, key=lambda r: (-r.rrf_score, r.parent_id)))


def rrf_fuse(lexical, vector) -> tuple[RetrievalHit, ...]:
    unique = _unique((*lexical, *vector))
    chunks = {h.chunk.chunk_id: h.chunk for h in unique}
    return tuple(RetrievalHit(chunks[r.parent_id], r.rrf_score, ()) for r in _fusion(lexical, vector))


class HUSHybridRetriever:
    """Hybrid service adapter; mode also selects budget-matched V5 comparators."""

    def __init__(self, data: HUSRAGData, *, vector=None, lexical=None, mode='hybrid'):
        if mode not in {'lexical', 'vector', 'hybrid'} or (mode != 'lexical' and vector is None):
            raise ValueError('V5 requires a valid mode and a vector leg for vector/hybrid')
        self._data = data
        self._lexical = lexical if lexical is not None else HUSRAGRetriever(data)
        self._vector = vector
        self._mode = mode
        self._signature = _canonical_signature(data)

    def _check_canonical(self):
        if _canonical_signature(self._data) != self._signature:
            raise RAGDataError('The canonical snapshot changed; reload before querying')

    @staticmethod
    def _validate(hits, allowed):
        if len(hits) > 20:
            raise RAGDataError('Leg exceeded pinned candidate budget')
        for hit in hits:
            if (hit.chunk.chunk_id not in allowed or type(hit.score) not in {int, float}
                    or not math.isfinite(hit.score)
                    or encoded(asdict(hit.chunk)) != encoded(asdict(allowed[hit.chunk.chunk_id]))):
                raise RAGDataError('Leg returned evidence outside canonical scope')
        return _unique(hits)

    def search(self, query, **kwargs):
        result = self.search_with_trace(query, **kwargs)
        LOGGER.info('hus_hybrid_retrieval', extra={'hus_retrieval': asdict(result.trace)})
        return result.hits

    def search_with_trace(self, query: str, *, dataset: str, major: str,
                          version: str | None = None, course_code: str | None = None,
                          field: str | None = None, program_variant: str | None = None,
                          top_k: int = 5, allow_generated: bool = False) -> HybridSearchResult:
        if not isinstance(query, str) or type(top_k) is not int or top_k != POLICY.final_k:
            raise RAGDataError('V5 requires a string query and pinned final top_k=5')
        self._check_canonical()
        scope = dict(dataset=dataset, major=major, version=version, course_code=course_code,
                     field=field, program_variant=program_variant, allow_generated=allow_generated)
        candidates = self._data.chunks(**scope)
        codes = {t.upper() for t in _tokens(query) if COURSE_CODE.fullmatch(t)}
        allowed = {c.chunk_id: c for c in candidates if not codes or c.metadata.get('course_code') in codes}
        lex, vec, fused, hits, vtrace, reason = (), (), (), (), None, None
        actual = self._mode
        if allowed and query.strip() and not (dataset == 'f3' and not allow_generated):
            if self._mode in {'lexical', 'hybrid'}:
                lex = self._validate(self._lexical.search(query, **scope, top_k=20), allowed)
            if self._mode in {'vector', 'hybrid'}:
                try:
                    vresult = self._vector.search_with_trace(query, **scope, top_k=20)
                    vtrace = vresult.trace
                    reason = vtrace.fallback_reason
                    if vtrace.mode_used != 'vector':
                        reason = reason or 'vector_unavailable'
                except RAGDataError:
                    raise
                except Exception as exc:
                    reason = exc.reason if isinstance(exc, VectorQueryError) else 'vector_runtime_error'
                    vtrace = VectorTrace(mode_used='lexical', fallback_reason=reason)
                if reason:
                    actual = 'lexical'
                    if self._mode == 'vector':
                        lex = self._validate(self._lexical.search(query, **scope, top_k=20), allowed)
                else:
                    vec = self._validate(vresult.hits, allowed)
            if actual == 'hybrid':
                fused = _fusion(lex, vec)
                hits = rrf_fuse(lex, vec)[:5]
            else:
                hits = (lex if actual == 'lexical' else vec)[:5]
        self._check_canonical()
        release = self._data.release_identity
        trace = HybridTrace(self._mode, actual, release['release_id'], release['release_sha256'],
            encoded(scope).decode(), encoded(asdict(POLICY)).decode(), POLICY.sha256,
            _ranks(lex), _ranks(vec), vtrace,
            tuple(sorted({h.chunk.chunk_id for h in (*lex, *vec)})), fused,
            tuple(h.chunk.chunk_id for h in hits), reason)
        return HybridSearchResult(hits, trace)
