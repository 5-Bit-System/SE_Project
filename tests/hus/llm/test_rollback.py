"""L6 enable/disable API checks on real RAG; provider is always synthetic."""

import json
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.hus.llm.test_pipeline import completion, transport
from tools.run_hus_rag_demo import PROGRAMS


@pytest.fixture(autouse=True)
def server_config(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-l6-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'gemini-3.5-flash-lite')
    monkeypatch.setenv('HUS_LLM_BASE_URL',
                       'https://generativelanguage.googleapis.com/v1beta/openai')


def reply_from_bundle(request):
    bundle = json.loads(json.loads(request.content)['messages'][1]['content'])
    if bundle['scope']['dataset'] == 'f2':
        output = {'kind': 'facts', 'style': 'direct', 'fact_keys': list(bundle['facts']),
                  'citation_ids': [s['citation_id'] for s in bundle['sources']]}
    elif bundle['schema_version'] == 'hus-llm-document-v3':
        output = {'kind': 'rewrite_v3', 'items': [{'id': part['id'], 'text': part['text']}
            for source in bundle['sources'] for part in source['segments']]}
    else:
        output = {'kind': 'rewrite', 'points': [
            {'text': s['quote'], 'anchor_quote': s['quote'], 'citation_id': s['citation_id']}
            for s in bundle['sources']]}
    return httpx.Response(200, json=completion(output))


def request_for(major, family):
    code, version = PROGRAMS[major]
    return {'question': {'f1': 'Giới thiệu ngành', 'f2': f'{code} có bao nhiêu tín chỉ?',
                         'f3': f'Nội dung {code}?'}[family],
            'major': major, 'version': version, 'allow_generated_reference': family == 'f3',
            'allow_llm_rewrite': True}


@pytest.mark.parametrize('major', list(PROGRAMS))
@pytest.mark.parametrize('family', ['f1', 'f2', 'f3'])
def test_off_on_off_restores_exact_legacy_response_and_needs_no_key(monkeypatch, major, family):
    from app.hus.demo import app

    calls = transport(monkeypatch, reply_from_bundle)
    payload = request_for(major, family)
    with TestClient(app) as client:
        original = client.post('/hus/chat', json=payload).json()
        assert original['hus_answer']['status'] == 'answered'
        assert set(original) == {'mode', 'reply', 'hus_answer'} and calls == []
        monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
        assert client.get('/hus/config').json()['llm_rewrite_available'] is True
        rewritten = client.post('/hus/chat', json=payload).json()
        assert rewritten['generation']['used'] is True and len(calls) == 1
        assert rewritten['hus_answer'] == original['hus_answer']
        monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
        monkeypatch.delenv('HUS_LLM_API_KEY')
        monkeypatch.setenv('HUS_LLM_BASE_URL', '/unused-invalid-config')
        assert client.get('/hus/config').json()['llm_rewrite_available'] is False
        rolled_back = client.post('/hus/chat', json=payload)
    assert rolled_back.status_code == 200
    assert rolled_back.json() == original
    assert len(calls) == 1  # No provider request at rollback, even though user consent is still true.


@pytest.mark.parametrize('family', ['f1', 'f2', 'f3'])
@pytest.mark.parametrize('failure', ['timeout', 'transport', 'quota', 'invalid_output'])
def test_failure_fallback_then_disable_uses_canonical_without_another_http(monkeypatch, family, failure):
    from app.hus.demo import app

    def fail(request):
        if failure == 'timeout':
            raise httpx.ReadTimeout('private-provider-error', request=request)
        if failure == 'transport':
            raise httpx.ConnectError('private-provider-error', request=request)
        if failure == 'quota':
            return httpx.Response(429, text='private-provider-error synthetic-l6-key')
        return httpx.Response(200, json=completion({'kind': 'wrong'}))

    calls = transport(monkeypatch, fail)
    payload = request_for('data_science', family)
    with TestClient(app) as client:
        original = client.post('/hus/chat', json=payload).json()
        monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
        failed = client.post('/hus/chat', json=payload)
        assert failed.status_code == 200
        response = failed.json()
        assert response['generation']['used'] is False and len(calls) == 1
        assert response['reply'] == original['reply'] and response['hus_answer'] == original['hus_answer']
        assert 'private-provider-error' not in failed.text and 'synthetic-l6-key' not in failed.text
        monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
        assert client.post('/hus/chat', json=payload).json() == original
    assert len(calls) == 1


@pytest.mark.parametrize('consent', ['rewrite', 'f3'])
def test_server_enabled_still_requires_user_permissions(monkeypatch, consent):
    from app.hus.demo import app

    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    calls = transport(monkeypatch, lambda request: pytest.fail('Missing consent sent HTTP'))
    payload = request_for('data_science', 'f3')
    payload['allow_llm_rewrite' if consent == 'rewrite' else 'allow_generated_reference'] = False
    with TestClient(app) as client:
        result = client.post('/hus/chat', json=payload)
    assert result.status_code == 200 and calls == []
    if consent == 'rewrite':
        assert 'generation' not in result.json()
    else:
        assert result.json()['generation']['used'] is False


def test_disabling_model_does_not_hide_canonical_failure(monkeypatch):
    from app.hus import demo
    from app.hus.rag_loader import RAGDataError

    def broken(request):
        raise RAGDataError('private-source-path')

    monkeypatch.setattr(demo, 'get_hus_answerer', lambda: SimpleNamespace(programs={}, answer=broken))
    calls = transport(monkeypatch, lambda request: pytest.fail('Broken canonical sent HTTP'))
    with TestClient(demo.app) as client:
        for flag in ('true', 'false'):
            monkeypatch.setenv('HUS_LLM_ENABLED', flag)
            response = client.post('/hus/chat', json=request_for('data_science', 'f2'))
            assert response.status_code == 503
            assert 'private-source-path' not in response.text
    assert calls == []
