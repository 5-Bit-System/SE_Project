"""Plan lifecycle and isolation through real HTTP and disposable PostgreSQL."""

import copy
import json

import pytest
from sqlalchemy import text

from app.integrations.daotao import runtime
from app.integrations.daotao.snapshot import snapshot
from database.tools.publish_catalogs import SOURCE, publish_catalogs
from tests.integrations.test_system_auth import runtime_engine, system  # noqa: F401
from tests.integrations.test_vnu_signin import login

pytestmark = pytest.mark.hus_postgres


@pytest.fixture
def planner(system, monkeypatch):  # noqa: F811
    client, engine, _ = system
    publish_catalogs(engine, json.loads(SOURCE.read_text(encoding='utf-8')))
    from app import program_bindings
    from app.api import academic
    from app.infrastructure.hus_repository import HusRepository
    catalog_repo = HusRepository(engine)
    monkeypatch.setattr(academic, 'load_catalog', catalog_repo.load_catalog)
    monkeypatch.setattr(program_bindings, 'list_catalogs', catalog_repo.list_catalogs)
    proof = dict.fromkeys(('source_host_valid', 'source_path_valid', 'transcript_container_valid',
        'filters_absent', 'pagination_absent', 'hidden_records_absent', 'virtualization_absent',
        'loading_absent', 'network_idle'), True)
    proof.update(layout_contract='vnu-full-table-20261025', stable_reads=3, data_table_count=1)
    payload = snapshot([['HỌC KỲ 1 - 2023-2024'],
        ['1', 'PHI1006', 'Synthetic course', '3', '7.5', 'B', '3']], proof)

    async def collect(request):
        return {'authenticated': True, 'subject': request['username'], 'snapshot': payload,
                'profile': {'name': 'Invented', 'program': 'Khoa học máy tính và thông tin',
                            'cohort': '68'}, 'cookies': []}
    monkeypatch.setattr(runtime, 'collect', collect)
    login(client, 'synthetic-planner')
    options = client.get('/me/academic-program').json()
    program = next(row for row in options['programs'] if row['program_id'] == options['suggested_program_id'])
    confirmation = {'program_id': program['program_id'], 'cohort': 68,
        'expected_catalog_revision': program['catalog_revision'],
        'expected_snapshot_digest': options['snapshot_digest'],
        'expected_source_scope': options['source_scope'], 'confirm': True}
    assert client.post('/me/academic-program', json=confirmation).status_code == 200
    board = client.get('/me/course-status').json()
    selections = board['selections']
    query = {}
    if selections['track_required']:
        query['selected_track_id'] = selections['tracks'][0]['id']
    if selections['path_required']:
        query['selected_graduation_path_id'] = next(row['id'] for row in selections['paths']
            if not row['allowed_track_ids'] or query.get('selected_track_id') in row['allowed_track_ids'])
    board = client.get('/me/course-status', params=query).json()
    assert board.get('plan_basis'), board
    code = board['courses']['eligible'][0]['code']
    body = {'title': 'HK1 — phương án A', 'academic_year_start': 2026, 'semester': 1,
            'max_credits': 20, 'course_codes': [code], 'expected_basis': board['plan_basis'], **query}
    return client, engine, body, board


def test_plan_lifecycle_persists_and_revalidates(planner):
    client, engine, body, board = planner
    result = client.post('/me/semester-plans', json=body)
    assert result.status_code == 201, result.text
    first = result.json()
    expected = next(row['credits'] for row in board['courses']['eligible'] if row['code'] == body['course_codes'][0])
    assert first['total_credits'] == expected and first['version'] == 1
    second = client.post('/me/semester-plans', json={**body, 'title': 'Phương án B'}).json()
    assert len(client.get('/me/semester-plans').json()['plans']) == 2
    login(client, 'synthetic-planner')
    listed = client.get('/me/semester-plans').json()['plans']
    assert {row['id'] for row in listed} == {first['id'], second['id']}
    assert not any(row['needs_review'] for row in listed)
    target = '/me/semester-plans/' + first['id']
    assert client.put(target, json={**body, 'course_codes': [], 'expected_version': 1}).status_code == 200
    assert client.put(target, json={**body, 'expected_version': 1}).status_code == 409
    changed = copy.deepcopy(body)
    changed['expected_basis'] = '0' * 64
    assert client.post('/me/semester-plans', json=changed).status_code == 409
    blocked = board['courses']['completed'][0]['code']
    assert client.post('/me/semester-plans', json={**body, 'course_codes': [blocked]}).status_code == 409
    with engine.begin() as conn:
        conn.execute(text("UPDATE portal_users SET profile=profile - 'academic_binding'"))
    assert all(row['needs_review'] for row in client.get('/me/semester-plans').json()['plans'])
    assert client.delete(target + '?expected_version=1').status_code == 409
    assert client.delete(target + '?expected_version=2').status_code == 200


def test_foreign_account_cannot_read_write_or_delete_plans(planner):
    client, _, body, _ = planner
    original = client.post('/me/semester-plans', json=body).json()
    login(client, 'synthetic-other-planner')
    assert client.get('/me/semester-plans').json()['plans'] == []
    target = '/me/semester-plans/' + original['id']
    assert client.delete(target + '?expected_version=1').status_code == 404
    # Even without a binding the foreign account cannot modify the original.
    assert client.put(target, json={**body, 'expected_version': 1}).status_code in {404, 409}
    login(client, 'synthetic-planner')
    assert client.get('/me/semester-plans').json()['plans'][0]['version'] == 1
