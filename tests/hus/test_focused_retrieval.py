"""Source parent restrictions are applied before both ranking legs/fallback."""
import json
from types import SimpleNamespace

import pytest

from app.hus.hybrid_retrieval import HUSHybridRetriever
from app.hus.rag_loader import RAGDataError
from app.hus.retrieval import HUSRAGRetriever, _body
from app.hus.vector_query import VectorSearchResult, VectorTrace
from tests.hus.test_vector_query import boundary, canonical, retriever  # noqa: F401


def test_vector_parent_filter_is_part_of_chroma_where(boundary):  # noqa: F811
    b = boundary
    pid = b.row['parent_id']
    result = retriever(b).search_with_trace('nghề nghiệp', **b.options, parent_ids=(pid,))
    assert next(x['parent_id']['$in'] for x in b.calls[0][1]['$and'] if 'parent_id' in x) == [pid]
    assert result.trace.mode_used == 'vector'
    assert all(h.chunk.chunk_id == pid for h in result.hits)


def test_source_filter_survives_vector_failure(boundary):  # noqa: F811
    b = boundary
    pid = b.row['parent_id']
    chunk = next(c for c in b.data.chunks(**{k:v for k,v in b.options.items() if k != 'top_k'}) if c.chunk_id == pid)
    b.runtime.query = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('fake vector failure'))
    result = retriever(b).search_with_trace(_body(chunk)[:100], **b.options, parent_ids=(pid,))
    assert result.trace.mode_used == 'lexical' and result.hits
    assert all(h.chunk.chunk_id == pid for h in result.hits)


def test_hybrid_passes_source_subset_to_both_legs_before_fusion(boundary):  # noqa: F811
    b = boundary
    lexical, calls = HUSRAGRetriever(b.data), []
    pid = b.row['parent_id']
    def vector(query, **options):
        calls.append(options)
        hits = lexical.search(query, **options)
        return VectorSearchResult(hits, VectorTrace(index_id='synthetic-pinned'))
    hybrid = HUSHybridRetriever(b.data, vector=SimpleNamespace(search_with_trace=vector))
    result = hybrid.search_with_trace('nghề nghiệp', **b.options, parent_ids=(pid,))
    assert calls[0]['parent_ids'] == (pid,) and calls[0]['top_k'] == 20
    assert json.loads(result.trace.filter_json)['parent_ids'] == [pid]
    assert all(h.chunk.chunk_id == pid for h in result.hits)


@pytest.mark.parametrize('bad', ['one', ['one'], ('one','one'), ('',), (False,)])
def test_parent_restriction_is_strict_not_a_user_query(bad, boundary):  # noqa: F811
    with pytest.raises(RAGDataError):
        HUSRAGRetriever(boundary.data).search('nội dung', **boundary.options, parent_ids=bad)


def test_empty_source_selection_never_opens_vector_runtime(boundary):  # noqa: F811
    def forbidden():
        pytest.fail('Empty source scope reached model/index runtime')
    result = retriever(boundary, forbidden).search_with_trace('nghề nghiệp', **boundary.options, parent_ids=())
    assert not result.hits
