"""L4 capacity/timeout/quota behavior with deterministic thread events, no live HTTP."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import httpx
import pytest
from fastapi.testclient import TestClient

from app.hus.chat import chat
from app.hus.llm import HUSLLMClient, HUSLLMError
from app.hus.llm.contracts import HUSTextRewrite
from app.hus.rag_loader import RAGDataError
from tests.hus.llm.fixtures import compact_text_output, context
from tests.hus.llm.test_pipeline import completion, fixed_answerer, transport


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-l4-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'gemini-3.5-flash-lite')
    monkeypatch.setenv('HUS_LLM_BASE_URL',
                       'https://generativelanguage.googleapis.com/v1beta/openai')


def rewrite(ctx):
    return HUSTextRewrite(reply='Nội dung đã kiểm.', model='gemini-3.5-flash-lite')


def test_capacity_is_shared_across_default_adapter_instances_and_does_not_queue(monkeypatch):
    entered, release = Event(), Event()

    def respond(request):
        entered.set()
        assert release.wait(10), 'Test did not release the provider request'
        return httpx.Response(200, json=completion(compact_text_output()))

    calls = transport(monkeypatch, respond)
    first_ctx, second_ctx = context(), context('f2')
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(chat, first_ctx.question, fixed_answerer(first_ctx))
        try:
            assert entered.wait(5)
            second = pool.submit(chat, second_ctx.question, fixed_answerer(second_ctx)).result(2)
            assert second.generation.used is False
            assert second.generation.fallback_reason == 'busy'
            assert second.reply == second_ctx.answer.reply
            assert second.hus_answer.model_dump() == second_ctx.answer.model_dump()
            assert len(calls) == 1
            # Ordinary RAG still runs while the AI slot is occupied.
            second_ctx.question.allow_llm_rewrite = False
            ordinary = pool.submit(chat, second_ctx.question, fixed_answerer(second_ctx)).result(2)
            assert 'generation' not in ordinary.model_dump()
            assert ordinary.reply == second_ctx.answer.reply
        finally:
            release.set()
        assert first.result(10).generation.used is True
    assert chat(first_ctx.question, fixed_answerer(first_ctx)).generation.used is True
    assert len(calls) == 2


def test_capacity_also_covers_server_injected_adapters():
    entered, release = Event(), Event()
    ctx = context()

    def blocking(context):
        entered.set()
        assert release.wait(10)
        return rewrite(context)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(chat, ctx.question, fixed_answerer(ctx), rewriter=blocking)
        try:
            assert entered.wait(5)
            second = pool.submit(chat, ctx.question, fixed_answerer(ctx), rewriter=rewrite).result(2)
            assert second.generation.fallback_reason == 'busy'
        finally:
            release.set()
        assert first.result(10).generation.used is True


@pytest.mark.parametrize('failure', ['timeout', 401, 403, 429, 500, 503,
                                    'invalid_result', 'unexpected', 'canonical'])
def test_capacity_is_released_on_every_failure_and_metadata_is_safe(failure):
    ctx = context()

    def fail(context):
        if isinstance(failure, int):
            raise HUSLLMError('http_error', status_code=failure)
        if failure == 'timeout':
            raise HUSLLMError('timeout')
        if failure == 'invalid_result':
            return {'reply': 'not validated'}
        if failure == 'canonical':
            raise RAGDataError('private-source-path')
        raise RuntimeError('private-provider-body synthetic-l4-key')

    if failure == 'canonical':
        with pytest.raises(RAGDataError):
            chat(ctx.question, fixed_answerer(ctx), rewriter=fail)
    else:
        failed = chat(ctx.question, fixed_answerer(ctx), rewriter=fail)
        assert failed.reply == ctx.answer.reply
        assert failed.generation.used is False
        if isinstance(failure, int):
            assert failed.generation.http_status == failure
        assert 'private-provider-body' not in failed.model_dump_json()
        assert 'synthetic-l4-key' not in failed.model_dump_json()
    assert chat(ctx.question, fixed_answerer(ctx), rewriter=rewrite).generation.used is True


@pytest.mark.parametrize('status', [401, 403, 429, 500, 503])
def test_http_quota_and_provider_failures_are_canonical_fallbacks(monkeypatch, status):
    ctx = context()
    calls = transport(monkeypatch, lambda request: httpx.Response(status, text='private-error-body'))
    result = chat(ctx.question, fixed_answerer(ctx))
    assert len(calls) == 1
    assert result.reply == ctx.answer.reply
    assert result.generation.fallback_reason == 'http_error'
    assert result.generation.http_status == status
    assert 'private-error-body' not in result.model_dump_json()


@pytest.mark.parametrize('change,expected', [({}, True),
    ({'HUS_LLM_ENABLED': 'false'}, False), ({'HUS_LLM_ENABLED': 'invalid'}, False),
    ({'HUS_LLM_API_KEY': ''}, False), ({'HUS_LLM_BASE_URL': '/invalid'}, False),
    ({'HUS_LLM_BASE_URL': 'https://other-provider.example/v1'}, False),
    ({'HUS_LLM_BASE_URL': 'http://generativelanguage.googleapis.com/v1beta/openai'}, False),
    ({'HUS_LLM_MODEL': 'synthetic-l4-key'}, False)])
def test_config_exposes_only_availability_without_constructing_http_client(monkeypatch, change, expected):
    from app.hus.demo import app

    for key, value in change.items():
        monkeypatch.setenv(key, value)

    def forbidden(*args, **kwargs):
        pytest.fail('Configuration must not initialize an LLM HTTP client')

    monkeypatch.setattr(HUSLLMClient, '__init__', forbidden)
    with TestClient(app) as client:
        response = client.get('/hus/config')
    assert response.status_code == 200
    assert response.json()['llm_rewrite_available'] is expected
    assert 'synthetic-l4-key' not in response.text
    assert 'HUS_LLM_API_KEY' not in response.text
