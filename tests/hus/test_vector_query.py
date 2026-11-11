"""V4 filters before top-k and never treats index text as citation evidence."""
import importlib
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest

from app.hus.rag_loader import RAGDataError
from app.hus.retrieval import HUSRAGRetriever
from app.hus.vector_contract import ROOT
from app.hus.vector_index import index_metadata


@pytest.fixture(scope='module')
def canonical(historical_v3_data):
    import json

    data = historical_v3_data
    rows = [json.loads(line) for line in
            (ROOT / 'data/hus/vector_passages/e5_small_v2_20261105/passages.jsonl').read_bytes().splitlines()]
    return data, rows


@pytest.fixture
def boundary(canonical):
    data, rows = canonical
    row = deepcopy(next(r for r in rows if r['metadata']['family'] == 'f1'))
    meta = row['metadata']
    calls = []
    result = {'ids': [[row['passage_id']]], 'distances': [[0.12]],
              'metadatas': [[index_metadata(row)]], 'documents': [[None]]}

    def query(question, *, where, top_k):
        calls.append((question, where, top_k))
        return deepcopy(result)

    runtime = SimpleNamespace(index_id='pinned-index', rows={row['passage_id']: row}, query=query)
    options = dict(dataset='f1', major=meta['major'], version=meta['version'],
                   field=meta['field'], top_k=5)
    return SimpleNamespace(data=data, rows=rows, row=row, runtime=runtime,
                           options=options, calls=calls, result=result)


def retriever(b, factory=None):
    cls = importlib.import_module('app.hus.vector_query').HUSVectorRetriever
    return cls(b.data, runtime_factory=factory or (lambda: b.runtime))


def test_where_contains_canonical_selection_and_scope_before_query(boundary):
    b = boundary
    result = retriever(b).search_with_trace('nghề nghiệp', **b.options)
    where = b.calls[0][1]['$and']
    assert {'family': 'f1'} in where and {'major': b.options['major']} in where
    assert {'version': b.options['version']} in where and {'field': b.options['field']} in where
    assert {'review_status': {'$in': ['include', 'include_markdown']}} in where
    assert {'ai_opt_in_required': False} in where
    assert {'release_sha256': b.data.release_identity['release_sha256']} in where
    parents = next(item['parent_id']['$in'] for item in where if 'parent_id' in item)
    assert b.row['parent_id'] in parents
    assert result.trace.mode_used == 'vector' and result.trace.fallback_reason is None
    assert result.hits[0].chunk.chunk_id == b.row['parent_id']
    assert result.hits[0].chunk.text != 'index supplied quote'
    assert result.trace.passage_ids == (b.row['passage_id'],)


def test_variant_filter_is_applied_before_query(boundary):
    b = boundary
    row = next(r for r in b.rows if r['metadata']['family'] == 'f3')
    meta = row['metadata']
    variant = meta['variant']
    b.runtime.rows = {row['passage_id']: row}
    b.result.update(ids=[[row['passage_id']]], metadatas=[[index_metadata(row)]])
    result = retriever(b).search_with_trace('nội dung', dataset='f3', major=meta['major'],
        course_code=meta['course_code'], version=meta['version'], field=meta['field'],
        program_variant=variant, allow_generated=True)
    assert {'variant': variant} in b.calls[0][1]['$and']
    assert {'content_origin': 'generated'} in b.calls[0][1]['$and']
    assert {'review_status': 'needs_review'} in b.calls[0][1]['$and']
    assert {'ai_opt_in_required': True} in b.calls[0][1]['$and']
    assert {'course_code': meta['course_code']} in b.calls[0][1]['$and']
    assert result.trace.mode_used == 'vector' and result.hits


def test_f3_without_opt_in_never_constructs_runtime(boundary):
    b = boundary
    def forbidden():
        pytest.fail('F3 must be blocked before optional runtime')
    result = retriever(b, forbidden).search_with_trace('nội dung', dataset='f3', major='data_science')
    assert result.hits == () and result.trace.fallback_reason is None


@pytest.mark.parametrize('fault', ['id', 'scope', 'hash', 'bool_type', 'nan', 'inf', 'length',
                                  'duplicate', 'document', 'missing_distances', 'negative_distance'])
def test_entire_bad_result_falls_back_to_same_scoped_bm25(boundary, fault):
    b = boundary
    if fault == 'id':
        b.result['ids'][0][0] = 'forged'
    elif fault == 'scope':
        b.result['metadatas'][0][0]['major'] = 'foreign'
    elif fault == 'hash':
        b.result['metadatas'][0][0]['parent_body_sha256'] = '0' * 64
    elif fault == 'bool_type':
        b.result['metadatas'][0][0]['ai_opt_in_required'] = 0
    elif fault in {'nan', 'inf'}:
        b.result['distances'][0][0] = float(fault)
    elif fault == 'length':
        b.result['distances'][0].clear()
    elif fault == 'duplicate':
        for value in b.result.values():
            value[0] *= 2
    elif fault == 'document':
        b.result['documents'][0][0] = 'index supplied quote'
    elif fault == 'missing_distances':
        del b.result['distances']
    else:
        b.result['distances'][0][0] = -2.0
    question = 'nghề nghiệp việc làm'
    result = retriever(b).search_with_trace(question, **b.options)
    assert result.trace.mode_used == 'lexical' and result.trace.fallback_reason == 'index_result_invalid'
    assert result.hits == HUSRAGRetriever(b.data).search(question, **b.options)


