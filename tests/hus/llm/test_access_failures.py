"""Provider error privacy and bounded L5 failure circuits, entirely offline."""

import json

import httpx
import pytest
from pydantic import ValidationError

from app.hus.llm import HUSLLMClient, HUSLLMError, HUSLLMSettings
from app.hus.llm.diagnostics import HUSLLMDiagnostic
from tests.hus.llm import test_evaluation as evaluation_fixtures
from tools import evaluate_hus_llm as evaluator

prepared = evaluation_fixtures.prepared
good = evaluation_fixtures.good
settings = evaluation_fixtures.settings


@pytest.mark.parametrize('error,issue,status', [
    ({'status': 'PERMISSION_DENIED', 'message': 'Your API key was reported as leaked. Use another key.'},
     'key_reported_leaked', 'PERMISSION_DENIED'),
    ({'code': 'permission_denied', 'message': 'Your project has been denied access'},
     'project_access_denied', 'PERMISSION_DENIED'),
    ({'status': 'PERMISSION_DENIED', 'message': 'FREE_TIER_VERIFICATION_REQUIRED'},
     'verification_required', 'PERMISSION_DENIED'),
    ({'status': 'PERMISSION_DENIED', 'details': [{'reason': 'FREE_TIER_VERIFICATION_REQUIRED'}]},
     'verification_required', 'PERMISSION_DENIED'),
    ({'code': 403, 'message': 'private opaque error'}, 'unspecified', 'other'),
    ({'status': 'PERMISSION_DENIED', 'message': 'Permission denied'}, 'unspecified', 'PERMISSION_DENIED'),
    ({'status': 'private-dynamic-status', 'code': 'private-code'}, 'unspecified', 'other'),
    ({'status': ['PERMISSION_DENIED'], 'message': {'private': 'value'}}, 'unspecified', 'other'),
])
@pytest.mark.parametrize('singleton_array', [False, True], ids=['object', 'singleton-array'])
def test_only_fixed_provider_error_labels_survive(error, issue, status, singleton_array):
    secret = 'synthetic-access-secret'
    response = {'error': {**error, 'metadata': {'key': secret, 'project': 'private-project'}},
                'request': secret, 'debug': 'private-debug'}
    response = [response] if singleton_array else response
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(403, json=response, headers={'private-header': secret})

    client = HUSLLMClient(HUSLLMSettings(enabled=True, api_key=secret), transport=httpx.MockTransport(respond))
    with pytest.raises(HUSLLMError) as raised:
        client.complete_result([{'role': 'user', 'content': 'Public test question'}])
    failure = raised.value
    assert len(calls) == 1 and failure.code == 'http_error' and failure.status_code == 403
    assert failure.diagnostic.model_dump(exclude_none=True) == {
        'stage': 'provider_http', 'provider_status': status, 'access_issue': issue}
    safe = str(failure) + repr(failure.diagnostic)
    assert all(value not in safe for value in (secret, 'private-project', 'private-debug', 'private-header'))


@pytest.mark.parametrize('body', [b'private-not-json', b'[]', b'{"error":null}',
                                 b'{"error":"private-value"}', b'x' * 16385])
def test_unknown_or_oversize_error_does_not_invent_a_cause(body):
    client = HUSLLMClient(HUSLLMSettings(enabled=True, api_key='synthetic-access-secret'),
                         transport=httpx.MockTransport(lambda request: httpx.Response(403, content=body)))
    with pytest.raises(HUSLLMError) as raised:
        client.complete([{'role': 'user', 'content': 'Public test question'}])
    assert raised.value.diagnostic.provider_status == 'other'
    assert raised.value.diagnostic.access_issue == 'unspecified'


@pytest.mark.parametrize('singleton_array', [False, True])
def test_access_label_does_not_follow_message_on_unrelated_http_status(singleton_array):
    body = {'error': {'message': 'Your API key was reported as leaked.'}}
    body = [body] if singleton_array else body
    client = HUSLLMClient(HUSLLMSettings(enabled=True, api_key='synthetic-access-secret'),
        transport=httpx.MockTransport(lambda request: httpx.Response(500, json=body)))
    with pytest.raises(HUSLLMError) as raised:
        client.complete([{'role': 'user', 'content': 'Public test question'}])
    assert raised.value.diagnostic.access_issue == 'unspecified'


@pytest.mark.parametrize('field,value', [('provider_status', 'private-status'),
                                        ('access_issue', 'private-message'), ('message', 'private-message')])
def test_error_diagnostic_schema_cannot_store_free_text(field, value):
    with pytest.raises(ValidationError):
        HUSLLMDiagnostic(stage='provider_http', **{field: value})


