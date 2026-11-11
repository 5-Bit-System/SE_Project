"""Scoped vector adapter. Canonical evidence is authoritative; ML stays lazy."""
from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass
from threading import Lock
from typing import Callable

from app.hus.passages import parent_chunk
from app.hus.rag_loader import MAJOR_CODES, HUSRAGData, RAGDataError
from app.hus.retrieval import COURSE_CODE, HUSRAGRetriever, RetrievalHit, _tokens
from app.hus.vector_contract import digest_json, encoded
from app.hus.vector_index import index_metadata

LOGGER = logging.getLogger(__name__)


class VectorQueryError(Exception):
    """A vector-only failure with a stable, non-sensitive reason code."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class VectorTrace:
    mode_requested: str = 'vector'
    mode_used: str = 'vector'
    fallback_reason: str | None = None
    index_id: str | None = None
    filter_json: str | None = None
    passage_ids: tuple[str, ...] = ()
    parent_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class VectorSearchResult:
    hits: tuple[RetrievalHit, ...]
    trace: VectorTrace


def _canonical_signature(data: HUSRAGData) -> str:
    try:
        chunks = [asdict(c) for family in ('f1', 'f3') for major in sorted(MAJOR_CODES.values())
                  for c in data.chunks(family, major=major, allow_generated=True)]
        return digest_json({'release': data.release_identity, 'chunks': chunks})
    except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
        raise RAGDataError('Invalid canonical snapshot') from exc


class HUSVectorRetriever:
    def __init__(self, data: HUSRAGData, *, runtime_factory: Callable):
        self._data = data
        self._lexical = HUSRAGRetriever(data)
        self._signature = _canonical_signature(data)
        self._factory = runtime_factory
        self._runtime = None
        self._runtime_lock = Lock()

    def _check_canonical(self):
        if _canonical_signature(self._data) != self._signature:
            raise RAGDataError('The canonical snapshot changed; reload before querying')

    def _get_runtime(self):
        with self._runtime_lock:
            if self._runtime is None:
                self._runtime = self._factory()
            return self._runtime

    def search(self, query: str, **kwargs) -> tuple[RetrievalHit, ...]:
        result = self.search_with_trace(query, **kwargs)
        LOGGER.info('hus_retrieval', extra={'hus_retrieval': asdict(result.trace)})
        return result.hits

    def search_with_trace(
        self, query: str, *, dataset: str, major: str, version: str | None = None,
        course_code: str | None = None, field: str | None = None,
        program_variant: str | None = None, top_k: int = 5, allow_generated: bool = False,
    ) -> VectorSearchResult:
        if not isinstance(query, str):
            raise RAGDataError('query must be a string')
        if type(top_k) is not int or not 1 <= top_k <= 50:
            raise RAGDataError('top_k must be an integer between 1 and 50')
        self._check_canonical()  # Outside the vector exception boundary.
        options = dict(dataset=dataset, major=major, version=version, course_code=course_code,
                       field=field, program_variant=program_variant, allow_generated=allow_generated)
        candidates = self._data.chunks(**options)
        codes = {term.upper() for term in _tokens(query) if COURSE_CODE.fullmatch(term)}
        candidates = tuple(c for c in candidates if not codes or c.metadata.get('course_code') in codes)
        # F3 requires opt-in even if an incorrectly labelled candidate were supplied.
        if (dataset == 'f3' and not allow_generated) or not candidates or not query.strip():
            return VectorSearchResult((), VectorTrace())
        for chunk in candidates:
            if (chunk.metadata.get('review_status') not in
                    ({'include', 'include_markdown'} if dataset == 'f1' else {'needs_review'})
                    or (dataset == 'f3' and chunk.metadata.get('content_origin') != 'generated')):
                raise RAGDataError('Invalid canonical selection review')
        allowed = {c.chunk_id: c for c in candidates}
        identity = self._data.release_identity
        filters = [{'family': dataset}, {'major': major},
                   {'release_id': identity['release_id']}, {'release_sha256': identity['release_sha256']},
                   {'ai_opt_in_required': dataset == 'f3'},
                   {'parent_id': {'$in': sorted(allowed)}}]
        filters.append({'review_status': {'$in': ['include', 'include_markdown']}}
                       if dataset == 'f1' else {'review_status': 'needs_review'})
        if dataset == 'f3':
            filters.append({'content_origin': 'generated'})
        for key, value in [('version', version), ('variant', program_variant),
                           ('course_code', course_code.strip().upper() if course_code else None),
                           ('field', field)]:
            if value is not None:
                filters.append({key: value})
        where = {'$and': filters}
        index_id, reason, hits, passage_ids = None, None, (), ()
        try:
            runtime = self._get_runtime()
            index_id = runtime.index_id
            raw = runtime.query(query, where=where, top_k=top_k)
            hits, passage_ids = self._resolve(raw, runtime.rows, allowed, top_k)
        except RAGDataError:
            raise
        except VectorQueryError as exc:
            reason = exc.reason
        except Exception:
            # Optional library errors cannot expose paths, query contents or secrets.
            reason = 'vector_runtime_error'
        self._check_canonical()  # Also guard mutation during a failed vector call.
        if reason:
            hits = self._lexical.search(query, **options, top_k=top_k)
        trace = VectorTrace(mode_used='lexical' if reason else 'vector', fallback_reason=reason,
                            index_id=index_id, filter_json=encoded(where).decode(),
                            passage_ids=passage_ids, parent_ids=tuple(h.chunk.chunk_id for h in hits))
        return VectorSearchResult(hits, trace)

    def _resolve(self, raw, rows, allowed, top_k):
        try:
            arrays = []
            for key in ('ids', 'distances', 'metadatas', 'documents'):
                value = raw[key]
                if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], list):
                    raise ValueError('Expected one query result')
                arrays.append(value[0])
            ids, distances, metadatas, documents = arrays
            if (len(ids) > top_k or any(len(v) != len(ids) for v in arrays)
                    or len(set(ids)) != len(ids)):
                raise ValueError('Invalid hit counts/duplicates')
            parents = {}
            for pid, distance, metadata, document in zip(*arrays, strict=True):
                if (type(pid) is not str or pid not in rows or type(distance) not in {int, float}
                        or not math.isfinite(distance) or not -1e-6 <= distance <= 2.000001
                        or document is not None):
                    raise ValueError('Invalid passage/distance/document')
                row = rows[pid]
                if (pid != row['passage_id'] or encoded(metadata) != encoded(index_metadata(row))
                        or row['parent_id'] not in allowed):
                    raise ValueError('Passage metadata or scope mismatch')
                canonical = allowed[row['parent_id']]
                resolved = parent_chunk(row, self._data)
                if encoded(asdict(canonical)) != encoded(asdict(resolved)):
                    raise ValueError('Parent identity mismatch')
                hit = RetrievalHit(canonical, 1.0 - distance, ())
                previous = parents.get(canonical.chunk_id)
                if previous is None or hit.score > previous.score:
                    parents[canonical.chunk_id] = hit
            return (tuple(sorted(parents.values(), key=lambda h: (-h.score, h.chunk.chunk_id))), tuple(ids))
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise VectorQueryError('index_result_invalid') from exc
