"""New source-owned boundary must reject anonymous/tampered requests before cutover."""

import copy

import pytest
from fastapi.testclient import TestClient

from app.integrations.daotao import runtime, store
from app.main import app


@pytest.fixture
def client(monkeypatch):
    runtime.sessions.clear()
    seen = []
    data = {"subject": "synthetic", "profile": {}, "snapshot": {
        "schema_version": 1, "completeness": "unknown", "digest": "synthetic",
        "attempts": [], "unknown_rows": []}, "fetched_at": None}

    def profile(owner):
        seen.append(owner)
        return copy.deepcopy(data)

    monkeypatch.setattr(store, "profile", profile)
    with TestClient(app, base_url="http://127.0.0.1:8000") as value:
        value.headers["origin"] = "http://127.0.0.1:8000"
        value.seen_owners = seen
        value.profile_data = data
        yield value
    runtime.sessions.clear()


def authenticated(client, owner="synthetic-owner"):
    token = runtime.new_session(owner, "synthetic", 0)
    client.cookies.set("study_portal_session", token)


def test_context_requires_authenticated_session(client):
    assert client.get('/me/academic-context?program_id=khdl').status_code == 401
    assert client.seen_owners == []


def test_preview_context_reads_owner_from_session_and_stays_unready(client):
    authenticated(client)
    response = client.get('/me/academic-context?program_id=khdl')
    assert response.status_code == 200
    assert response.json()['status'] == 'needs_program_binding'
    assert response.json()['completed_course_codes'] == []
    assert client.seen_owners == ['synthetic-owner']
    assert response.headers['cache-control'] == 'no-store'


def test_client_cannot_supply_owner_or_completed_facts(client):
    authenticated(client)
    response = client.get('/me/academic-context?program_id=khdl&owner=other')
    assert response.status_code == 422
    assert client.seen_owners == []
    response = client.post('/me/recommendations', json={
        'program_id': 'khdl', 'passed_course_codes': ['MAT2400'], 'owner': 'other'})
    assert response.status_code == 422


@pytest.mark.parametrize('path', ['/me/eligibility', '/me/academic-progress'])
def test_unready_source_never_returns_personalized_empty_transcript_results(client, path):
    authenticated(client)
    response = client.get(path + '?program_id=khdl')
    assert response.status_code == 409
    assert response.json()['detail']['code'] == 'academic_context_not_ready'
    assert 'program_binding_unverified' in response.json()['detail']['blocking_reasons']


@pytest.mark.parametrize('path', ['/me/recommendations', '/me/recommendations/what-if',
                                '/me/advisor/chat'])
def test_personalized_operations_share_the_context_gate(client, path):
    authenticated(client)
    response = client.post(path, json={'program_id': 'khdl', 'expected_revision': None})
    assert response.status_code == 409
    assert response.json()['detail']['code'] == 'academic_context_not_ready'


def test_new_source_gate_keeps_legacy_routes_until_ready_cutover(client):
    # The approved removal gate has not passed; do not prematurely delete the working flow.
    response = client.post('/eligibility', json={'program_id': 'khdl', 'passed_course_codes': []})
    assert response.status_code == 200


@pytest.fixture
def ready_context(client, monkeypatch):
    # Test-only evidence/policy. Never enable these settings for a real account.
    import importlib.util
    assert importlib.util.find_spec('app.api.academic') is not None, 'Source-owned API missing'
    from app.academic_context import AcademicPolicy
    from app.api.academic import POLICIES

    authenticated(client)
    preview = client.get('/me/academic-context?program_id=khdl').json()
    client.profile_data['profile']['academic_binding'] = {
        'program_id': 'khdl_7460108_2022', 'catalog_revision': preview['catalog_revision'],
        'verified': True, 'evidence_ref': 'synthetic-only:review', 'policy_version': 'test-only-v1'}
    client.profile_data['snapshot'].update(completeness='complete', attempts=[{
        'row_key': '0', 'code': 'PHI1006', 'credits': '3', 'grade10': '4.2',
        'letter': 'D', 'grade4': '1'}])
    monkeypatch.setitem(POLICIES, 'test-only-v1', AcademicPolicy(
        'test-only-v1', 'synthetic:test-spec', ('khdl_7460108_2022',), {'D': (4, 4.9, 1)}))
    context = client.get('/me/academic-context?program_id=khdl').json()
    assert context['status'] == 'ready'
    assert context['completed_course_codes'] == ['PHI1006']
    return context