@pytest.mark.parametrize('statuses,expected_calls,stop', [
    ([403, 403, 200], 2, 'permission_denied'),
    ([401, 200, 200], 1, 'authentication'),
    ([429, 200, 200], 1, 'quota'),
    ([403, 200, 403], 3, None),
    ([403, 500, 403], 3, None),
    ([500, 500, 200], 3, None),
])
def test_failure_circuit_preserves_remaining_baseline_and_controls(
        prepared, tmp_path, statuses, expected_calls, stop):
    calls = []

    def respond(request):
        status = statuses[len(calls)]
        calls.append(request)
        if status == 200:
            return good(request)
        return httpx.Response(status, json={'error': {'status': 'PERMISSION_DENIED',
            'message': 'private-message synthetic-eval-key', 'details': [{'project': 'private-project'}]}})

    folder = tmp_path / 'run'
    report = evaluator.run(prepared, folder, settings(),
                           transport_factory=lambda: httpx.MockTransport(respond), min_interval=0)
    saved = evaluator.read_sealed(folder)['observations.json']
    assert len(calls) == expected_calls and report['metrics']['provider_requests'] == expected_calls
    assert report['evaluation_stop_reason'] == stop
    assert report['metrics']['eligible_not_attempted'] == 3 - expected_calls
    assert report['collection_complete'] is (stop is None)
    assert len(saved) == 4 and saved[-1]['trace']['attempted'] is False
    assert all(o['a']['hus_answer'] == o['b']['hus_answer'] for o in saved)
    for observation in saved:
        if not observation['b']['generation']['used']:
            assert observation['b']['reply'] == observation['a']['reply']
    if expected_calls < 3:
        assert saved[expected_calls]['trace']['evaluation_stop'] == stop
        assert saved[expected_calls]['trace']['http_status'] is None
    for request in calls:
        body = json.loads(request.content)
        assert body['max_tokens'] == 1024 and body['stream'] is False
        assert body['model'] == settings().model
    text = (folder / 'observations.json').read_text(encoding='utf-8')
    assert all(value not in text for value in ('private-message', 'private-project', 'synthetic-eval-key'))
    assert evaluator.replay(folder)['reproduced']


@pytest.mark.parametrize('status,limit,reason', [(403, 2, 'permission_denied'),
                                               (401, 1, 'authentication')])
def test_permission_headers_stop_batch_even_if_error_body_times_out(prepared, tmp_path, status, limit, reason):
    calls = []

    class BrokenBody(httpx.SyncByteStream):
        def __iter__(self):
            raise httpx.ReadTimeout('private-body synthetic-eval-key')
            yield b''

    def respond(request):
        calls.append(request)
        return httpx.Response(status, stream=BrokenBody())

    report = evaluator.run(prepared, tmp_path / 'run', settings(),
        transport_factory=lambda: httpx.MockTransport(respond), min_interval=0)
    assert len(calls) == limit and report['evaluation_stop_reason'] == reason
    assert report['metrics']['http_status'] == {str(status): limit}
    assert report['metrics']['eligible_not_attempted'] == 3 - limit
    assert evaluator.replay(tmp_path / 'run')['reproduced']


@pytest.mark.parametrize('damage', ['policy', 'stop_reason', 'continued_call'])
def test_replay_verifies_new_failure_policy(prepared, tmp_path, damage):
    folder = tmp_path / 'run'
    evaluator.run(prepared, folder, settings(),
                  transport_factory=lambda: httpx.MockTransport(lambda request: httpx.Response(403)), min_interval=0)
    report = json.loads((folder / 'report.json').read_bytes())
    if damage == 'policy':
        report['failure_policy']['stop_after_consecutive_403'] = 24
    elif damage == 'stop_reason':
        report['evaluation_stop_reason'] = None
    else:
        observations = json.loads((folder / 'observations.json').read_bytes())
        observations[2]['trace'].update(attempted=True, evaluation_stop=None, http_status=403)
        (folder / 'observations.json').write_text(json.dumps(observations), encoding='utf-8')
        report['collection_complete'] = True  # Pass the pre-existing completeness check; test the circuit itself.
    (folder / 'report.json').write_text(json.dumps(report), encoding='utf-8')
    evaluator.seal(folder)
    with pytest.raises(ValueError, match='failure'):
        evaluator.replay(folder)


@pytest.mark.parametrize('singleton_array', [False, True])
def test_one_call_diagnostic_budget_never_uses_remaining_cohort(prepared, tmp_path, singleton_array):
    calls = []

    def respond(request):
        calls.append(request)
        body = {'error': {'status': 'PERMISSION_DENIED',
            'message': 'Your API key was reported as leaked. synthetic-eval-key'}}
        return httpx.Response(403, json=[body] if singleton_array else body)

    report = evaluator.run(prepared, tmp_path / 'run', settings(), max_calls=1,
                           transport_factory=lambda: httpx.MockTransport(respond), min_interval=0)
    assert len(calls) == 1 and report['metrics']['eligible_not_attempted'] == 2
    saved = evaluator.read_sealed(tmp_path / 'run')['observations.json']
    assert saved[0]['trace']['provider_error']['access_issue'] == 'key_reported_leaked'
    assert saved[1]['trace']['evaluation_stop'] == 'call_budget'
    assert report['metrics']['used'] == 0 and report['collection_complete'] is False
    assert evaluator.replay(tmp_path / 'run')['reproduced']


def test_transport_error_breaks_consecutive_permission_streak(prepared, tmp_path):
    calls = []

    def respond(request):
        calls.append(request)
        if len(calls) == 2:
            raise httpx.ConnectError('private-connect-failure', request=request)
        return httpx.Response(403)

    report = evaluator.run(prepared, tmp_path / 'run', settings(),
                           transport_factory=lambda: httpx.MockTransport(respond), min_interval=0)
    assert len(calls) == 3 and report['evaluation_stop_reason'] is None
    assert report['collection_complete'] is True
    assert report['metrics']['used'] == 0 and report['metrics']['http_status'] == {'403': 2}
    assert evaluator.replay(tmp_path / 'run')['reproduced']
