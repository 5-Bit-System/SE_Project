"""A hybrid request must bind to its own artifacts; lexical stays lightweight."""
import json
import os
from unittest.mock import patch

import pytest


def profile(tmp_path):
    raw = {'schema_version': 'hus-retrieval-profile-1.0',
           'release_id': 'hus-data-20261111-v4', 'release_sha256': 'b' * 64,
           'contract_path': 'data/hus/vector_contracts/new',
           'passage_path': 'data/hus/vector_passages/new',
           'index_path': 'data/hus/vector_indexes/new', 'expected_index_id': 'a' * 64}
    folder = tmp_path / 'data/hus/vector_profiles'
    folder.mkdir(parents=True)
    path = folder / 'hybrid_v4_20261114.json'
    path.write_text(json.dumps(raw), encoding='utf-8')
    return path, raw


def test_lexical_never_reads_profile_or_model(tmp_path, monkeypatch):
    from pathlib import Path

    from app.hus.retrieval_profile import configure_retrieval
    monkeypatch.setattr(Path, 'read_bytes', lambda *a: pytest.fail('Lexical read optional config'))
    with patch.dict(os.environ, {}, clear=True):
        configure_retrieval('lexical', root=tmp_path)
        assert os.environ['HUS_RETRIEVAL_MODE'] == 'lexical'


def test_hybrid_exports_separately_pinned_artifacts(tmp_path):
    from app.hus.retrieval_profile import configure_retrieval
    _, raw = profile(tmp_path)
    with patch.dict(os.environ, {}, clear=True):
        configure_retrieval('hybrid', root=tmp_path)
        assert os.environ['HUS_VECTOR_EXPECTED_INDEX_ID'] == raw['expected_index_id']
        assert os.environ['HUS_VECTOR_CONTRACT_PATH'] == str(tmp_path / raw['contract_path'])
        assert os.environ['HUS_VECTOR_PASSAGE_PATH'] == str(tmp_path / raw['passage_path'])
        assert os.environ['HUS_VECTOR_INDEX_PATH'] == str(tmp_path / raw['index_path'])
        assert os.environ['HUS_VECTOR_MODEL_CACHE'] == str(tmp_path / '.cache/hus/multilingual-e5-small')


@pytest.mark.parametrize('fault', ['pin', 'escape'])
def test_bad_profile_rejected(tmp_path, fault):
    from app.hus.retrieval_profile import configure_retrieval
    path, raw = profile(tmp_path)
    raw['expected_index_id' if fault == 'pin' else 'contract_path'] = 'bad' if fault == 'pin' else '../escape'
    path.write_text(json.dumps(raw), encoding='utf-8')
    with pytest.raises(ValueError):
        configure_retrieval('hybrid', root=tmp_path)


def test_settings_keep_explicit_v4_artifact_paths():
    from app.hus.retrieval_config import HUSRetrievalSettings
    settings = HUSRetrievalSettings.from_env({'HUS_RETRIEVAL_MODE': 'hybrid',
        'HUS_VECTOR_CONTRACT_PATH': 'new-contract', 'HUS_VECTOR_PASSAGE_PATH': 'new-passages'})
    assert settings.contract_path == 'new-contract' and settings.passage_path == 'new-passages'