def test_ready_server_source_drives_eligibility_and_recommendations(client, ready_context):
    context = ready_context
    response = client.get('/me/eligibility?program_id=khdl')
    assert response.status_code == 200
    assert 'PHI1006' not in [course['code'] for course in response.json()['eligible_courses']]
    body = {'program_id': 'khdl', 'expected_revision': context['revision'], 'goal': '', 'limit': 5}
    response = client.post('/me/recommendations', json=body)
    assert response.status_code == 200
    assert response.json()['context_revision'] == context['revision']
    assert 'PHI1006' not in [course['code'] for course in response.json()['recommendations']]
    client.profile_data['snapshot']['digest'] = 'newer-synthetic-source'
    assert client.post('/me/recommendations', json=body).status_code == 409


@pytest.mark.parametrize('change,expected', [('source', 409), ('logout', 401)])
def test_slow_recommendation_never_returns_results_after_source_or_session_changes(
        client, ready_context, monkeypatch, change, expected):
    from app.api import academic
    real_recommend = academic.recommend

    def delayed(*args, **kwargs):
        result = real_recommend(*args, **kwargs)
        if change == 'source':
            client.profile_data['snapshot']['digest'] = 'updated-during-ranking'
        else:
            runtime.sessions.clear()
        return result

    monkeypatch.setattr(academic, 'recommend', delayed)
    response = client.post('/me/recommendations', json={
        'program_id': 'khdl', 'expected_revision': ready_context['revision']})
    assert response.status_code == expected
    assert 'recommendations' not in response.json()


def test_ready_progress_and_advisor_share_source_owned_completed_facts(client, ready_context):
    response = client.get('/me/academic-progress?program_id=khdl')
    assert response.status_code == 200
    assert response.json()['context_revision'] == ready_context['revision']
    assert response.json()['gpa'] is None
    response = client.post('/me/advisor/chat', json={
        'program_id': 'khdl', 'expected_revision': ready_context['revision'],
        'message': 'Goi y mon hoc'})
    assert response.status_code == 200
    assert response.json()['context_revision'] == ready_context['revision']


def test_what_if_requires_a_server_baseline_even_when_context_is_ready(client, ready_context):
    response = client.post('/me/recommendations/what-if', json={
        'program_id': 'khdl', 'expected_revision': ready_context['revision']})
    assert response.status_code == 409
    assert response.json()['detail'] == 'academic_baseline_not_available'


def test_context_revision_changes_on_new_session_even_for_same_owner(client):
    authenticated(client)
    before = client.get('/me/academic-context?program_id=khdl').json()
    authenticated(client)
    after = client.get('/me/academic-context?program_id=khdl').json()
    assert before['revision'] != after['revision']


@pytest.mark.parametrize('selection', [
    'selected_track_id=missing', 'selected_graduation_path_id=missing'])
def test_unready_source_does_not_accept_invalid_plan_selection(client, selection):
    authenticated(client)
    response = client.get('/me/academic-context?program_id=khdl&' + selection)
    assert response.status_code == 422


@pytest.mark.parametrize('path', ['/me/eligibility', '/me/academic-progress'])
def test_expired_session_does_not_read_stored_source(client, path):
    import time
    authenticated(client)
    for value in runtime.sessions.values():
        value.expiry = time.monotonic() - 1
    assert client.get(path + '?program_id=khdl').status_code == 401
    assert client.seen_owners == []
