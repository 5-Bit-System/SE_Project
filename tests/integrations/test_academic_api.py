"""New source-owned boundary must reject anonymous/tampered requests before cutover."""

import copy

import pytest
from fastapi.testclient import TestClient

from app.integrations.daotao import runtime, store
from app.main import app


@pytest.fixture
def client(monkeypatch, fake_accounts):
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
        value.fake_accounts = fake_accounts
        yield value
    runtime.sessions.clear()


def authenticated(client, owner="synthetic-owner"):
    client.fake_accounts.issue(client, owner, 'synthetic', linked=True)


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


def test_legacy_calculation_routes_require_a_verified_system_account(client):
    # The approved removal gate has not passed; do not prematurely delete the working flow.
    response = client.post('/eligibility', json={'program_id': 'khdl', 'passed_course_codes': []})
    assert response.status_code == 401
    authenticated(client)
    response = client.post('/eligibility', json={'program_id': 'khdl', 'passed_course_codes': []})
    assert response.status_code == 200


@pytest.fixture
def ready_context(client, monkeypatch):
    # Test-only evidence/policy. Never enable these settings for a real account.
    import importlib.util
    assert importlib.util.find_spec('app.api.academic') is not None, 'Source-owned API missing'
    from app.academic_context import AcademicPolicy
    from app.api import academic
    from app.api.academic import POLICIES
    from tests.support.catalog_fixtures import mark_catalog_reviewed_for_test

    load_catalog = academic.load_catalog
    monkeypatch.setattr(academic, 'load_catalog', lambda program_id:
                        mark_catalog_reviewed_for_test(load_catalog(program_id)))

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
            client.fake_accounts.revoke(client.cookies.get('study_app_session'))
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
    authenticated(client)
    client.fake_accounts.resolve(client.cookies.get('study_app_session'))['expires_in'] = 0
    assert client.get(path + '?program_id=khdl').status_code == 401
    assert client.seen_owners == []


def test_course_board_requires_session_and_never_guesses_program_from_display(client):
    assert client.get('/me/course-status').status_code == 401
    assert client.seen_owners == []
    authenticated(client)
    client.profile_data['profile'].update(program='Khoa học dữ liệu', cohort='2022')
    response = client.get('/me/course-status')
    assert response.status_code == 200
    assert response.json()['courses'] is None
    assert response.json()['blocking_reasons'] == [
        'source_incomplete', 'program_binding_unverified']
    assert response.headers['cache-control'] == 'no-store'


@pytest.mark.parametrize('query', [
    'program_id=khdl', 'passed_course_codes=PHI1006', 'owner=someone-else',
    'max_credits=0', 'max_credits=31', 'max_credits=2.5',
])
def test_course_board_rejects_foreign_facts_and_invalid_budget(client, query):
    authenticated(client)
    assert client.get('/me/course-status?' + query).status_code == 422
    assert client.seen_owners == []


def test_course_board_returns_disjoint_states_from_verified_server_context(client, ready_context):
    selections = 'selected_track_id=synthetic_track&selected_graduation_path_id=thesis'
    response = client.get('/me/course-status?max_credits=20&' + selections)
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ready'
    selected_context = client.get('/me/academic-context?program_id=khdl&' + selections).json()
    assert data['context_revision'] == selected_context['revision']
    sets = [{course['code'] for course in data['courses'][key]}
            for key in ('completed', 'eligible', 'blocked')]
    assert sets[0] == {'PHI1006'}
    assert not sets[0] & sets[1] and not sets[0] & sets[2] and not sets[1] & sets[2]
    assert len(set.union(*sets)) == 13
    assert all(course['counted_in_total'] for rows in data['courses'].values() for course in rows)
    assert 'CME1000' not in set.union(*sets)
    assert data['prerequisite_courses']['MAT2505'] == {
        'name': 'Synthetic MAT2505', 'name_en': None}
    assert data['plan']['max_credits'] == 20
    assert data['plan']['suggested_credits'] <= 20
    assert set(data['plan']['course_codes']) <= sets[1]
    assert data['plan']['offering_status'] == 'unknown'
    conditional = {course['code'] for course in data['courses']['eligible']
                   if course['eligibility_basis'] == 'available_prerequisites'}
    assert 'THESIS101' in conditional
    assert not conditional & set(data['plan']['course_codes'])
    strict = client.get('/me/eligibility?program_id=khdl&' + selections).json()
    assert not conditional & {course['code'] for course in strict['eligible_courses']}


def test_course_board_does_not_expose_colors_when_source_becomes_unready(client, ready_context):
    client.profile_data['snapshot']['completeness'] = 'unknown'
    data = client.get('/me/course-status').json()
    assert data['courses'] is None
    assert data['progress'] is None
    assert data['plan'] is None
    assert 'source_incomplete' in data['blocking_reasons']


