"""Query token budgets and existing-index-only startup, without optional ML."""
import importlib
from types import SimpleNamespace

import pytest


def runtime_module():
    return importlib.import_module('app.hus.vector_runtime')


@pytest.mark.parametrize('size', [3, 512, 513])
def test_query_prefix_special_tokens_budget_and_no_truncation(size):
    m = runtime_module()
    calls, rows = [], []
    class Encoder:
        def tokenizer(self, text, **kwargs):
            calls.append((text, kwargs))
            return {'input_ids': [0] + [7] * (size - 2) + [2]}

        def encode(self, batch):
            rows.extend(batch)
            return [[1.0] + [0.0] * 383]
    encoder = Encoder()
    if size > 512:
        with pytest.raises(m.VectorQueryError, match='query_token_budget'):
            m.encode_query(encoder, 'mục tiêu')
        assert not rows
    else:
        vector = m.encode_query(encoder, 'mục tiêu')
        assert vector == [1.0] + [0.0] * 383
        assert rows[0]['input_tokens'] == size
        assert rows[0]['embedding_text'] == 'query: mục tiêu'
    assert calls == [('query: mục tiêu', dict(truncation=False, padding=False, add_special_tokens=True))]


def test_missing_index_does_not_create_directory_or_import_chroma(tmp_path, monkeypatch):
    m = runtime_module()
    from app.hus import vector_index
    def forbidden(*args):
        pytest.fail('Do not open/create missing index')
    monkeypatch.setattr(vector_index, '_client', forbidden)
    folder = tmp_path / 'absent'
    settings = SimpleNamespace(index_path=str(folder), model_cache=str(tmp_path / 'model'),
                               expected_index_id='a' * 64)
    with pytest.raises(m.VectorQueryError, match='index_missing'):
        m.LocalVectorRuntime(settings, None)
    assert not folder.exists()


def test_missing_pin_is_configuration_fallback_before_any_index_access():
    m = runtime_module()
    with pytest.raises(m.VectorQueryError, match='vector_configuration'):
        m.LocalVectorRuntime(SimpleNamespace(index_path=None, model_cache=None, expected_index_id=None), None)


def test_importing_v4_runtime_does_not_import_optional_libraries():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, '-c',
                             "import sys; import app.hus.vector_runtime; import app.hus.vector_query; "
                             "assert not ({'torch','chromadb','transformers','tokenizers','numpy'} & set(sys.modules))"],
                            capture_output=True)
    assert result.returncode == 0, result.stderr.decode()


@pytest.fixture
def live_index(tmp_path, monkeypatch):
    import json
    from threading import Lock

    from app.hus.vector_contract import ROOT
    from app.hus.vector_index import HNSW, index_metadata, inventory_bytes

    m = runtime_module()
    row = json.loads((ROOT / 'data/hus/vector_passages/e5_small_v2_20261105/passages.jsonl')
                     .read_bytes().splitlines()[0])
    vector = [1.0] + [0.0] * 383
    item = {'passage_id': row['passage_id'], 'metadata': index_metadata(row), 'vector': vector}
    state = {'metadata': {'index_id': 'pinned'}, 'configuration': {'hnsw': dict(HNSW)},
             'vector': vector, 'document': None, 'query_called': False}
    class Collection:
        @property
        def metadata(self):
            return state['metadata']

        @property
        def configuration(self):
            return state['configuration']

        def count(self):
            return 1

        def get(self, **kwargs):
            return {'ids': [row['passage_id']], 'metadatas': [index_metadata(row)],
                    'embeddings': [state['vector']], 'documents': [state['document']]}

        def query(self, **kwargs):
            state['query_called'] = True
            assert kwargs['where'] == {'family': 'f1'} and kwargs['n_results'] == 5
            assert kwargs['query_embeddings'] == [vector]
            return 'verified-query'
    runtime = m.LocalVectorRuntime.__new__(m.LocalVectorRuntime)
    runtime.folder = tmp_path
    runtime._manifest_raw = b'{}'
    runtime._inventory_raw = inventory_bytes([item])
    (tmp_path / 'manifest.json').write_bytes(runtime._manifest_raw)
    (tmp_path / 'vectors.jsonl').write_bytes(runtime._inventory_raw)
    runtime._expected_metadata = dict(state['metadata'])
    runtime.rows = {row['passage_id']: row}
    runtime._client = SimpleNamespace(get_collection=lambda *a, **kw: Collection())
    runtime._encoder = object()
    runtime._lock = Lock()
    monkeypatch.setattr(m, 'encode_query', lambda *args: vector)
    return runtime, state


def test_live_index_checks_precede_query_and_pass_explicit_embedding(live_index):
    runtime, state = live_index
    assert runtime.query('test', where={'family': 'f1'}, top_k=5) == 'verified-query'
    assert state['query_called']


@pytest.mark.parametrize('fault', ['manifest', 'inventory', 'metadata', 'vector', 'document',
                                  'metric', 'default_embedding_function'])
def test_live_index_rejects_post_startup_tampering_before_top_k(live_index, fault):
    runtime, state = live_index
    if fault in {'manifest', 'inventory'}:
        path = runtime.folder / ('manifest.json' if fault == 'manifest' else 'vectors.jsonl')
        path.write_bytes(path.read_bytes() + b' ')
    elif fault == 'metadata':
        state['metadata']['index_id'] = 'forged'
    elif fault == 'vector':
        state['vector'] = [0.0, 1.0] + [0.0] * 382
    elif fault == 'document':
        state['document'] = 'forbidden'
    elif fault == 'metric':
        state['configuration']['hnsw']['space'] = 'l2'
    else:
        state['configuration']['embedding_function'] = {'name': 'default'}
    with pytest.raises(runtime_module().VectorQueryError, match='index_identity'):
        runtime.query('test', where={'family': 'f1'}, top_k=5)
    assert not state['query_called']
