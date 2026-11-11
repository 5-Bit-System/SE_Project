"""RRF uses parent ranks and verified vector success, never raw score addition."""
import importlib
from dataclasses import FrozenInstanceError, replace
from types import SimpleNamespace

import pytest

from app.hus.rag_loader import HUSRAGData, RAGDataError
from app.hus.retrieval import RetrievalHit
from app.hus.vector_query import VectorSearchResult, VectorTrace


def module():
    return importlib.import_module('app.hus.hybrid_retrieval')


@pytest.fixture(scope='module')
def canonical():
    return HUSRAGData.load_current()


@pytest.fixture
def boundary(canonical):
    chunks = canonical.chunks('f1', major='data_science', field='careers')
    assert len(chunks) >= 3
    calls = []
    lexical = [RetrievalHit(c, float(100 - i), ()) for i, c in enumerate(chunks[:3])]
    vector = [RetrievalHit(c, 0.9 - i / 10, ()) for i, c in enumerate(reversed(chunks[:3]))]
    state = {'lexical': lexical, 'vector': vector, 'reason': None}

    def bm25(query, **kwargs):
        calls.append(('lexical', kwargs))
        return tuple(state['lexical'])

    def chroma(query, **kwargs):
        calls.append(('vector', kwargs))
        trace = VectorTrace(mode_used='lexical' if state['reason'] else 'vector',
                            fallback_reason=state['reason'], index_id='pinned',
                            passage_ids=tuple(h.chunk.chunk_id + '#p000' for h in state['vector']))
        return VectorSearchResult(tuple(state['vector']), trace)

    return SimpleNamespace(data=canonical, lexical=SimpleNamespace(search=bm25),
                           vector=SimpleNamespace(search_with_trace=chroma), state=state,
                           calls=calls, options=dict(dataset='f1', major='data_science', field='careers'))


def adapter(b, mode='hybrid'):
    return module().HUSHybridRetriever(b.data, vector=b.vector, lexical=b.lexical, mode=mode)


def test_policy_is_pinned_immutable_and_hashable():
    p = module().POLICY
    assert (p.lexical_k, p.vector_passage_k, p.rrf_constant, p.final_k) == (20, 20, 60, 5)
    assert len(p.sha256) == 64
    with pytest.raises(FrozenInstanceError):
        p.rrf_constant = 9


def test_rrf_uses_rank_after_dedup_not_raw_scores(boundary):
    b = boundary
    a, c, d = b.state['lexical']
    hits = module().rrf_fuse([a, a, c], [replace(d, score=-0.9), replace(c, score=9999.0)])
    assert hits[0].chunk.chunk_id == c.chunk.chunk_id
    assert hits[0].score == pytest.approx(2 / 62)
    assert hits[1].score == hits[2].score == pytest.approx(1 / 61)
    assert [h.chunk.chunk_id for h in hits[1:]] == sorted([a.chunk.chunk_id, d.chunk.chunk_id])


def test_both_legs_receive_top20_and_identical_scope_before_fusion(boundary):
    b = boundary
    result = adapter(b).search_with_trace('nghề nghiệp', **b.options)
    assert [call[1]['top_k'] for call in b.calls] == [20, 20]
    assert b.calls[0][1] == b.calls[1][1]
    trace = result.trace
    assert trace.actual_mode == trace.requested_mode == 'hybrid'
    assert len(trace.candidate_union) == 3 and len(trace.final_top5) == 3
    assert trace.final_top5 == tuple(h.chunk.chunk_id for h in result.hits)
    assert trace.policy_sha256 == module().POLICY.sha256
    assert len(trace.lexical) == len(trace.vector) == 3
    assert all(row.rrf_score > 0 and row.lexical_rank and row.vector_rank for row in trace.fused)


