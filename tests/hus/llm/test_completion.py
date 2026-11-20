"""Actual provider envelope is distinct from the requested model/generated JSON."""

import httpx
import pytest

from app.hus.llm import HUSLLMClient, HUSLLMError, HUSLLMSettings


def envelope(**overrides):
    data = {'id': 'chatcmpl-offline', 'object': 'chat.completion', 'created': 0,
            'model': 'actual-model-version',
            'choices': [{'index': 0, 'finish_reason': 'stop',
                         'message': {'role': 'assistant', 'content': ' {"kind":"facts"} '}}],
            'usage': {'prompt_tokens': 8, 'completion_tokens': 5, 'total_tokens': 13}}
    data.update(overrides)
    return data


def client(body):
    return HUSLLMClient(HUSLLMSettings(enabled=True, api_key='synthetic-completion-key'),
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body)))


def test_completion_exposes_actual_model_and_provider_usage():
    result = client(envelope()).complete_result([{'role': 'user', 'content': 'Return JSON.'}])
    assert result.content == ' {"kind":"facts"} '
    assert result.model == 'actual-model-version'
    assert result.usage.prompt_tokens == 8
    assert result.usage.completion_tokens == 5
    assert result.usage.total_tokens == 13


def test_text_api_still_returns_only_trimmed_text():
    assert client(envelope()).complete([{'role': 'user', 'content': 'Return JSON.'}]) == (
        '{"kind":"facts"}')


@pytest.mark.parametrize('model', [None, '', ' ', [], 1, 'bad model', '<script>', 'x' * 101])
def test_missing_or_malformed_returned_model_is_not_replaced_by_requested_model(model):
    with pytest.raises(HUSLLMError) as error:
        client(envelope(model=model)).complete_result([{'role': 'user', 'content': 'hello'}])
    assert error.value.code == 'invalid_response'


def test_returned_key_cannot_become_model_metadata():
    with pytest.raises(HUSLLMError) as error:
        client(envelope(model='synthetic-completion-key')).complete_result(
            [{'role': 'user', 'content': 'hello'}])
    assert error.value.code == 'invalid_response'
    assert 'synthetic-completion-key' not in str(error.value)


@pytest.mark.parametrize('usage', [None, {}])
def test_absent_usage_is_unknown_not_fabricated(usage):
    result = client(envelope(usage=usage)).complete_result([{'role': 'user', 'content': 'hello'}])
    assert result.usage is None


@pytest.mark.parametrize('usage', [[], {'prompt_tokens': True}, {'completion_tokens': -1},
                                  {'total_tokens': '13'}, {'completion_tokens': 1.2}])
def test_invalid_usage_is_not_reported_as_valid(usage):
    with pytest.raises(HUSLLMError) as error:
        client(envelope(usage=usage)).complete_result([{'role': 'user', 'content': 'hello'}])
    assert error.value.code == 'invalid_response'


def test_usage_details_are_not_copied_into_metadata():
    body = envelope(usage={'prompt_tokens': 8, 'completion_tokens': 5, 'total_tokens': 13,
                           'provider_debug': {'private': 'must-not-leave-envelope'}})
    result = client(body).complete_result([{'role': 'user', 'content': 'hello'}])
    assert result.usage.model_dump() == {'prompt_tokens': 8, 'completion_tokens': 5,
                                        'total_tokens': 13}


def test_reported_output_over_token_budget_is_rejected():
    with pytest.raises(HUSLLMError) as error:
        client(envelope(usage={'completion_tokens': 1025})).complete_result(
            [{'role': 'user', 'content': 'hello'}])
    assert error.value.code == 'output_budget'


@pytest.mark.parametrize('extra', [{'tool_calls': [{'id': 'unsafe', 'type': 'function',
    'function': {'name': 'fetch', 'arguments': '{}'}}]},
    {'function_call': {'name': 'fetch', 'arguments': '{}'}}])
def test_provider_tool_output_never_becomes_a_completion(extra):
    body = envelope()
    body['choices'][0]['message'].update(extra)
    with pytest.raises(HUSLLMError) as error:
        client(body).complete_result([{'role': 'user', 'content': 'hello'}])
    assert error.value.code == 'invalid_response'