@pytest.mark.parametrize('reason', ['query_token_budget', 'index_missing', 'index_identity',
                                    'model_unavailable', 'vector_runtime_error'])
def test_stable_fallback_reason_is_per_call(boundary, reason):
    b = boundary
    m = importlib.import_module('app.hus.vector_query')
    def unavailable():
        raise m.VectorQueryError(reason)
    result = retriever(b, unavailable).search_with_trace('nghề nghiệp', **b.options)
    assert result.trace.fallback_reason == reason and result.trace.passage_ids == ()
    with pytest.raises((AttributeError, TypeError)):
        result.trace.mode_used = 'vector'


def test_runtime_unexpected_error_falls_back_without_logging_question(boundary, caplog):
    b = boundary
    def broken(*args, **kwargs):
        raise RuntimeError('secret details must not appear in trace')
    b.runtime.query = broken
    result = retriever(b).search_with_trace('private-question', **b.options)
    assert result.trace.fallback_reason == 'vector_runtime_error'
    assert 'private-question' not in caplog.text and 'secret details' not in caplog.text


def test_successful_empty_query_does_not_trigger_lexical_fallback(boundary):
    b = boundary
    for value in b.result.values():
        value[0].clear()
    result = retriever(b).search_with_trace('nghề nghiệp', **b.options)
    assert result.hits == () and result.trace.mode_used == 'vector'


def test_duplicate_parent_passages_produce_one_canonical_hit(boundary):
    b = boundary
    siblings = [r for r in b.rows if r['parent_id'] == '235a29b3d7972cb0f9de66bf06d58bff']
    b.runtime.rows = {r['passage_id']: r for r in siblings}
    b.result.update(ids=[[r['passage_id'] for r in siblings]], distances=[[0.2, 0.1]],
                    metadatas=[[index_metadata(r) for r in siblings]], documents=[[None, None]])
    meta = siblings[0]['metadata']
    result = retriever(b).search_with_trace('nghề nghiệp', dataset='f1', major=meta['major'],
                                          version=meta['version'], field=meta['field'])
    assert len(result.hits) == 1 and result.hits[0].score == pytest.approx(0.9)
    assert result.hits[0].chunk.chunk_id == siblings[0]['parent_id']


def test_query_code_cannot_leak_other_courses(boundary):
    b = boundary
    result = retriever(b).search_with_trace('MAT9999 nội dung', dataset='f3', major='data_science',
                                          allow_generated=True)
    assert result.hits == () and not b.calls


def test_passage_from_another_edition_cannot_survive_post_query_guard(boundary):
    b = boundary
    other = next(r for r in b.rows if r['metadata']['family'] == 'f1'
                 and r['metadata']['version'] != b.options['version'])
    b.runtime.rows[other['passage_id']] = other
    b.result.update(ids=[[other['passage_id']]], metadatas=[[index_metadata(other)]])
    result = retriever(b).search_with_trace('nghề nghiệp', **b.options)
    assert result.trace.fallback_reason == 'index_result_invalid'
    assert all(h.chunk.version == b.options['version'] for h in result.hits)


def test_concurrent_queries_have_independent_trace_and_one_runtime(boundary):
    from concurrent.futures import ThreadPoolExecutor

    b = boundary
    m = importlib.import_module('app.hus.vector_query')
    created = []
    def factory():
        created.append(True)
        return b.runtime
    def query(question, **kwargs):
        if question == 'fail':
            raise m.VectorQueryError('query_token_budget')
        return deepcopy(b.result)
    b.runtime.query = query
    r = retriever(b, factory)
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda question: r.search_with_trace(question, **b.options),
                                     ['pass', 'fail']))
    assert len(created) == 1
    assert outcomes[0].trace.mode_used == 'vector'
    assert outcomes[1].trace.mode_used == 'lexical'
    assert outcomes[0].trace.passage_ids and not outcomes[1].trace.passage_ids


def test_canonical_change_fails_closed_before_runtime_or_fallback(boundary):
    b = boundary
    b.data = deepcopy(b.data)
    r = retriever(b)
    family = b.row['metadata']['family']
    chunks = b.data._chunks[family]
    b.data._chunks[family] = tuple(replace(c, text=c.text + 'tampered') for c in chunks)
    with pytest.raises(RAGDataError, match='canonical'):
        r.search('nghề nghiệp', **b.options)
    assert not b.calls


def test_canonical_error_during_runtime_is_not_swallowed(boundary):
    b = boundary
    def broken(*args, **kwargs):
        raise RAGDataError('canonical invalid')
    b.runtime.query = broken
    with pytest.raises(RAGDataError):
        retriever(b).search('nghề nghiệp', **b.options)


@pytest.mark.parametrize('options', [{'top_k': True}, {'top_k': 0}, {'allow_generated': 1},
                                   {'dataset': 'f2'}, {'major': 'foreign'}])
def test_invalid_input_does_not_become_fallback(boundary, options):
    b = boundary
    with pytest.raises((ValueError, RAGDataError)):
        retriever(b).search('nghề nghiệp', **(b.options | options))
    assert not b.calls
