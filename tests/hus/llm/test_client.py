"""L1 exercises the real adapter against offline HTTP transports."""

import importlib
import json
import subprocess
import sys
from pathlib import Path

import httpx
import pytest


@pytest.fixture
def api():
    # Keep the initial RED run an assertion failure rather than collection errors.
    assert importlib.util.find_spec('app.hus.llm') is not None, 'L1 package missing'
    return importlib.import_module('app.hus.llm')


def settings(api, **overrides):
    return api.HUSLLMSettings(enabled=True, api_key='synthetic-gemini-key', **overrides)


def no_request(request):
    pytest.fail('Disabled/invalid configuration must never send HTTP')


def completion(content='Nội dung từ nguồn.', **overrides):
    choice = {'index': 0, 'message': {'role': 'assistant', 'content': content},
              'finish_reason': 'stop'}
    choice.update(overrides)
    return {'id': 'chatcmpl-synthetic', 'object': 'chat.completion', 'created': 0,
            'model': 'gemini-3.5-flash-lite', 'choices': [choice],
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5, 'total_tokens': 15}}


def test_defaults_disable_requests_without_key(api):
    config = api.HUSLLMSettings.from_env({})
    client = api.HUSLLMClient(config, transport=httpx.MockTransport(no_request))
    with pytest.raises(api.HUSLLMError) as error:
        client.complete([{'role': 'user', 'content': 'Xin chào'}])
    assert error.value.code == 'disabled'
    assert error.value.status_code is None


def test_enabled_requires_own_key_not_recommendation_key(api):
    with pytest.raises(ValueError, match='HUS_LLM_API_KEY'):
        api.HUSLLMSettings.from_env({'HUS_LLM_ENABLED': 'true', 'GEMINI_API_KEY': 'other'})


@pytest.mark.parametrize('value', ['', ' ', 'truee', 'enabled', None, True])
def test_invalid_enabled_value_rejected(api, value):
    with pytest.raises(ValueError, match='HUS_LLM_ENABLED'):
        api.HUSLLMSettings.from_env({'HUS_LLM_ENABLED': value})


@pytest.mark.parametrize('value', ['false', '0', 'off', 'no', ' FALSE '])
def test_explicit_false_values_never_send_http(api, value):
    config = api.HUSLLMSettings.from_env({'HUS_LLM_ENABLED': value,
                                        'HUS_LLM_API_KEY': 'synthetic'})
    with pytest.raises(api.HUSLLMError) as error:
        api.HUSLLMClient(config, transport=httpx.MockTransport(no_request)).complete(
            [{'role': 'user', 'content': 'hello'}])
    assert error.value.code == 'disabled'


@pytest.mark.parametrize('field,value', [
    ('base_url', ''), ('base_url', '/v1'), ('base_url', 'ftp://localhost/v1'),
    ('base_url', 'http://'), ('base_url', 'http://localhost:invalid/v1'),
    ('base_url', 'http://localhost:99999/v1'), ('base_url', 'http://localhost/v1?key=secret'),
    ('base_url', 'http://localhost/v1#fragment'),
    ('base_url', 'http://user:secret@localhost/v1'),
    ('base_url', 'http://local\nhost/v1'), ('base_url', None),
    ('base_url', 'http://local\x00host/v1'), ('base_url', 'http://localhost/v1\x7f'),
    ('base_url', 'http://[::1]junk/v1'), ('base_url', 'http://\u200d.example/v1'),
    ('base_url', 'http://localhost/v1?'), ('base_url', 'http://localhost/v1#'),
    ('model', ''), ('model', '  '), ('model', None), ('model', 'model\nsecret'),
    ('api_key', ' '), ('api_key', 'key\nsecret'), ('api_key', None),
    ('enabled', 'false'),
])
def test_bad_direct_configuration_rejected_before_http(api, field, value):
    values = {'enabled': True, 'api_key': 'synthetic-gemini-key', field: value}
    with pytest.raises(ValueError):
        api.HUSLLMSettings(**values)


def test_secret_never_appears_in_config_repr_or_validation_error(api):
    secret = 'synthetic-private-key'
    assert secret not in repr(api.HUSLLMSettings(enabled=True, api_key=secret))
    with pytest.raises(ValueError) as error:
        api.HUSLLMSettings(enabled=True, api_key=secret + '\n')
    assert secret not in str(error.value)


@pytest.mark.parametrize('config_source', ['constructor', 'env'])
@pytest.mark.parametrize('base_url', [None,
    'https://generativelanguage.googleapis.com/v1beta/openai',
    'https://generativelanguage.googleapis.com/v1beta/openai/'])
def test_success_calls_google_directly_and_returns_text(api, base_url, config_source):
    requests = []
    messages = [{'role': 'system', 'content': 'Chỉ dùng nguồn.'},
                {'role': 'user', 'content': 'Nội dung?'}]

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=completion('  Nội dung từ nguồn.  '))

    if config_source == 'env':
        env = {'HUS_LLM_ENABLED': 'true', 'HUS_LLM_API_KEY': 'synthetic-gemini-key'}
        if base_url is not None:
            env['HUS_LLM_BASE_URL'] = base_url
        config = api.HUSLLMSettings.from_env(env)
    else:
        config = settings(api, **({'base_url': base_url} if base_url is not None else {}))
    result = api.HUSLLMClient(config, transport=httpx.MockTransport(respond)).complete(messages)
    assert result == 'Nội dung từ nguồn.'
    assert len(requests) == 1
    request = requests[0]
    assert request.method == 'POST'
    assert str(request.url) == (
        'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions')
    assert request.headers['authorization'] == 'Bearer synthetic-gemini-key'
    assert request.headers['content-type'] == 'application/json'
    assert json.loads(request.content) == {
        'model': 'gemini-3.5-flash-lite', 'messages': messages,
        'stream': False, 'max_tokens': 1024,
    }
    assert request.extensions['timeout'] == {
        'connect': 20.0, 'read': 20.0, 'write': 20.0, 'pool': 20.0,
    }