def test_runtime_verifies_explicit_paths_instead_of_v3(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from app.hus import vector_index, vector_runtime
    index = tmp_path / 'index'
    (index / 'chroma').mkdir(parents=True)
    for name in ['manifest.json', 'vectors.jsonl', 'chroma/chroma.sqlite3']:
        (index / name).write_bytes(b'')
    model = tmp_path / 'model'
    model.mkdir()
    calls = []
    def verify(folder, contract, passages, data, cache, **kwargs):
        calls.append((contract, passages))
        raise ValueError('stop before native runtime')
    monkeypatch.setattr(vector_index, 'verify_index', verify)
    settings = SimpleNamespace(index_path=str(index), model_cache=str(model), expected_index_id='a'*64,
                               contract_path='v4-contract', passage_path='v4-passages')
    with pytest.raises(vector_runtime.VectorQueryError):
        vector_runtime.LocalVectorRuntime(settings, None)
    assert calls == [('v4-contract', 'v4-passages')]


def test_gemini_hybrid_check_never_loads_key(tmp_path, monkeypatch):
    import app.hus.retrieval_profile as module
    from tools import run_hus_llm
    calls = []
    monkeypatch.setattr(module, 'check_hybrid', lambda **kwargs: calls.append(kwargs) or {'passed': True})
    monkeypatch.setattr(run_hus_llm, 'configure', lambda *a, **k: pytest.fail('Check loaded backend key'))
    run_hus_llm.main(['--retrieval', 'hybrid', '--check'])
    assert calls


@pytest.mark.parametrize('fault', ['release', 'fallback', 'pin', 'lexical_empty'])
def test_hybrid_preflight_never_counts_fallback_or_stale_index_as_success(tmp_path, monkeypatch, fault):
    from types import SimpleNamespace

    from app.hus.retrieval_profile import require_hybrid
    from app.services import hus_service
    _, raw = profile(tmp_path)
    release = {'release_id': raw['release_id'], 'release_sha256': raw['release_sha256']}
    if fault == 'release':
        release['release_sha256'] = 'c' * 64
    trace = SimpleNamespace(actual_mode='lexical' if fault == 'fallback' else 'hybrid',
        fallback_reason='model_unavailable' if fault == 'fallback' else None,
        lexical=() if fault == 'lexical_empty' else (1,), vector=(1,),
        vector_trace=SimpleNamespace(index_id='c'*64 if fault == 'pin' else raw['expected_index_id']))
    result = SimpleNamespace(trace=trace, hits=(1,))
    answerer = SimpleNamespace(data=SimpleNamespace(release_identity=release),
                              retriever=SimpleNamespace(search_with_trace=lambda *a, **k: result))
    def get_answerer():
        return answerer
    get_answerer.cache_clear = lambda: None
    monkeypatch.setattr(hus_service, 'get_hus_answerer', get_answerer)
    with pytest.raises(ValueError):
        require_hybrid(root=tmp_path)


def test_offline_launcher_uses_hybrid_check_instead_of_lexical_check(monkeypatch):
    import app.hus.retrieval_profile as module
    from tools import run_hus_rag
    calls = []
    monkeypatch.setattr(module, 'check_hybrid', lambda **kwargs: calls.append(kwargs) or {'passed': True})
    monkeypatch.setattr(run_hus_rag, 'check', lambda: pytest.fail('Ran lexical check for hybrid'))
    with patch.dict(os.environ):
        run_hus_rag.main(['--retrieval', 'hybrid', '--check'])
    assert calls


def test_normal_gemini_hybrid_warms_before_server_and_keeps_auto(tmp_path, monkeypatch):
    import uvicorn

    import app.hus.retrieval_profile as module
    from tools import run_hus_llm
    profile(tmp_path)
    (tmp_path / '.env').write_text('HUS_LLM_API_KEY=fake-only\n', encoding='utf-8')
    monkeypatch.setattr(run_hus_llm, 'ROOT', tmp_path)
    order = []
    def preflight(**kwargs):
        assert os.environ['HUS_LLM_ENABLED'] == os.environ['HUS_LLM_AUTO'] == 'true'
        assert os.environ['HUS_RETRIEVAL_MODE'] == 'hybrid'
        order.append('preflight')
    monkeypatch.setattr(module, 'require_hybrid', preflight)
    monkeypatch.setattr(uvicorn, 'run', lambda *a, **k: order.append('server'))
    with patch.dict(os.environ, {}, clear=True):
        run_hus_llm.main(['--retrieval', 'hybrid'])
    assert order == ['preflight', 'server']


def test_hybrid_check_forces_llm_off(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import app.hus.retrieval_profile as module
    _, raw = profile(tmp_path)
    def preflight(**kwargs):
        assert os.environ['HUS_LLM_ENABLED'] == os.environ['HUS_LLM_AUTO'] == 'false'
        answerer = SimpleNamespace(data=SimpleNamespace(release_identity={}))
        result = SimpleNamespace(hits=(1,), trace=SimpleNamespace(actual_mode='hybrid',lexical=(1,),vector=(1,)))
        return answerer, result
    monkeypatch.setattr(module, 'require_hybrid', preflight)
    with patch.dict(os.environ, {'HUS_LLM_ENABLED':'true','HUS_LLM_AUTO':'true'}, clear=True):
        result = module.check_hybrid(root=tmp_path)
        assert result['Google_calls'] == 0 and result['index_id'] == raw['expected_index_id']


def test_config_exposes_requested_retrieval_mode(monkeypatch):
    from fastapi.testclient import TestClient

    from app.hus import demo
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'lexical')
    with TestClient(demo.app) as client:
        assert client.get('/hus/config').json()['retrieval_mode'] == 'lexical'
