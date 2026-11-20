"""Actual automatic policy/adapter/validator, synthetic completion only."""
import json
from types import SimpleNamespace

import pytest

from app.hus.answering import HUSAnswerer
from app.hus.llm.adapter import HUSGroundedAdapter
from app.hus.llm.auto import AutoLLMPolicy, AutoLLMUnavailable
from app.hus.llm.client import HUSCompletion, HUSLLMError
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion


@pytest.fixture(scope='module')
def data():
    return HUSRAGData.load_current()


@pytest.fixture
def setup(data, monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-focused-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'synthetic')
    monkeypatch.setenv('HUS_LLM_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai')
    monkeypatch.setenv('HUS_LLM_INTENT_ENABLED', 'false')
    state = {'error': None, 'bad_output': False, 'calls': []}
    def complete(messages):
        state['calls'].append(messages)
        if state['error']:
            raise HUSLLMError('http_error', status_code=state['error'])
        value = json.loads(messages[1]['content'])
        if value['scope']['dataset'] == 'f2':
            result = {'kind':'facts','style':'direct','fact_keys':list(value['facts']),
                      'citation_ids':[s['citation_id'] for s in value['sources']]}
        else:
            result = {'kind':'focused_rewrite_v1','items':[
                {'unit_id':u['id'], 'text':u['text']} for u in value['units']]}
            if state['bad_output']:
                result['items'][0]['text'] = 'Không ' + result['items'][0]['text']
        return HUSCompletion(json.dumps(result, ensure_ascii=False), 'synthetic')
    client = SimpleNamespace(settings=SimpleNamespace(enabled=True, model='synthetic', api_key='synthetic-focused-key'),
                             complete_result=complete)
    return HUSAnswerer(data, answer_policy='focused'), AutoLLMPolicy(), HUSGroundedAdapter(client), state


def question(text='Trong nội dung MAT1202, các đối tượng và kế thừa được giải thích thế nào?'):
    return HUSQuestion(question=text, major='mathematics_informatics', version='QD3567-2023',
                       allow_generated_reference=True)


def test_focused_adapter_used_and_canonical_context_is_retained(setup):
    answerer, policy, adapter, state = setup
    result = policy.reply(question(), answerer, rewriter=adapter)
    assert result.generation.used and len(state['calls']) == 1
    assert 'focused_rewrite_v1' in state['calls'][0][0]['content']
    assert 'Ví dụ minh họa' not in result.reply
    assert all('Ví dụ minh họa' in c.quote for c in result.hus_answer.citations)
    assert 'focus_plan' not in result.model_dump()['hus_answer']


def test_f2_uses_original_facts_protocol_even_under_focused_policy(setup):
    answerer, policy, adapter, state = setup
    result = policy.reply(question('MAT1202 có bao nhiêu tín chỉ?'), answerer, rewriter=adapter)
    assert result.generation.used and result.hus_answer.facts['value'] == 3
    assert result.hus_answer.focus_plan is None
    assert 'F2 presentation protocol' in state['calls'][0][0]['content']


@pytest.mark.parametrize('error', [401,403,503])
def test_nonquota_failures_never_silently_return_offline(setup, error):
    answerer, policy, adapter, state = setup
    state['error'] = error
    with pytest.raises(AutoLLMUnavailable):
        policy.reply(question(), answerer, rewriter=adapter)
    assert not policy.quota_exhausted and len(state['calls']) == 1


def test_invalid_output_is_an_error_without_offline_substitution(setup):
    answerer, policy, adapter, state = setup
    state['bad_output'] = True
    with pytest.raises(AutoLLMUnavailable) as error:
        policy.reply(question(), answerer, rewriter=adapter)
    assert error.value.diagnostic.code == 'output_rejected'
    assert len(state['calls']) == 1 and not policy.quota_exhausted


def test_quota_latches_and_uses_the_same_checked_offline_spans(setup):
    answerer, policy, adapter, state = setup
    state['error'] = 429
    first = policy.reply(question(), answerer, rewriter=adapter)
    assert not first.generation.used and first.generation.http_status == 429
    assert policy.quota_exhausted and len(state['calls']) == 1
    second = policy.reply(question(), answerer, rewriter=adapter)
    assert second.reply == first.reply and len(state['calls']) == 1


def test_ambiguous_source_never_calls_generation(setup):
    answerer, policy, adapter, state = setup
    request = HUSQuestion(question='Ngành KHMTTT có thể học tiếp sau đại học như thế nào?',
        major='computer_science', version='QD3568-2023')
    result = policy.reply(request, answerer, rewriter=adapter)
    assert result.hus_answer.source_choices and not state['calls']
