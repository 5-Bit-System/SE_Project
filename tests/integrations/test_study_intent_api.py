"""Authenticated synthetic HTTP flow, real JS payload and service; no external calls."""

import json
import subprocess

from app.api import academic
from app.recommendation.feature_extractor import CatalogFeatureExtractor


def payload(revision, *, goal, explicit=False):
    script = """
import {recommendationPayload} from './app/static/recommendation-model.mjs';
const p = recommendationPayload({program_id:'khdl'}, {
  credits:20, workload:'moderate', goal:process.argv[1], confirmedWorkload:process.argv[2]==='yes'
}, 'balanced', process.argv[3]);
console.log(JSON.stringify(p));
"""
    return json.loads(subprocess.check_output(['node', '--input-type=module', '-e', script,
        goal, 'yes' if explicit else 'no', revision], text=True))


def test_actual_ui_payload_invokes_extractor_and_surfaces_workload_conflict(client, ready_context, monkeypatch):
    calls = []
    class Extractor:
        def extract(self, message):
            calls.append(message)
            return {"target_credits": 30, "target_course_count": 20}
    monkeypatch.setattr(academic, 'configured_adapters', lambda *_: (Extractor(), None))
    response = client.post('/me/recommendations', json=payload(ready_context['revision'],
        goal='Tối đa 3 tín chỉ và 1 môn', explicit=True))
    assert response.status_code == 200
    data = response.json()
    assert calls and data['intent']['status'] == 'needs_clarification'
    assert data['recommendations'] == []
    assert data['preference']['target_credits'] == 3
    assert data['context_revision'] == ready_context['revision']


def test_api_enforces_text_budget_with_empty_provider_json(client, ready_context, monkeypatch):
    monkeypatch.setattr(academic, 'configured_adapters', lambda cat:
        (CatalogFeatureExtractor(cat, lambda _: '{}'), None))
    response = client.post('/me/recommendations', json={
        'program_id': 'khdl', 'expected_revision': ready_context['revision'],
        'goal': 'Tối đa 3 tín chỉ và 1 môn', 'max_credits': 20, 'limit': 20})
    assert response.status_code == 200
    data = response.json()
    assert data['intent']['status'] == 'ready'
    assert len(data['recommendations']) <= 1
    assert sum(row['credits'] for row in data['recommendations']) <= 3
    assert 'PHI1006' not in [row['code'] for row in data['recommendations']]


def test_advisor_server_state_survives_provider_failure_and_rejects_stale_turn(client, ready_context, monkeypatch):
    monkeypatch.setattr(academic, 'configured_adapters', lambda *_: (None, None))
    body = {'program_id': 'khdl', 'expected_revision': ready_context['revision'],
            'message': 'Tối đa 3 tín chỉ và 1 môn'}
    first = client.post('/me/advisor/chat', json=body)
    assert first.status_code == 200
    assert first.json()['intent_version'] == 1
    second = client.post('/me/advisor/chat', json={**body, 'message': 'Ưu tiên thực hành nhé', 'intent_version': 1})
    assert second.status_code == 200
    data = second.json()
    assert data['preference']['target_credits'] == 3
    assert data['preference']['target_course_count'] == 1
    assert len(data['suggested_courses']) <= 1
    assert client.post('/me/advisor/chat', json={**body, 'intent_version': 1}).status_code == 409
    changed = client.post('/me/advisor/chat', json={**body, 'message': 'đổi thành 6 tín chỉ và 2 môn', 'intent_version': 2})
    assert changed.json()['preference']['target_credits'] == 6


def test_missing_server_state_does_not_trust_client_history(client, ready_context, monkeypatch):
    monkeypatch.setattr(academic, 'configured_adapters', lambda *_: (None, None))
    body = {'program_id': 'khdl', 'expected_revision': ready_context['revision'],
            'message': 'Ưu tiên thực hành', 'history': [{'role': 'user', 'content': 'tối đa 3 tín chỉ'}]}
    response = client.post('/me/advisor/chat', json=body)
    assert response.status_code == 200
    assert response.json()['intent']['status'] == 'needs_clarification'
    assert response.json()['suggested_courses'] == []
    reset = client.post('/me/advisor/chat', json={**body, 'message': 'tối đa 3 tín chỉ', 'reset_intent': True})
    assert reset.json()['intent']['status'] == 'ready'


def test_invalid_limit_remains_blocked_across_turns(client, ready_context, monkeypatch):
    monkeypatch.setattr(academic, 'configured_adapters', lambda *_: (None, None))
    base = {'program_id': 'khdl', 'expected_revision': ready_context['revision']}
    first = client.post('/me/advisor/chat', json={**base, 'message': 'đổi thành 99 tín chỉ'}).json()
    assert first['intent']['status'] == 'needs_clarification'
    second = client.post('/me/advisor/chat', json={**base, 'message': 'thực hành nhé', 'intent_version': first['intent_version']}).json()
    assert second['intent']['status'] == 'needs_clarification' and not second['suggested_courses']


def test_revision_change_does_not_reuse_previous_intent_state(client, ready_context, monkeypatch):
    monkeypatch.setattr(academic, 'configured_adapters', lambda *_: (None, None))
    body = {'program_id': 'khdl', 'expected_revision': ready_context['revision'],
            'message': 'Tối đa 3 tín chỉ và 1 môn'}
    first = client.post('/me/advisor/chat', json=body)
    assert first.status_code == 200
    assert first.json()['intent_version'] == 1
    assert first.json()['preference']['target_credits'] == 3

    # Same account and session, different graduation path: the context revision changes.
    switched = client.post('/me/advisor/chat', json={
        **body, 'selected_graduation_path_id': 'thesis',
        'message': 'Ưu tiên thực hành nhé', 'intent_version': 1})
    assert switched.status_code == 409
    new_revision = switched.json()['detail']['context_revision']
    assert new_revision != ready_context['revision']

    after = client.post('/me/advisor/chat', json={
        **body, 'selected_graduation_path_id': 'thesis',
        'expected_revision': new_revision, 'message': 'Ưu tiên thực hành nhé',
        'intent_version': 1})
    assert after.status_code == 200
    data = after.json()
    assert data['context_revision'] == new_revision
    # The old state belongs to another revision: ask instead of silently reusing 3 credits.
    assert data['intent']['status'] == 'needs_clarification'
    assert data['preference']['target_credits'] is None
    assert data['suggested_courses'] == []

