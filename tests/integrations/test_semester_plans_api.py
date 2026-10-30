"""Offline API contracts; database persistence is covered separately."""

import pytest

from app.services import semester_plan_service as plans
from tests.integrations.test_program_binding import (  # noqa: F401
    authenticate,
    client,
    confirmation,
)


def test_plan_endpoints_require_current_account(client):  # noqa: F811
    assert client.get('/me/semester-plans').status_code == 401
    assert client.post('/me/semester-plans', json={}).status_code == 401


def test_board_provides_stable_plan_basis_across_app_sessions(client, monkeypatch):  # noqa: F811
    from app import program_bindings
    from app.api import academic
    from tests.support.catalog_fixtures import mark_catalog_reviewed_for_test

    list_catalogs = program_bindings.list_catalogs
    load_catalog = academic.load_catalog
    monkeypatch.setattr(program_bindings, 'list_catalogs', lambda:
                        [mark_catalog_reviewed_for_test(catalog) for catalog in list_catalogs()])
    monkeypatch.setattr(academic, 'load_catalog', lambda program_id:
                        mark_catalog_reviewed_for_test(load_catalog(program_id)))

    authenticate(client, 'owner-a')
    assert client.post('/me/academic-program', json=confirmation(client)).status_code == 200
    first = client.get('/me/course-status').json()
    authenticate(client, 'owner-a')
    second = client.get('/me/course-status').json()
    assert first['context_revision'] != second['context_revision']
    assert first['plan_basis'] == second['plan_basis']
    client.data['owner-a']['snapshot']['digest'] = 'new-source'
    assert client.get('/me/course-status').json()['plan_basis'] != first['plan_basis']


@pytest.mark.parametrize('extra', [{'account_id': 'foreign'}, {'total_credits': 0},
                                  {'program_id': 'foreign'}, {'verified': True}])
def test_plan_body_cannot_override_server_facts(client, extra):  # noqa: F811
    authenticate(client, 'owner-a')
    payload = {'title': 'Draft', 'academic_year_start': 2026, 'semester': 1,
               'course_codes': [], 'expected_basis': 'a' * 64, **extra}
    assert client.post('/me/semester-plans', json=payload).status_code == 422


def test_create_and_update_version_contract_and_csrf(client, monkeypatch):  # noqa: F811
    authenticate(client, 'owner-a')
    monkeypatch.setattr(plans, 'save_plan', lambda value, body, plan_id=None: {
        'title': body.title, 'max_credits': body.max_credits})
    body = {'title': '  Draft  ', 'academic_year_start': 2026, 'semester': 1,
            'course_codes': [], 'expected_basis': 'a' * 64}
    result = client.post('/me/semester-plans', json=body)
    assert result.status_code == 201 and result.json()['title'] == 'Draft'
    target = '/me/semester-plans/00000000-0000-0000-0000-000000000001'
    assert client.put(target, json=body).status_code == 422
    assert client.delete(target).status_code == 422
    assert client.post('/me/semester-plans', json={**body, 'title': '  '}).status_code == 422
    assert client.post('/me/semester-plans', json={**body, 'academic_year_start': '2026'}).status_code == 422
    client.headers['x-csrf-token'] = 'wrong'
    assert client.post('/me/semester-plans', json=body).status_code == 403
