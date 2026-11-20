"""Auto Gemini uses offline only after quota, with no real provider calls."""
import pytest

from app.hus.chat import chat
from app.hus.llm.client import HUSLLMError
from app.hus.llm.contracts import HUSF2Presentation
from app.schemas.hus import HUSQuestion
from app.services.hus_service import get_hus_answerer


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_AUTO', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-auto-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'gemini-3.5-flash-lite')
    monkeypatch.setenv('HUS_LLM_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai')


@pytest.fixture(scope='module')
def answerer():
    return get_hus_answerer()


def request(question='MAT3533 có bao nhiêu tín chỉ?'):
    return HUSQuestion(question=question, major='data_science', version='QD3569-2023')


def test_auto_calls_without_request_opt_in(configured, answerer):
    from app.hus.llm.auto import AutoLLMPolicy
    calls = []
    def provider(context):
        calls.append(context)
        return HUSF2Presentation(style='direct', model='gemini-3.5-flash-lite')
    result = AutoLLMPolicy().reply(request(), answerer, rewriter=provider)
    assert result.generation.used is True and len(calls) == 1
    assert result.hus_answer.facts['value'] == 3


def test_quota_switches_to_offline_until_restart(configured, answerer):
    from app.hus.llm.auto import AutoLLMPolicy
    policy, calls = AutoLLMPolicy(), []
    def provider(context):
        calls.append(context)
        raise HUSLLMError('http_error', status_code=429)
    first = policy.reply(request(), answerer, rewriter=provider)
    second = policy.reply(request(), answerer, rewriter=provider)
    assert len(calls) == 1 and policy.quota_exhausted
    baseline = chat(request(), answerer)
    for result in (first, second):
        assert result.reply == baseline.reply
        assert result.generation.used is False and result.generation.http_status == 429
        assert result.hus_answer.facts == baseline.hus_answer.facts
    assert AutoLLMPolicy().quota_exhausted is False


def test_inflight_preparation_rechecks_quota_before_provider(configured, answerer):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from app.hus.llm.auto import AutoLLMPolicy
    entered, release, calls = Event(), Event(), []
    policy = AutoLLMPolicy()
    class SlowPreparation:
        programs = answerer.programs
        def prepare_evidence(self, request):
            entered.set()
            assert release.wait(10)
            return answerer.prepare_evidence(request)
    def success(context):
        calls.append(context)
        return HUSF2Presentation(style='direct', model='gemini-3.5-flash-lite')
    def quota(context):
        raise HUSLLMError('http_error', status_code=429)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(policy.reply, request(), SlowPreparation(), rewriter=success)
        try:
            assert entered.wait(10)
            policy.reply(request(), answerer, rewriter=quota)
        finally:
            release.set()
        result = pending.result(timeout=15)
    assert calls == []
    assert result.generation.used is False and result.generation.http_status == 429


@pytest.mark.parametrize('code,status', [('http_error', 401), ('http_error', 403),
    ('http_error', 503), ('transport_error', None), ('timeout', None), ('invalid_output', None)])
def test_other_errors_do_not_return_offline(configured, answerer, code, status):
    from app.hus.llm.auto import AutoLLMPolicy, AutoLLMUnavailable
    policy = AutoLLMPolicy()
    def provider(context):
        raise HUSLLMError(code, status_code=status)
    with pytest.raises(AutoLLMUnavailable):
        policy.reply(request(), answerer, rewriter=provider)
    assert policy.quota_exhausted is False


@pytest.mark.parametrize('question', ['Xin chào', 'Nội dung MAT3533?', 'Tín chỉ MAT9999?'])
def test_basic_missing_and_f3_opt_out_do_not_call_model(configured, answerer, question):
    from app.hus.llm.auto import AutoLLMPolicy
    def provider(context):
        pytest.fail('Model must not be called without eligible evidence/consent')
    result = AutoLLMPolicy().reply(request(question), answerer, rewriter=provider)
    assert result.generation is None or result.generation.used is False


def test_saved_key_launcher_selects_auto_mode(tmp_path, monkeypatch):
    from tools.run_hus_llm import configure
    monkeypatch.delenv('HUS_LLM_AUTO', raising=False)
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-auto-key')
    import os
    from unittest.mock import patch
    with patch.dict(os.environ):
        configure(tmp_path / '.env', root=tmp_path)
        assert os.environ['HUS_LLM_AUTO'] == 'true'


@pytest.mark.parametrize('status,expected_http', [(None, 200), (429, 200), (503, 502)])
def test_api_enforces_auto_even_when_client_flag_is_false(configured, answerer, monkeypatch, status, expected_http):
    from fastapi.testclient import TestClient

    from app.hus import demo
    from app.hus.llm import auto
    calls = []
    def provider(context):
        calls.append(context)
        if status:
            raise HUSLLMError('http_error', status_code=status)
        return HUSF2Presentation(style='direct', model='gemini-3.5-flash-lite')
    monkeypatch.setattr(auto, 'chat', lambda request, answerer, rewriter=None:
                        chat(request, answerer, rewriter=provider))
    monkeypatch.setattr(demo, 'auto_policy', auto.AutoLLMPolicy())
    monkeypatch.setattr(demo, 'current_answerer', lambda: answerer)
    with TestClient(demo.app) as client:
        result = client.post('/hus/chat', json={**request().model_dump(), 'allow_llm_rewrite': False})
        assert result.status_code == expected_http and len(calls) == 1
        config = client.get('/hus/config').json()
        assert config['llm_auto'] is True
        assert config['llm_quota_exhausted'] is (status == 429)
        if status == 503:
            assert 'hus_answer' not in result.json()
            assert 'synthetic-auto-key' not in result.text
        else:
            assert result.json()['generation']['used'] is (status is None)
