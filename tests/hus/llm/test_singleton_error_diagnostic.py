"""Synthetic singleton failures; ambiguous arrays never become provider causes."""
import json

import httpx
import pytest

from app.hus.llm import HUSLLMClient, HUSLLMError, HUSLLMSettings
from app.hus.llm.diagnostics import http_error_diagnostic

LEAKED = {'error': {'status': 'PERMISSION_DENIED',
                    'message': 'Your API key was reported as leaked. synthetic-only-secret'}}


@pytest.mark.parametrize('body', [[], [None], ['private'], [42], [True], [[LEAKED]],
                                [LEAKED, {}], [{}, LEAKED], [LEAKED, LEAKED],
                                [{'error': [LEAKED]}], [{'untrusted': LEAKED}]])
def test_ambiguous_or_nested_arrays_remain_unspecified(body):
    diagnostic = http_error_diagnostic(body, 403)
    assert diagnostic.provider_status == 'other'
    assert diagnostic.access_issue == 'unspecified'
    assert 'synthetic-only-secret' not in diagnostic.model_dump_json()


def test_singleton_retains_message_and_body_limits():
    message = 'Your API key was reported as leaked.'
    for length, expected in ((8192, 'key_reported_leaked'), (8193, 'unspecified')):
        body = [{'error': {'status': 'PERMISSION_DENIED',
                            'message': message + 'x' * (length - len(message))}}]
        assert http_error_diagnostic(body, 403).access_issue == expected
    body = [dict(LEAKED, private_padding='x' * 16385)]
    assert len(json.dumps(body).encode()) > 16384
    client = HUSLLMClient(HUSLLMSettings(enabled=True, api_key='synthetic-only-secret'),
        transport=httpx.MockTransport(lambda request: httpx.Response(403, json=body)))
    with pytest.raises(HUSLLMError) as raised:
        client.complete([{'role': 'user', 'content': 'Public synthetic evidence'}])
    assert raised.value.diagnostic.provider_status == 'other'
    assert raised.value.diagnostic.access_issue == 'unspecified'


def test_singleton_success_response_is_not_unwrapped_as_completion():
    completion = [{'model': 'synthetic-model', 'choices': [
        {'finish_reason': 'stop', 'message': {'content': 'Synthetic output'}}]}]
    client = HUSLLMClient(HUSLLMSettings(enabled=True, api_key='synthetic-only-secret'),
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=completion)))
    with pytest.raises(HUSLLMError) as raised:
        client.complete([{'role': 'user', 'content': 'Public synthetic evidence'}])
    assert raised.value.code == 'invalid_response'
    assert raised.value.diagnostic.stage == 'provider_envelope'