def test_vector_fallback_never_votes_twice(boundary):
    b = boundary
    b.state.update(reason='index_missing', vector=list(reversed(b.state['lexical'])))
    result = adapter(b).search_with_trace('nghề nghiệp', **b.options)
    assert result.hits == tuple(b.state['lexical'])
    assert result.trace.actual_mode == 'lexical' and result.trace.fallback_reason == 'index_missing'
    assert result.trace.vector == () and result.trace.fused == ()
    assert result.hits[0].score == 100.0


@pytest.mark.parametrize('mode', ['lexical', 'vector'])
def test_comparator_budget_is20_to5_and_preserves_leg_order(boundary, mode):
    b = boundary
    result = adapter(b, mode).search_with_trace('nghề nghiệp', **b.options)
    assert len(b.calls) == 1 and b.calls[0][0] == mode and b.calls[0][1]['top_k'] == 20
    assert result.hits == tuple(b.state[mode])
    assert result.trace.actual_mode == mode and not result.trace.fused


def test_vector_comparator_fallback_is_labelled_lexical(boundary):
    b = boundary
    b.state['reason'] = 'query_token_budget'
    result = adapter(b, 'vector').search_with_trace('nghề nghiệp', **b.options)
    assert result.trace.actual_mode == 'lexical'
    assert result.hits == tuple(b.state['lexical']) and not result.trace.vector


def test_successful_empty_vector_is_empty_leg_not_failure(boundary):
    b = boundary
    b.state['vector'] = []
    result = adapter(b).search_with_trace('nghề nghiệp', **b.options)
    assert result.trace.actual_mode == 'hybrid' and not result.trace.fallback_reason
    assert result.hits[0].score == pytest.approx(1 / 61)


def test_wrong_scope_from_leg_fails_closed(boundary):
    b = boundary
    b.state['lexical'][0] = replace(b.state['lexical'][0],
                                   chunk=replace(b.state['lexical'][0].chunk, version='foreign'))
    with pytest.raises(RAGDataError):
        adapter(b).search('nghề nghiệp', **b.options)


def test_canonical_error_is_not_downgraded_to_fallback(boundary):
    b = boundary
    def broken(*args, **kwargs):
        raise RAGDataError('canonical invalid')
    b.vector.search_with_trace = broken
    with pytest.raises(RAGDataError):
        adapter(b).search('nghề nghiệp', **b.options)


def test_opt_out_blocks_both_legs_before_any_query(boundary):
    b = boundary
    result = adapter(b).search_with_trace('nội dung', dataset='f3', major='data_science')
    assert not result.hits and not b.calls


def test_candidate_union_is_not_truncated_to_final5(canonical):
    chunks = canonical.chunks('f3', major='data_science', allow_generated=True)
    a = [RetrievalHit(c, 30.0 - i, ()) for i, c in enumerate(chunks[:20])]
    v = [RetrievalHit(c, 0.99 - i / 100, ()) for i, c in enumerate(chunks[20:40])]
    result = module().HUSHybridRetriever(canonical, lexical=SimpleNamespace(search=lambda *a_, **kw: tuple(a)),
        vector=SimpleNamespace(search_with_trace=lambda *a_, **kw: VectorSearchResult(tuple(v), VectorTrace(index_id='pin'))))
    outcome = result.search_with_trace('nội dung', dataset='f3', major='data_science', allow_generated=True)
    assert len(outcome.trace.candidate_union) == len(outcome.trace.fused) == 40
    assert len(outcome.hits) == len(outcome.trace.final_top5) == 5


def test_invalid_top_k_does_not_change_pinned_policy(boundary):
    with pytest.raises(ValueError):
        adapter(boundary).search('nghề nghiệp', **boundary.options, top_k=20)


def test_trace_is_frozen_and_independent_across_calls(boundary):
    from concurrent.futures import ThreadPoolExecutor
    b = boundary
    r = adapter(b)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda q: r.search_with_trace(q, **b.options), ['nghề nghiệp', 'công việc']))
    assert results[0].trace is not results[1].trace
    with pytest.raises(FrozenInstanceError):
        results[0].trace.actual_mode = 'wrong'
