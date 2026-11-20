"""Default v3, unchanged F2 and safe failure diagnostics; synthetic transport only."""
import json
import traceback

import httpx
import pytest

from app.hus.chat import chat
from app.hus.llm import HUSLLMClient, HUSLLMError, HUSLLMSettings
from tests.hus.llm.fixtures import context, facts_output, text_output
from tests.hus.llm.test_compact_document import document
from tests.hus.llm.test_compact_output import check, copied
from tests.hus.llm.test_evaluation import prepared  # noqa: F401 -- pytest fixture
from tests.hus.llm.test_pipeline import completion, fixed_answerer, transport


@pytest.fixture(autouse=True)
def settings(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-compact-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'gemini-3.5-flash-lite')
    monkeypatch.setenv('HUS_LLM_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai')


def wire_output(request):
    payload = json.loads(json.loads(request.content)['messages'][1]['content'])
    if payload['scope']['dataset'] == 'f2':
        return facts_output()
    return {'kind': 'rewrite_v3', 'items': [{'id': s['id'], 'text': s['text']}
                for source in payload['sources'] for s in source['segments']]}


@pytest.mark.parametrize('family', ['f1', 'f2', 'f3'])
def test_default_adapter_and_actual_wire_protocol_match(family, monkeypatch):
    ctx = context(family)
    original = ctx.answer.model_dump_json()
    calls = transport(monkeypatch, lambda r: httpx.Response(200, json=completion(wire_output(r))))
    reply = chat(ctx.question, fixed_answerer(ctx))
    assert reply.generation.used is True
    assert reply.hus_answer.model_dump_json() == original
    payload = json.loads(json.loads(calls[0].content)['messages'][1]['content'])
    assert payload['schema_version'] == ('hus-llm-evidence-v1' if family == 'f2' else 'hus-llm-document-v3')
    if family == 'f2':
        assert reply.reply.endswith(ctx.answer.reply)
    else:
        assert all('quote' not in s and s['segments'] for s in payload['sources'])


def test_legacy_points_are_not_silently_accepted_on_default_v3(monkeypatch):
    ctx = context()
    calls = transport(monkeypatch, lambda r: httpx.Response(200, json=completion(text_output())))
    result = chat(ctx.question, fixed_answerer(ctx))
    assert len(calls) == 1 and result.generation.used is False
    assert result.generation.fallback_reason == 'invalid_output' and result.reply == ctx.answer.reply


def test_leaf_count_preflight_falls_back_without_sending_http(monkeypatch):
    ctx = context()
    ctx.answer.citations = [ctx.answer.citations[0]]
    ctx.answer.citations[0].quote = '\n'.join('Một ý nguồn cần giữ.' for _ in range(65))
    calls = transport(monkeypatch, lambda r: pytest.fail('Structure cap was ignored'))
    result = chat(ctx.question, fixed_answerer(ctx))
    assert calls == [] and result.reply == ctx.answer.reply
    assert result.generation.fallback_reason == 'prompt_budget'


@pytest.mark.parametrize('finish,reason,stage', [('length', 'invalid_response', 'provider_envelope'),
                                              ('PRIVATE_PROVIDER_REASON', 'invalid_response', 'provider_envelope'),
                                              ('stop', 'output_budget', 'provider_budget')])
def test_client_error_diagnostics_never_contain_provider_text_or_unknown_finish(finish, reason, stage):
    body = completion({'private_provider_text': 'PRIVATE_COMPLETION_BODY'})
    body['choices'][0]['finish_reason'] = finish
    if finish == 'stop':
        body['usage']['completion_tokens'] = 1025
    client = HUSLLMClient(HUSLLMSettings(enabled=True, api_key='synthetic-compact-key'),
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=body)))
    with pytest.raises(HUSLLMError) as error:
        client.complete_result([{'role': 'user', 'content': 'Synthetic diagnostic'}])
    assert error.value.code == reason
    diagnostic = error.value.diagnostic.model_dump(exclude_none=True)
    assert diagnostic['stage'] == stage
    assert diagnostic['finish_reason'] == ('other' if finish.startswith('PRIVATE') else finish)
    assert diagnostic['content_kind'] == 'text' and diagnostic['content_chars'] > 0
    assert 'PRIVATE' not in json.dumps(diagnostic) and 'PRIVATE' not in str(error.value)


@pytest.mark.parametrize('failure,stage,leaf_id', [('json', 'output_json', None),
    ('schema', 'output_schema', None), ('unknown', 'output_ids', None),
    ('coverage', 'output_coverage', 'b001'), ('number', 'output_atoms', 'b001')])
def test_validator_diagnostics_have_stage_and_only_known_leaf_ids(failure, stage, leaf_id):
    doc = document('Nguồn có điều kiện; không bảo đảm kết quả.')
    value = copied(doc)
    if failure == 'json':
        value = '{PRIVATE_UNPARSED_BODY'
    elif failure == 'schema':
        value['kind'] = 'PRIVATE_UNKNOWN_KIND'
    elif failure == 'unknown':
        value['items'][0]['id'] = 'b999'
    elif failure == 'coverage':
        value['items'][0]['text'] = 'Nguồn có điều kiện.'
    else:
        value['items'][0]['text'] += ' Có 17 học phần.'
    with pytest.raises(HUSLLMError) as error:
        check(doc, value)
    safe = error.value.diagnostic.model_dump(exclude_none=True)
    assert safe['stage'] == stage and safe.get('leaf_id') == leaf_id
    assert 'PRIVATE' not in json.dumps(safe) and 'b999' not in json.dumps(safe)


def test_measurement_trace_records_adapter_validation_stage_without_rejected_text(prepared, tmp_path):  # noqa: F811
    from tools import evaluate_hus_llm as engine

    body = completion({'kind': 'PRIVATE_INVALID_KIND'})
    result = engine.run(prepared, tmp_path / 'observed', HUSLLMSettings(enabled=True, api_key='synthetic-compact-key'),
        transport_factory=lambda: httpx.MockTransport(lambda r: httpx.Response(200, json=body)), min_interval=0)
    assert result['metrics']['provider_requests'] == 3
    saved = engine.read_sealed(tmp_path / 'observed')['observations.json']
    assert saved[0]['trace']['validation']['stage'] == 'output_schema'
    assert saved[0]['trace']['provider_envelope']['finish_reason'] == 'stop'
    assert 'PRIVATE_INVALID_KIND' not in json.dumps(saved)
    assert 'PRIVATE' not in json.dumps([o['trace'] for o in saved])


def test_rejected_schema_traceback_does_not_echo_provider_content():
    needle = 'PRIVATE_' + 'REJECTED_OUTPUT'
    value = {'kind': needle, 'items': []}
    doc = document('Nội dung nguồn công khai.')
    with pytest.raises(HUSLLMError) as error:
        check(doc, value)
    assert needle not in ''.join(traceback.format_exception(error.value))
