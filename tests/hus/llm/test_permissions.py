"""L2 permissions and response boundaries; no provider calls or L3 prompts."""

import importlib
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.hus.chat import chat
from app.hus.llm.client import HUSLLMError
from app.hus.rag_loader import RAGDataError
from app.schemas.hus import HUSQuestion
from app.services.hus_service import get_hus_answerer


@pytest.fixture(autouse=True)
def isolated_llm_settings(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-l2-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'gemini-3.5-flash-lite')
    monkeypatch.setenv('HUS_LLM_BASE_URL',
                       'https://generativelanguage.googleapis.com/v1beta/openai')


@pytest.fixture(scope='module')
def answerer():
    return get_hus_answerer()


def contracts():
    return importlib.import_module('app.hus.llm.contracts')


def question(text='Giới thiệu ngành', **extra):
    return HUSQuestion(question=text, major='data_science', version='QD3569-2023', **extra)


def forbidden(context):
    pytest.fail('This request must not reach the rewrite adapter')


@pytest.mark.parametrize('value', ['true', 'false', 0, 1, None, [], {}])
def test_request_rewrite_permission_is_strict_boolean(value):
    with pytest.raises(ValidationError):
        question(allow_llm_rewrite=value)


def test_default_permission_preserves_legacy_request_serialization():
    request = question()
    assert request.allow_llm_rewrite is False
    assert 'allow_llm_rewrite' not in request.model_dump()
    assert question(allow_llm_rewrite=True).model_dump()['allow_llm_rewrite'] is True


@pytest.mark.parametrize('permission', [None, False])
def test_user_off_preserves_legacy_response_without_reading_llm_config(
        answerer, monkeypatch, permission):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'invalid')
    monkeypatch.setenv('HUS_LLM_MODEL', '')
    request = question(**({} if permission is None else {'allow_llm_rewrite': permission}))
    before = chat(request, answerer).model_dump()
    result = chat(request, answerer, rewriter=forbidden)
    assert result.model_dump() == before
    assert set(before) == {'mode', 'reply', 'hus_answer'}
    assert 'generation' not in json.loads(result.model_dump_json())


@pytest.mark.parametrize('flag', ['false', '0', 'off', 'no'])
def test_server_off_preserves_legacy_response_even_with_user_opt_in(
        answerer, monkeypatch, flag):
    monkeypatch.setenv('HUS_LLM_ENABLED', flag)
    monkeypatch.setenv('HUS_LLM_MODEL', '')
    expected = chat(question(), answerer).model_dump()
    result = chat(question(allow_llm_rewrite=True), answerer, rewriter=forbidden)
    assert result.model_dump() == expected


@pytest.mark.parametrize('text,dataset,generated', [
    ('Giới thiệu ngành', 'f1', False),
    ('MAT3533 có bao nhiêu tín chỉ?', 'f2', False),
    ('Nội dung MAT3533?', 'f3', True),
])
def test_only_eligible_answers_reach_typed_adapter(answerer, text, dataset, generated):
    c = contracts()
    request = question(text, allow_llm_rewrite=True, allow_generated_reference=generated)
    original = chat(request.model_copy(update={'allow_llm_rewrite': False}), answerer).hus_answer
    before = original.model_dump()
    contexts = []

    def rewrite(context):
        contexts.append(context)
        assert context.answer.dataset == dataset
        assert context.answer.release_sha256 == original.release_sha256
        assert context.requested_model == 'gemini-3.5-flash-lite'
        if dataset == 'f2':
            return c.HUSF2Presentation(style='explain_source', model='gemini-3.5-flash-lite')
        return c.HUSTextRewrite(reply='Bản diễn đạt đã qua adapter kiểm chứng.',
                                model='gemini-3.5-flash-lite')

    result = chat(request, answerer, rewriter=rewrite)
    assert len(contexts) == 1
    assert result.generation.used is True
    assert result.generation.model == 'gemini-3.5-flash-lite'
    assert result.generation.fallback_reason is None
    assert result.hus_answer.model_dump() == before
    assert original.model_dump() == before
    if dataset == 'f2':
        assert result.reply.endswith(original.reply)
        assert result.hus_answer.facts['value'] == 3
    else:
        assert 'Bản diễn đạt đã qua adapter kiểm chứng.' in result.reply
        assert all(warning in result.reply for warning in original.warnings)
    if dataset == 'f3':
        assert all(item.display_label == 'kiến thức AI' for item in result.hus_answer.citations)


