"""Real adapter/client/HTTP serialization and chat/API integration, entirely offline."""

import json
from copy import deepcopy
from hashlib import sha256
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from app.hus.chat import chat
from app.hus.rag_loader import RAGDataError
from app.services.hus_service import get_hus_answerer
from tests.hus.llm.fixtures import compact_text_output, context, facts_output, text_output


@pytest.fixture(autouse=True)
def settings(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-pipeline-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'gemini-3.5-flash-lite')
    monkeypatch.setenv('HUS_LLM_BASE_URL',
                       'https://generativelanguage.googleapis.com/v1beta/openai')


def completion(data, **extra):
    return {'id': 'chatcmpl-offline', 'object': 'chat.completion', 'created': 0,
            'model': 'actual-model-version', 'choices': [{'index': 0, 'finish_reason': 'stop',
                'message': {'role': 'assistant', 'content': json.dumps(data, ensure_ascii=False)}}],
            'usage': {'prompt_tokens': 8, 'completion_tokens': 5, 'total_tokens': 13}, **extra}


def transport(monkeypatch, handler):
    requests = []

    def handle(self, request):
        requests.append(request)
        return handler(request)

    monkeypatch.setattr(httpx.HTTPTransport, 'handle_request', handle)
    return requests


def fixed_answerer(ctx):
    return SimpleNamespace(programs={}, answer=lambda request: ctx.answer)


