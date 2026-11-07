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


@pytest.mark.parametrize('value', ['vector', 'hybrid'])
def test_reserved_modes_are_explicitly_unavailable_at_v1(value):
    c = config().HUSRetrievalSettings.from_env({'HUS_RETRIEVAL_MODE': value})
    assert c.mode == value
    with pytest.raises(ValueError, match='V1'):
        c.require_available()


@pytest.mark.parametrize('value', ['', 'unknown', 'LEXICAL', True, None])
def test_invalid_mode_does_not_silently_enable_or_fake_a_retriever(value):
    with pytest.raises(ValueError):
        config().HUSRetrievalSettings.from_env({'HUS_RETRIEVAL_MODE': value})


@pytest.mark.parametrize('value', ['vector', 'hybrid', 'unknown'])
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