@pytest.mark.parametrize('text,generated,reason', [
    ('Xin chào', False, 'basic_chat'),
    ('Số tín chỉ MAT9999?', False, 'not_answered'),
    ('MAT3533 có tên gì, bao nhiêu tín chỉ và tiên quyết gì?', False, 'not_answered'),
    ('Nội dung MAT3533?', False, 'not_answered'),
])
def test_ineligible_requests_never_call_adapter(answerer, text, generated, reason):
    result = chat(question(text, allow_llm_rewrite=True,
                           allow_generated_reference=generated), answerer, rewriter=forbidden)
    assert result.generation.used is False
    assert result.generation.fallback_reason == reason
    assert result.generation.model is None


def test_f3_permission_never_implies_rewrite_permission(answerer):
    result = chat(question('Nội dung MAT3533?', allow_generated_reference=True),
                  answerer, rewriter=forbidden)
    assert result.hus_answer.status == 'answered'
    assert 'generation' not in result.model_dump()


def test_f3_guard_applies_even_to_incorrect_answerer_output(answerer):
    request = question('Nội dung MAT3533?', allow_generated_reference=True)
    original = chat(request, answerer).hus_answer
    fixed = SimpleNamespace(programs=answerer.programs, answer=lambda request: original)
    result = chat(request.model_copy(update={'allow_generated_reference': False,
                                            'allow_llm_rewrite': True}),
                  fixed, rewriter=forbidden)
    assert result.generation.fallback_reason == 'f3_opt_out'


def test_answered_without_citations_never_calls_adapter(answerer):
    original = chat(question(), answerer).hus_answer.model_copy(update={'citations': []})
    fixed = SimpleNamespace(programs=answerer.programs, answer=lambda request: original)
    result = chat(question(allow_llm_rewrite=True), fixed, rewriter=forbidden)
    assert result.reply == original.reply
    assert result.generation.fallback_reason == 'no_sources'


def test_unavailable_pipeline_has_explicit_fallback(answerer, monkeypatch):
    from app.hus.llm import adapter

    monkeypatch.setattr(adapter, 'get_default_rewriter', lambda settings: None)
    result = chat(question(allow_llm_rewrite=True), answerer)
    assert result.reply == result.hus_answer.reply
    assert result.generation.used is False
    assert result.generation.fallback_reason == 'pipeline_unavailable'
    assert result.generation.requested_model == 'gemini-3.5-flash-lite'
    assert result.generation.model is None


@pytest.mark.parametrize('key,value', [('HUS_LLM_ENABLED', 'wrong'),
                                      ('HUS_LLM_API_KEY', ''), ('HUS_LLM_MODEL', '')])