def test_from_env_uses_separate_explicit_endpoint_and_model(api):
    config = api.HUSLLMSettings.from_env({
        'HUS_LLM_ENABLED': 'true', 'HUS_LLM_API_KEY': 'synthetic-gemini-key',
        'HUS_LLM_BASE_URL': 'https://custom.example/v1/', 'HUS_LLM_MODEL': 'custom-model',
        'GEMINI_MODEL': 'wrong-model', 'GEMINI_BASE_URL': 'https://wrong.example',
    })
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=completion())

    api.HUSLLMClient(config, transport=httpx.MockTransport(respond)).complete(
        [{'role': 'user', 'content': 'hello'}])
    assert str(requests[0].url) == 'https://custom.example/v1/chat/completions'
    assert json.loads(requests[0].content)['model'] == 'custom-model'


@pytest.mark.parametrize('status', [301, 401, 403, 429, 500, 503])
def test_http_errors_are_sanitized_without_retry_or_redirect(api, status, caplog):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(status, text='synthetic-private-provider-body',
                              headers={'location': 'https://other.example/secret'})

    client = api.HUSLLMClient(settings(api), transport=httpx.MockTransport(respond))
    with pytest.raises(api.HUSLLMError) as error:
        client.complete([{'role': 'user', 'content': 'synthetic-private-question'}])
    assert error.value.code == 'http_error'
    assert error.value.status_code == status
    assert len(requests) == 1
    for secret in ('synthetic-gemini-key', 'synthetic-private-provider-body',
                   'synthetic-private-question'):
        assert secret not in str(error.value) + caplog.text
    assert error.value.__suppress_context__


@pytest.mark.parametrize('exception,code', [(httpx.ReadTimeout, 'timeout'),
                                           (httpx.ConnectError, 'transport_error')])
def test_network_failures_have_stable_safe_errors(api, exception, code):
    def fail(request):
        raise exception('synthetic-private-provider-detail', request=request)

    client = api.HUSLLMClient(settings(api), transport=httpx.MockTransport(fail))
    with pytest.raises(api.HUSLLMError) as error:
        client.complete([{'role': 'user', 'content': 'hello'}])
    assert error.value.code == code
    assert 'synthetic-private-provider-detail' not in str(error.value)
    assert error.value.__suppress_context__


@pytest.mark.parametrize('body', [None, [], {}, {'choices': []}, {'choices': [None]},
                               completion(None), completion('  '), completion(['text']),
                               completion('partial', finish_reason='length'),
                               completion('blocked', finish_reason='content_filter')])
def test_invalid_or_incomplete_responses_are_not_success(api, body):
    client = api.HUSLLMClient(settings(api), transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=body)))
    with pytest.raises(api.HUSLLMError) as error:
        client.complete([{'role': 'user', 'content': 'hello'}])
    assert error.value.code == 'invalid_response'


def test_non_json_success_response_is_rejected(api):
    client = api.HUSLLMClient(settings(api), transport=httpx.MockTransport(
        lambda request: httpx.Response(200, text='<html>synthetic-private-body</html>')))
    with pytest.raises(api.HUSLLMError) as error:
        client.complete([{'role': 'user', 'content': 'hello'}])
    assert error.value.code == 'invalid_response'
    assert 'synthetic-private-body' not in str(error.value)


@pytest.mark.parametrize('messages', [[], 'hello', [{'role': 'user', 'content': ''}],
                                     [{'role': 'tool', 'content': 'hello'}],
                                     [{'role': 'user', 'content': None}]])
def test_bad_messages_rejected_before_http(api, messages):
    client = api.HUSLLMClient(settings(api), transport=httpx.MockTransport(no_request))
    with pytest.raises(ValueError, match='messages'):
        client.complete(messages)


def test_import_and_construction_do_not_load_recommendation_or_connect(api):
    script = '''
import importlib.abc
import socket
import sys
import httpx

class BlockRecommendation(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith(('app.services', 'app.recommendation', 'app.config')):
            raise AssertionError('Forbidden dependency: ' + fullname)

def forbidden(*args, **kwargs):
    raise AssertionError('L1 import/construction must not initialize HTTP or connect')

sys.meta_path.insert(0, BlockRecommendation())
socket.socket.connect = forbidden
httpx.Client = forbidden
from app.hus.llm import HUSLLMClient, HUSLLMSettings
HUSLLMClient(HUSLLMSettings(enabled=True, api_key='synthetic'))
print('L1-isolated')
'''
    result = subprocess.run([sys.executable, '-c', script], capture_output=True,
                            text=True, cwd=Path(__file__).resolve().parents[3], timeout=20)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == 'L1-isolated'


def test_application_startup_with_llm_enabled_never_calls_provider(monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-gemini-key')
    from app.main import app

    with TestClient(app) as client:
        assert client.get('/health').status_code == 200
