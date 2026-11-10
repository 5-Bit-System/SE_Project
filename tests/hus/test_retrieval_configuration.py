"""Optional vector dependencies cannot affect the default lexical runtime."""
import importlib
import importlib.util

import pytest


def config():
    assert importlib.util.find_spec('app.hus.retrieval_config') is not None, 'V1 retrieval config missing'
    return importlib.import_module('app.hus.retrieval_config')


def test_mode_defaults_to_lexical_without_any_optional_import():
    c = config().HUSRetrievalSettings.from_env({})
    assert c.mode == 'lexical'
    c.require_available()


@pytest.mark.parametrize('value', ['hybrid'])
def test_hybrid_is_explicitly_available_at_v5(value):
    c = config().HUSRetrievalSettings.from_env({'HUS_RETRIEVAL_MODE': value})
    assert c.mode == value
    c.require_available()


@pytest.mark.parametrize('value', ['', 'unknown', 'LEXICAL', True, None])
def test_invalid_mode_does_not_silently_enable_or_fake_a_retriever(value):
    with pytest.raises(ValueError):
        config().HUSRetrievalSettings.from_env({'HUS_RETRIEVAL_MODE': value})


@pytest.mark.parametrize('value', ['unknown'])
def test_service_checks_mode_before_loading_any_vector_runtime(monkeypatch, value):
    config()
    from app.services.hus_service import get_hus_answerer
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', value)
    get_hus_answerer.cache_clear()
    try:
        with pytest.raises(ValueError):
            get_hus_answerer()
    finally:
        get_hus_answerer.cache_clear()


def test_vector_mode_accepts_explicit_local_configuration():
    c = config().HUSRetrievalSettings.from_env({'HUS_RETRIEVAL_MODE': 'vector',
        'HUS_VECTOR_INDEX_PATH': 'index', 'HUS_VECTOR_MODEL_CACHE': 'cache',
        'HUS_VECTOR_EXPECTED_INDEX_ID': 'a' * 64})
    c.require_available()
    assert c.index_path == 'index' and c.model_cache == 'cache'
    assert c.expected_index_id == 'a' * 64


def test_vector_service_f2_never_constructs_model(monkeypatch):
    from app.hus import vector_runtime
    from app.schemas.hus import HUSQuestion
    from app.services.hus_service import get_hus_answerer

    def forbidden(*args, **kwargs):
        pytest.fail('F2 must not initialize optional runtime')
    monkeypatch.setattr(vector_runtime, 'LocalVectorRuntime', forbidden)
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'vector')
    get_hus_answerer.cache_clear()
    try:
        answerer = get_hus_answerer()
        assert type(answerer.retriever).__name__ == 'HUSVectorRetriever'
        answer = answerer.answer(HUSQuestion(question='MAT2501 có bao nhiêu tín chỉ?',
                                             major='data_science', version='QD3569-2023'))
        assert answer.status == 'answered' and answer.dataset == 'f2'
    finally:
        get_hus_answerer.cache_clear()


def test_vector_service_missing_configuration_falls_back_with_trace(monkeypatch):
    from app.services.hus_service import get_hus_answerer

    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'vector')
    for key in ('HUS_VECTOR_INDEX_PATH', 'HUS_VECTOR_MODEL_CACHE', 'HUS_VECTOR_EXPECTED_INDEX_ID'):
        monkeypatch.delenv(key, raising=False)
    get_hus_answerer.cache_clear()
    try:
        result = get_hus_answerer().retriever.search_with_trace('nghề nghiệp', dataset='f1',
                                                               major='data_science', field='careers')
        assert result.trace.fallback_reason == 'vector_configuration'
        assert result.trace.mode_used == 'lexical'
    finally:
        get_hus_answerer.cache_clear()


def test_vector_service_canonical_load_failure_never_falls_back(monkeypatch):
    from app.hus.rag_loader import HUSRAGData, RAGDataError
    from app.services.hus_service import get_hus_answerer

    def broken(*args, **kwargs):
        raise RAGDataError('canonical invalid')
    monkeypatch.setattr(HUSRAGData, 'load_current', broken)
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'vector')
    get_hus_answerer.cache_clear()
    try:
        with pytest.raises(RAGDataError, match='canonical'):
            get_hus_answerer()
    finally:
        get_hus_answerer.cache_clear()


def test_actual_lexical_service_runs_when_optional_ml_imports_are_blocked(monkeypatch):
    config()
    import sys

    from app.schemas.hus import HUSQuestion
    from app.services.hus_service import get_hus_answerer

    class BlockML:
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split('.')[0] in {'torch', 'transformers', 'chromadb', 'tokenizers', 'sentence_transformers'}:
                raise AssertionError('Unexpected optional ML import: ' + fullname)

    monkeypatch.delenv('HUS_RETRIEVAL_MODE', raising=False)
    blocker = BlockML()
    sys.meta_path.insert(0, blocker)
    get_hus_answerer.cache_clear()
    try:
        answerer = get_hus_answerer()
        assert type(answerer.retriever).__name__ == 'HUSRAGRetriever'
        a = answerer.answer(HUSQuestion(question='MAT2501 có bao nhiêu tín chỉ?', major='data_science', version='QD3569-2023'))
        assert a.status == 'answered' and a.dataset == 'f2'
    finally:
        sys.meta_path.remove(blocker)
        get_hus_answerer.cache_clear()


def test_hybrid_service_uses_vector_configuration_and_f2_without_ml(monkeypatch):
    from app.hus import vector_runtime
    from app.schemas.hus import HUSQuestion
    from app.services.hus_service import get_hus_answerer

    settings = config().HUSRetrievalSettings.from_env({'HUS_RETRIEVAL_MODE': 'hybrid',
        'HUS_VECTOR_INDEX_PATH': 'index', 'HUS_VECTOR_MODEL_CACHE': 'cache',
        'HUS_VECTOR_EXPECTED_INDEX_ID': 'a' * 64})
    assert settings.index_path == 'index'
    def forbidden(*args, **kwargs):
        pytest.fail('F2 must not initialize ML in hybrid mode')
    monkeypatch.setattr(vector_runtime, 'LocalVectorRuntime', forbidden)
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'hybrid')
    get_hus_answerer.cache_clear()
    try:
        answerer = get_hus_answerer()
        assert type(answerer.retriever).__name__ == 'HUSHybridRetriever'
        answer = answerer.answer(HUSQuestion(question='MAT2501 có bao nhiêu tín chỉ?',
                                             major='data_science', version='QD3569-2023'))
        assert answer.status == 'answered' and answer.dataset == 'f2'
    finally:
        get_hus_answerer.cache_clear()