def test_bad_server_configuration_falls_back_safely(answerer, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    result = chat(question(allow_llm_rewrite=True), answerer, rewriter=forbidden)
    assert result.reply == result.hus_answer.reply
    assert result.generation.fallback_reason == 'configuration'
    assert 'synthetic-l2-key' not in result.model_dump_json()


def test_misconfigured_model_cannot_expose_key_in_metadata(answerer, monkeypatch):
    monkeypatch.setenv('HUS_LLM_MODEL', 'synthetic-l2-key')
    result = chat(question(allow_llm_rewrite=True), answerer, rewriter=forbidden)
    assert result.generation.fallback_reason == 'configuration'
    assert 'synthetic-l2-key' not in result.model_dump_json()


def test_adapter_mutation_cannot_change_nested_canonical_values(answerer):
    c = contracts()
    request = question('MAT3533 có bao nhiêu tín chỉ?', allow_llm_rewrite=True)
    original = chat(request.model_copy(update={'allow_llm_rewrite': False}), answerer).hus_answer
    before = deepcopy(original.model_dump())
    fixed = SimpleNamespace(programs=answerer.programs, answer=lambda request: original)

    def mutate(context):
        context.question.question = 'changed question'
        context.answer.facts['value'] = 999
        context.answer.citations[0].quote = 'forged quote'
        context.answer.citations[0].metadata['review_status'] = 'forged review'
        context.answer.warnings.clear()
        return c.HUSF2Presentation(style='direct', model='gemini-3.5-flash-lite')

    result = chat(request, fixed, rewriter=mutate)
    assert result.hus_answer.model_dump() == before
    assert result.reply.endswith(before['reply'])
    assert request.question == 'MAT3533 có bao nhiêu tín chỉ?'


@pytest.mark.parametrize('state,value', [('unknown', [None]), ('present', ['MAT1001']),
                                       ('unresolved', ['Mã chưa giải quyết']),
                                       ('conflict', ['MAT1001', 'MAT1002'])])
def test_f2_presentation_keeps_every_prerequisite_state(answerer, state, value):
    c = contracts()
    request = question('Tiên quyết MAT2400?', allow_llm_rewrite=True)
    original = chat(request.model_copy(update={'allow_llm_rewrite': False}), answerer).hus_answer
    original = original.model_copy(deep=True)
    original.facts['prerequisite_status'] = state
    original.facts['value'] = value
    original.reply = f'Trạng thái nguồn: {state}; dòng nguồn: {value!r}. Không kết luận đủ điều kiện.'
    fixed = SimpleNamespace(programs=answerer.programs, answer=lambda request: original)
    before = deepcopy(original.model_dump())
    result = chat(request, fixed, rewriter=lambda context: c.HUSF2Presentation(
        style='explain_source', model='gemini-3.5-flash-lite'))
    assert result.generation.used is True
    assert result.reply.endswith(original.reply)
    assert result.hus_answer.model_dump() == before


def test_f2_rejects_free_text_rewrite_even_if_well_typed(answerer):
    c = contracts()
    result = chat(question('MAT3533 có bao nhiêu tín chỉ?', allow_llm_rewrite=True),
                  answerer, rewriter=lambda context: c.HUSTextRewrite(
                      reply='MAT3533 có 999 tín chỉ.', model='gemini-3.5-flash-lite'))
    assert result.reply == result.hus_answer.reply
    assert result.hus_answer.facts['value'] == 3
    assert result.generation.fallback_reason == 'invalid_result'


@pytest.mark.parametrize('code', ['timeout', 'transport_error', 'http_error', 'invalid_response'])
def test_provider_errors_do_not_leak_or_modify_canonical(answerer, code, caplog):
    def fail(context):
        raise HUSLLMError(code, status_code=429 if code == 'http_error' else None)

    result = chat(question(allow_llm_rewrite=True), answerer, rewriter=fail)
    assert result.reply == result.hus_answer.reply
    assert result.generation.used is False
    assert result.generation.fallback_reason == code
    assert result.generation.model is None
    assert 'synthetic-l2-key' not in result.model_dump_json() + caplog.text


def test_unexpected_adapter_failure_is_sanitized(answerer, caplog):
    def fail(context):
        raise RuntimeError('synthetic-private-provider-body synthetic-l2-key')

    result = chat(question(allow_llm_rewrite=True), answerer, rewriter=fail)
    assert result.generation.fallback_reason == 'adapter_error'
    assert 'synthetic-private-provider-body' not in result.model_dump_json() + caplog.text


@pytest.mark.parametrize('value', ['unvalidated text', {'reply': 'unvalidated'}, None])
def test_untyped_adapter_output_is_not_published(answerer, value):
    result = chat(question(allow_llm_rewrite=True), answerer, rewriter=lambda context: value)
    assert result.reply == result.hus_answer.reply
    assert result.generation.fallback_reason == 'invalid_result'


@pytest.mark.parametrize('changes', [{'reply': ''}, {'reply': '   '},
                                     {'kind': 'facts'}, {'model': 'invalid model id'}])
def test_typed_result_still_requires_validated_contract(answerer, changes):
    c = contracts()
    result_data = {'reply': 'Nội dung từ nguồn.', 'model': 'gemini-3.5-flash-lite', **changes}
    result = chat(question(allow_llm_rewrite=True), answerer,
                  rewriter=lambda context: c.HUSTextRewrite.model_construct(**result_data))
    assert result.generation.used is False
    assert result.generation.fallback_reason == 'invalid_result'
    assert result.reply == result.hus_answer.reply


def test_canonical_data_error_still_fails_closed(answerer):
    def corrupt(request):
        raise RAGDataError('private canonical path')

    fixed = SimpleNamespace(programs=answerer.programs, answer=corrupt)
    with pytest.raises(RAGDataError):
        chat(question(allow_llm_rewrite=True), fixed, rewriter=forbidden)


def test_adapter_canonical_error_is_not_swallowed(answerer):
    def corrupt(context):
        raise RAGDataError('private canonical path')

    with pytest.raises(RAGDataError):
        chat(question(allow_llm_rewrite=True), answerer, rewriter=corrupt)


def test_reported_model_is_adapter_returned_model(answerer):
    c = contracts()
    result = chat(question(allow_llm_rewrite=True), answerer, rewriter=lambda context:
                  c.HUSTextRewrite(reply='Nội dung đã kiểm.', model='returned-model-version'))
    assert result.generation.requested_model == 'gemini-3.5-flash-lite'
    assert result.generation.model == 'returned-model-version'


@pytest.mark.parametrize('text,generated', [('Giới thiệu ngành', False),
    ('MAT3533 có bao nhiêu tín chỉ?', False), ('Nội dung MAT3533?', True)])
def test_actual_api_serializes_success_without_changing_canonical(monkeypatch, text, generated):
    from app.hus import demo

    c = contracts()

    def rewrite(context):
        if context.answer.dataset == 'f2':
            return c.HUSF2Presentation(style='direct', model='gemini-3.5-flash-lite')
        return c.HUSTextRewrite(reply='Nội dung được diễn đạt.', model='gemini-3.5-flash-lite')

    monkeypatch.setattr(demo, 'chat', lambda request, answerer: chat(
        request, answerer, rewriter=rewrite))
    payload = {'question': text, 'major': 'data_science', 'version': 'QD3569-2023',
               'allow_generated_reference': generated}
    with TestClient(demo.app) as client:
        original = client.post('/hus/chat', json=payload).json()
        response = client.post('/hus/chat', json={**payload, 'allow_llm_rewrite': True})
    assert response.status_code == 200
    result = response.json()
    assert result['generation']['used'] is True
    assert result['generation']['model'] == 'gemini-3.5-flash-lite'
    assert result['hus_answer'] == original['hus_answer']


def test_actual_api_preserves_legacy_keys_and_reports_missing_pipeline(monkeypatch):
    from app.hus.demo import app
    from app.hus.llm import adapter

    monkeypatch.setattr(adapter, 'get_default_rewriter', lambda settings: None)

    with TestClient(app) as client:
        payload = {'question': 'Giới thiệu ngành', 'major': 'data_science', 'version': 'QD3569-2023'}
        before = client.post('/hus/chat', json=payload)
        assert before.status_code == 200
        assert set(before.json()) == {'mode', 'reply', 'hus_answer'}
        response = client.post('/hus/chat', json={**payload, 'allow_llm_rewrite': True})
        assert response.status_code == 200
        result = response.json()
        assert result['generation']['fallback_reason'] == 'pipeline_unavailable'
        assert result['generation']['used'] is False
        assert result['hus_answer'] == before.json()['hus_answer']
        assert result['reply'] == before.json()['reply']
        assert client.post('/hus/chat', json={**payload, 'allow_llm_rewrite': 'true'}).status_code == 422
        assert client.post('/hus/chat', json={**payload, 'rewriter': 'remote'}).status_code == 422