@pytest.mark.parametrize('change, expected', [('source', 409), ('logout', 401)])
def test_course_board_discards_result_if_source_or_session_changes_during_calculation(
        client, ready_context, monkeypatch, change, expected):
    from app.api import academic
    calculate = academic.course_board

    def changed(*args, **kwargs):
        result = calculate(*args, **kwargs)
        if change == 'source':
            client.profile_data['snapshot']['digest'] = 'changed-during-course-board'
        else:
            client.fake_accounts.sessions.clear()
            runtime.sessions.clear()
        return result

    monkeypatch.setattr(academic, 'course_board', changed)
    response = client.get('/me/course-status?selected_track_id=synthetic_track'
                          '&selected_graduation_path_id=thesis')
    assert response.status_code == expected
    assert 'courses' not in response.json()


def test_course_board_requires_track_and_path_before_suggesting_a_bundle(client, ready_context):
    data = client.get('/me/course-status').json()
    assert data['status'] == 'partial'
    assert data['can_plan'] is False
    assert {row['code'] for row in data['courses']['eligible']} == {
        'MAT2505', 'PEC1008', 'MAT2400', 'ELECT101', 'ELECT102',
        'AND101', 'MAT3399', 'THESIS101', 'THESIS102', 'OR101', 'CONFLICT101'}
    assert data['plan']['course_codes'] == []
    assert [course['code'] for course in data['courses']['completed']] == ['PHI1006']
    assert set(data['blocking_reasons']) == {
        'track_selection_required', 'graduation_selection_required'}
    assert data['selections']['tracks'][0]['id'] == 'synthetic_track'


@pytest.mark.parametrize('code, available, plannable', [
    ('MAT2505', True, True), ('CME1000', False, False), ('OR101', True, False),
])
def test_pending_results_and_map_sequences_do_not_promote_completed_facts(
        client, ready_context, code, available, plannable):
    from app.catalog import load_catalog

    course = next(course for course in load_catalog('khdl').courses if course.code == code)
    client.profile_data['snapshot']['attempts'].append({
        'row_key': 'pending', 'code': course.code, 'credits': str(course.credits),
        'grade10': '', 'letter': 'I', 'grade4': ''})
    result = client.get('/me/course-status?selected_track_id=synthetic_track'
                        '&selected_graduation_path_id=thesis').json()
    assert result['status'] == 'partial'
    assert result['can_plan'] is True
    assert [row['code'] for row in result['courses']['completed']] == ['PHI1006']
    assert (course.code in {row['code'] for row in result['courses']['eligible']}) is available
    assert (course.code in result['plan']['course_codes']) is plannable
    if code == 'OR101':
        row = next(row for row in result['courses']['eligible'] if row['code'] == code)
        assert row['eligibility_basis'] == 'completed_prerequisites'
        assert row['result_pending'] is True
        assert row['planning_eligible'] is False
    if code == 'MAT2505':
        following = next(row for row in result['courses']['eligible'] if row['code'] == 'THESIS101')
        assert following['eligibility_basis'] == 'available_prerequisites'
        assert following['prerequisite_clauses'] == [['MAT2505']]
        assert 'THESIS101' not in result['plan']['course_codes']
    strict = client.get('/me/academic-context?program_id=khdl').json()
    assert strict['status'] == 'needs_policy_review'
    assert strict['completed_course_codes'] == []
    assert client.get('/me/eligibility?program_id=khdl').status_code == 409
    assert client.post('/me/recommendations', json={
        'program_id': 'khdl', 'expected_revision': strict['revision']}).status_code == 409


def test_unmapped_result_pauses_bundle_but_preserves_independently_resolved_courses(client, ready_context):
    client.profile_data['snapshot']['attempts'].append({
        'row_key': 'foreign', 'code': 'UNMAPPED001', 'credits': '3',
        'grade10': '7', 'letter': 'B', 'grade4': '3'})
    result = client.get('/me/course-status?selected_track_id=synthetic_track'
                        '&selected_graduation_path_id=thesis').json()
    assert result['status'] == 'partial'
    assert result['can_plan'] is False
    assert [row['code'] for row in result['courses']['completed']] == ['PHI1006']
    assert {row['code'] for row in result['courses']['eligible']} == {
        'MAT2505', 'PEC1008', 'MAT2400', 'ELECT101', 'ELECT102',
        'AND101', 'MAT3399', 'THESIS101', 'OR101', 'CONFLICT101'}
    assert result['plan']['course_codes'] == []
    assert result['review_items'][0]['code'] == 'UNMAPPED001'