@pytest.mark.parametrize('dataset', ['f1', 'f2', 'f3'])
def test_default_pipeline_sends_only_grounded_bundle_and_preserves_canonical(monkeypatch, dataset):
    ctx = context(dataset)
    original = deepcopy(ctx.answer.model_dump())
    output = facts_output() if dataset == 'f2' else compact_text_output()
    calls = transport(monkeypatch, lambda request: httpx.Response(200, json=completion(output)))
    result = chat(ctx.question, fixed_answerer(ctx))
    assert result.generation.used is True
    assert result.generation.model == 'actual-model-version'
    assert result.generation.requested_model == 'gemini-3.5-flash-lite'
    assert result.generation.usage.total_tokens == 13
    assert len(calls) == 1
    wire = json.loads(calls[0].content)
    assert set(wire) == {'model', 'messages', 'stream', 'max_tokens'}
    assert wire['model'] == 'gemini-3.5-flash-lite'
    assert wire['stream'] is False and wire['max_tokens'] == 1024
    assert str(calls[0].url) == (
        'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions')
    assert calls[0].headers['authorization'] == 'Bearer synthetic-pipeline-key'
    assert 'synthetic-pipeline-key' not in calls[0].content.decode()
    assert 'PRIVATE_' not in calls[0].content.decode()
    assert 'C:/Users/' not in calls[0].content.decode()
    expected_hash = sha256(json.dumps(wire['messages'], ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()
    assert result.generation.prompt_sha256 == expected_hash
    assert result.hus_answer.model_dump() == original
    if dataset == 'f2':
        assert result.reply.endswith(ctx.answer.reply)
        assert result.hus_answer.facts['value'] == 3
    else:
        assert '[1]' in result.reply and '[2]' in result.reply
        assert all(w in result.reply for w in ctx.answer.warnings)


@pytest.mark.parametrize('reason', ['unknown_id', 'foreign_text', 'number', 'coverage', 'extra_f2'])
def test_rejected_default_pipeline_output_falls_back_without_publishing_it(monkeypatch, reason):
    ctx = context('f2' if reason == 'extra_f2' else 'f1')
    output = facts_output() if reason == 'extra_f2' else compact_text_output()
    if reason == 'unknown_id':
        output['items'][0]['id'] = 'b999'
    elif reason == 'foreign_text':
        output['items'][0]['text'] = 'invented source words'
    elif reason == 'number':
        output['items'][0]['text'] += ' Có 999 học phần.'
    elif reason == 'coverage':
        output['items'].pop()
    else:
        output['value'] = 999
    calls = transport(monkeypatch, lambda request: httpx.Response(200, json=completion(output)))
    result = chat(ctx.question, fixed_answerer(ctx))
    assert len(calls) == 1
    assert result.generation.used is False
    assert result.generation.fallback_reason in {'invalid_output', 'evidence_coverage'}
    assert result.generation.model is None
    assert result.reply == ctx.answer.reply
    assert result.hus_answer.model_dump() == ctx.answer.model_dump()


def test_prompt_overflow_never_sends_http(monkeypatch):
    ctx = context()
    ctx.answer.citations[0].quote = 'nguồn ' * 3000
    calls = transport(monkeypatch, lambda request: pytest.fail('Oversized prompt sent'))
    result = chat(ctx.question, fixed_answerer(ctx))
    assert calls == []
    assert result.generation.fallback_reason == 'prompt_budget'
    assert result.reply == ctx.answer.reply


def test_raw_response_whitespace_counts_toward_output_budget(monkeypatch):
    body = completion(text_output())
    body['choices'][0]['message']['content'] = ' ' * 9000 + body['choices'][0]['message']['content']
    calls = transport(monkeypatch, lambda request: httpx.Response(200, json=body))
    ctx = context()
    result = chat(ctx.question, fixed_answerer(ctx))
    assert len(calls) == 1
    assert result.generation.used is False
    assert result.generation.fallback_reason == 'output_budget'
    assert result.reply == ctx.answer.reply


def test_known_key_in_user_prompt_never_leaves_backend(monkeypatch):
    ctx = context()
    ctx.question.question += ' synthetic-pipeline-key'
    calls = transport(monkeypatch, lambda request: pytest.fail('Key sent in provider JSON'))
    result = chat(ctx.question, fixed_answerer(ctx))
    assert calls == []
    assert result.generation.fallback_reason == 'unsafe_prompt'


def test_invalid_canonical_scope_fails_closed_before_provider(monkeypatch):
    ctx = context()
    ctx.answer.citations[0].metadata['scope']['major'] = 'mathematics'
    calls = transport(monkeypatch, lambda request: pytest.fail('Invalid scope sent'))
    with pytest.raises(RAGDataError):
        chat(ctx.question, fixed_answerer(ctx))
    assert calls == []


@pytest.mark.parametrize('failure', ['http', 'timeout', 'truncated', 'over_tokens'])
def test_client_failures_keep_original_answer(monkeypatch, failure):
    def respond(request):
        if failure == 'http':
            return httpx.Response(429, text='private-provider-body')
        if failure == 'timeout':
            raise httpx.ReadTimeout('private-provider-body', request=request)
        body = completion(text_output())
        if failure == 'truncated':
            body['choices'][0]['finish_reason'] = 'length'
        else:
            body['usage']['completion_tokens'] = 1025
        return httpx.Response(200, json=body)

    ctx = context()
    calls = transport(monkeypatch, respond)
    result = chat(ctx.question, fixed_answerer(ctx))
    assert len(calls) == 1
    assert result.generation.fallback_reason == {'http': 'http_error', 'timeout': 'timeout',
        'truncated': 'invalid_response', 'over_tokens': 'output_budget'}[failure]
    assert result.reply == ctx.answer.reply
    assert 'private-provider-body' not in result.model_dump_json()


@pytest.mark.parametrize('case', ['server_off', 'user_off', 'basic', 'missing', 'f3_opt_out'])
def test_default_pipeline_remains_behind_every_l2_guard(monkeypatch, case):
    ctx = context('f3' if case == 'f3_opt_out' else 'f1')
    if case == 'server_off':
        monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    elif case == 'user_off':
        ctx.question.allow_llm_rewrite = False
    elif case == 'basic':
        ctx.question.dataset = 'auto'
        ctx.question.question = 'Xin chào'
    elif case == 'missing':
        ctx.answer.status = 'no_information'
    else:
        ctx.question.allow_generated_reference = False
    calls = transport(monkeypatch, lambda request: pytest.fail('Guarded request sent'))
    result = chat(ctx.question, fixed_answerer(ctx))
    assert calls == []
    if case in {'server_off', 'user_off'}:
        assert 'generation' not in result.model_dump()
    else:
        assert result.generation.used is False


@pytest.mark.parametrize('major', ['data_science', 'mathematics',
                                 'mathematics_informatics', 'computer_science'])
@pytest.mark.parametrize('dataset', ['f1', 'f2', 'f3'])
def test_actual_api_uses_registered_pipeline_with_real_rag_and_mock_http(monkeypatch, major, dataset):
    from app.hus.demo import app

    answerer = get_hus_answerer()
    version = next(v for m, v in answerer.programs.values() if m == major)
    code = answerer.data.f2_courses(major=major, version=version)[0].course['course_code']
    text = {'f1': 'Giới thiệu ngành', 'f2': f'{code} có bao nhiêu tín chỉ?',
            'f3': f'Nội dung {code}?'}[dataset]

    def respond(request):
        evidence = json.loads(json.loads(request.content)['messages'][1]['content'])
        if evidence['scope']['dataset'] == 'f2':
            data = {'kind': 'facts', 'style': 'direct', 'fact_keys': list(evidence['facts']),
                    'citation_ids': [s['citation_id'] for s in evidence['sources']]}
        else:
            data = {'kind': 'rewrite_v3', 'items': [{'id': part['id'], 'text': part['text']}
                for source in evidence['sources'] for part in source['segments']]}
        return httpx.Response(200, json=completion(data))

    calls = transport(monkeypatch, respond)
    with TestClient(app) as client:
        payload = {'question': text, 'major': major, 'version': version,
                   'allow_generated_reference': dataset == 'f3'}
        baseline = client.post('/hus/chat', json=payload)
        assert baseline.status_code == 200
        response = client.post('/hus/chat', json={**payload, 'allow_llm_rewrite': True})
    assert response.status_code == 200
    assert len(calls) == 1
    result = response.json()
    assert result['generation']['used'] is True
    assert result['generation']['model'] == 'actual-model-version'
    assert result['hus_answer'] == baseline.json()['hus_answer']
    if result['hus_answer']['dataset'] == 'f2':
        assert result['reply'].endswith(baseline.json()['reply'])


@pytest.mark.parametrize('state,value', [('unknown', [None]), ('present', ['MAT1001']),
                                       ('unresolved', ['Mã chưa rõ']),
                                       ('conflict', ['MAT1001', 'MAT1002'])])
def test_f2_prerequisite_states_survive_the_registered_pipeline(monkeypatch, state, value):
    ctx = context('f2')
    ctx.answer.facts.update(field='prerequisites', prerequisite_status=state, value=value)
    original = deepcopy(ctx.answer.model_dump())
    calls = transport(monkeypatch, lambda request: httpx.Response(
        200, json=completion(facts_output())))
    result = chat(ctx.question, fixed_answerer(ctx))
    assert len(calls) == 1
    assert result.generation.used is True
    assert result.hus_answer.model_dump() == original
    assert result.reply.endswith(original['reply'])


def test_api_does_not_leak_canonical_error_details(monkeypatch):
    from app.hus import demo

    ctx = context()
    ctx.answer.citations[0].metadata['release_id'] = 'wrong-release'
    monkeypatch.setattr(demo, 'get_hus_answerer', lambda: fixed_answerer(ctx))
    calls = transport(monkeypatch, lambda request: pytest.fail('Invalid release sent'))
    with TestClient(demo.app) as client:
        result = client.post('/hus/chat', json=ctx.question.model_dump())
    assert result.status_code == 503
    assert 'wrong-release' not in result.text
    assert calls == []
