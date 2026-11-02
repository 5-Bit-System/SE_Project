"""VNU identity lifecycle and cutover against disposable databases only."""

# ruff: noqa: F811

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from sqlalchemy import text

from app.auth import portal, repository
from app.auth.security import AuthFailure
from app.integrations.daotao import runtime, store
from app.integrations.daotao.snapshot import PortalFailure, snapshot
from tests.integrations.test_system_auth import (  # noqa: F401
    PASSWORD,
    runtime_engine,
    system,
    verified_login,
)

pytestmark = pytest.mark.hus_postgres


def login(client, username='synthetic-vnu'):
    response = client.post('/auth/vnu', json={'username': username, 'password': 'synthetic-private'})
    assert response.status_code == 200, response.text
    state = client.get('/auth/session').json()
    assert state['authenticated']
    client.headers['x-csrf-token'] = state['csrf_token']
    return state['account']


def test_student_creates_one_account_without_email_or_password(system):
    client, engine, messages = system
    first = login(client)
    assert first['auth_method'] == 'vnu' and first['role'] == 'student' and first['email'] is None
    assert not first['must_change_password']
    assert client.get('/me/profile').json()['snapshot']
    assert client.get('/me/portal-connection').json() == {'linked': True, 'connected': True}
    assert client.post('/me/portal-sync').status_code == 202
    old = client.cookies.get('study_app_session')
    second = login(client)
    assert first['account_id'] == second['account_id'] and first['session_id'] != second['session_id']
    assert repository.session_from_token(old) is None
    assert not messages
    with engine.connect() as conn:
        row = conn.execute(text('SELECT * FROM accounts')).mappings().one()
        assert row['password_hash'] == '!vnu-only' and row['email_verified_at'] is None
        assert conn.execute(text('SELECT count(*) FROM account_portal_links')).scalar_one() == 1


@pytest.mark.parametrize('path', ['/auth/register', '/auth/email/resend', '/auth/email/verify'])
def test_email_auth_is_retired_without_side_effects(system, path):
    client, engine, messages = system
    assert client.post(path, json={'email': 'any@sohoctap.test', 'password': PASSWORD}).status_code == 410
    assert not messages
    with engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM accounts')).scalar_one() == 0


def test_local_student_login_is_closed_but_admin_login_remains(system):
    client, engine, messages = system
    account = verified_login(client, messages)
    assert account['auth_method'] == 'local' and account['role'] == 'admin'
    client.post('/auth/logout')
    with engine.begin() as conn:
        conn.execute(text("UPDATE accounts SET role='student'"))
    assert client.post('/auth/login', json={'email': 'admin@sohoctap.test', 'password': PASSWORD}).status_code == 401
    assert client.get('/auth/session').json() == {'authenticated': False}


def test_admin_username_login_and_password_boundary(system):
    client, engine, messages = system
    admin = verified_login(client, messages)
    with engine.begin() as conn:
        conn.execute(text("UPDATE accounts SET username='synthetic-admin' WHERE id=:id"), {'id': admin['account_id']})
    assert client.post('/auth/login', json={'username': 'SYNTHETIC-ADMIN', 'password': PASSWORD}).status_code == 200
    client.headers['x-csrf-token'] = client.get('/auth/session').json()['csrf_token']
    assert client.post('/me/password', json={'current_password': PASSWORD, 'new_password': 'Ab9!x'}).status_code == 400
    assert client.post('/me/password', json={'current_password': PASSWORD, 'new_password': 'Ab9!xy'}).status_code == 200


def test_student_cannot_escalate_or_change_local_password(system):
    client, _, _ = system
    principal = login(client)
    assert client.get('/admin/users').status_code == 403
    assert client.patch('/admin/users/' + principal['account_id'], json={'role': 'admin'}).status_code == 403
    assert client.post('/me/password', json={'current_password': 'x', 'new_password': PASSWORD}).json() == {'detail': 'use_vnu_password'}
    assert client.post('/auth/vnu', json={'username': 'x', 'password': 'x', 'role': 'admin'}).status_code == 400
    client.headers.pop('x-csrf-token')
    assert client.delete('/me/portal-data').status_code == 403


@pytest.mark.parametrize('code,status', [('identity_unverified', 401), ('interaction_required', 409),
                                       ('timeout', 504), ('browser_unavailable', 503),
                                       ('network_access_denied', 503)])
def test_no_identity_or_session_when_vnu_authentication_fails(system, monkeypatch, code, status):
    client, engine, _ = system

    async def fail(value):
        raise PortalFailure(code)
    monkeypatch.setattr(runtime, 'collect', fail)
    response = client.post('/auth/vnu', json={'username': 'synthetic-vnu', 'password': 'private'})
    assert response.status_code == status
    assert 'private' not in response.text
    with engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM accounts')).scalar_one() == 0
        assert conn.execute(text('SELECT count(*) FROM auth_sessions')).scalar_one() == 0


def test_delete_source_retains_identity_and_relogin_reuses_account(system):
    client, engine, _ = system
    original = login(client)
    assert client.delete('/me/portal-data').status_code == 200
    assert client.get('/auth/session').json()['authenticated']
    with engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM portal_transcript_snapshots')).scalar_one() == 0
        assert conn.execute(text('SELECT vnu_subject FROM accounts')).scalar_one() == 'synthetic-vnu'
    assert login(client)['account_id'] == original['account_id']
    assert client.get('/me/profile').json()['snapshot']
    assert client.post('/me/portal-connection', json={'username': 'different-vnu', 'password': 'private'}).status_code == 409


def test_deleted_source_identity_cannot_be_linked_to_another_account(system):
    client, _, messages = system
    student = login(client)
    assert client.delete('/me/portal-data').status_code == 200
    verified_login(client, messages)
    assert client.post('/me/portal-connection', json={'username': 'synthetic-vnu', 'password': 'private'}).status_code == 409
    assert login(client)['account_id'] == student['account_id']


def test_source_failure_after_proven_login_preserves_existing_data(system, monkeypatch):
    client, _, _ = system
    original = login(client)
    before = client.get('/me/profile').json()

    async def collect(value):
        return {'authenticated': True, 'subject': 'synthetic-vnu', 'snapshot': None,
                'warning': 'source_unavailable', 'cookies': []}
    monkeypatch.setattr(runtime, 'collect', collect)
    assert login(client)['account_id'] == original['account_id']
    after = client.get('/me/profile').json()
    assert after['snapshot'] == before['snapshot'] and after['last_synced_at'] == before['last_synced_at']


def test_new_account_can_login_when_source_temporarily_unavailable(system, monkeypatch):
    client, _, _ = system

    async def collect(value):
        return {'authenticated': True, 'subject': 'synthetic-vnu', 'snapshot': None,
                'warning': 'source_unavailable', 'cookies': []}
    monkeypatch.setattr(runtime, 'collect', collect)
    login(client)
    assert client.get('/me/profile').json()['snapshot'] is None


def test_changed_unknown_snapshot_cannot_overwrite_old_source(system):
    client, _, _ = system
    owner, generation = store.owner('synthetic-vnu')
    original = snapshot([['1', 'OLD001', 'Old synthetic course', '3', '7', 'B', '3']])
    store.save(owner, generation, original)
    response = client.post('/auth/vnu', json={'username': 'synthetic-vnu', 'password': 'private'})
    assert response.status_code == 200 and response.json()['warning'] == 'incomplete_snapshot'
    assert client.get('/me/profile').json()['snapshot'] == original


def test_account_disable_during_login_does_not_issue_session(system, monkeypatch):
    client, engine, _ = system
    login(client)
    original = runtime.collect

    async def collect(value):
        with engine.begin() as conn:
            conn.execute(text('UPDATE accounts SET is_active=false,auth_version=auth_version+1'))
        return await original(value)
    monkeypatch.setattr(runtime, 'collect', collect)
    assert client.post('/auth/vnu', json={'username': 'synthetic-vnu', 'password': 'private'}).status_code == 403
    assert client.get('/auth/session').json() == {'authenticated': False}


def test_admin_lists_searches_and_disables_vnu_students(system):
    client, _, messages = system
    student = login(client)
    old = client.cookies.get('study_app_session')
    verified_login(client, messages)
    rows = client.get('/admin/users?q=synthetic-vnu').json()['items']
    assert len(rows) == 1 and rows[0]['vnu_subject'] == 'synthetic-vnu'
    assert client.patch('/admin/users/' + student['account_id'], json={'role': 'admin'}).json() == {'detail': 'admin_credentials_required'}
    assert client.patch('/admin/users/' + student['account_id'], json={'is_active': False}).status_code == 200
    assert repository.session_from_token(old) is None
    assert client.post('/auth/vnu', json={'username': 'synthetic-vnu', 'password': 'private'}).status_code == 403


def test_app_session_survives_ram_loss_and_logout_revokes_it(system):
    client, _, _ = system
    login(client)
    for value in list(runtime.sessions.values()):
        runtime.revoke(value)
    assert client.get('/auth/session').json()['authenticated']
    assert client.get('/me/profile').json()['snapshot']
    assert client.post('/me/portal-sync').json() == {'state': 'reauth_required'}
    assert client.post('/auth/logout').status_code == 200
    assert client.get('/me/profile').status_code == 401


def test_concurrent_first_logins_share_identity_and_owner(system):
    _, engine, _ = system
    result = {'authenticated': True, 'subject': 'synthetic-concurrent', 'snapshot': None,
              'warning': 'source_unavailable'}
    barrier = Barrier(2)

    def signin():
        barrier.wait()
        return portal.signin(result)[0]
    with ThreadPoolExecutor(max_workers=2) as workers:
        tasks = [workers.submit(signin) for _ in range(2)]
        principals = [repository.session_from_token(task.result(timeout=10)) for task in tasks]
    assert principals[0]['account_id'] == principals[1]['account_id']
    with engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM accounts')).scalar_one() == 1
        assert conn.execute(text('SELECT count(*) FROM account_portal_links')).scalar_one() == 1


def test_vnu_login_rate_limit_is_database_backed(system):
    client, _, _ = system
    for _ in range(10):
        login(client)
    assert client.post('/auth/vnu', json={'username': 'synthetic-vnu', 'password': 'private'}).status_code == 429


def test_unproven_worker_result_cannot_create_account(system):
    _, engine, _ = system
    with pytest.raises(AuthFailure, match='identity_unverified'):
        portal.signin({'subject': 'synthetic-vnu', 'snapshot': None})
    with engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM accounts')).scalar_one() == 0


def test_cutover_preserves_linked_account_source_and_admin_credentials(system):
    from alembic import command
    from database.tools.migrate import config
    client, engine, messages = system
    admin = verified_login(client, messages)
    owner, generation = store.owner('synthetic-linked')
    payload = snapshot([['1', 'OLD001', 'Preserved synthetic', '3', '8', 'B', '3']])
    store.save(owner, generation, payload)
    with engine.begin() as conn:
        # Model an existing 05 account with its already verified source link.
        conn.execute(text("UPDATE accounts SET role='student' WHERE id=:id"), {'id': admin['account_id']})
        conn.execute(text('INSERT INTO account_portal_links(account_id,portal_owner_id) VALUES(:account,:owner)'),
                     {'account': admin['account_id'], 'owner': owner})
        original = conn.execute(text('SELECT username,password_hash,email,email_verified_at FROM accounts')).one()
        conn.execute(text('ALTER TABLE accounts DROP CONSTRAINT ck_accounts_vnu_subject'))
        conn.execute(text('ALTER TABLE accounts DROP COLUMN vnu_subject'))
        conn.execute(text('ALTER TABLE auth_sessions DROP COLUMN auth_method'))
        conn.execute(text("UPDATE hus_alembic_version SET version_num='hus_20261025_05'"))
        cfg = config()
        cfg.attributes['connection'] = conn
        # Only replay this historical cutover; newer tables already exist in this fixture.
        command.upgrade(cfg, 'hus_20261025_06')
        after = conn.execute(text('SELECT username,password_hash,email,email_verified_at FROM accounts')).one()
        assert original == after
        assert conn.execute(text('SELECT vnu_subject FROM accounts')).scalar_one() == 'synthetic-linked'
    assert login(client, 'synthetic-linked')['account_id'] == admin['account_id']
    assert client.get('/me/profile').json()['snapshot'] == payload


def test_vnu_cannot_take_over_admin_source_link(system):
    client, engine, messages = system
    admin = verified_login(client, messages)
    owner, _ = store.owner('synthetic-admin-source')
    with engine.begin() as conn:
        conn.execute(text('INSERT INTO account_portal_links(account_id,portal_owner_id) VALUES(:account,:owner)'),
                     {'account': admin['account_id'], 'owner': owner})
    response = client.post('/auth/vnu', json={'username': 'synthetic-admin-source', 'password': 'private'})
    assert response.status_code == 409
    assert client.get('/auth/session').json()['account']['role'] == 'admin'
    with engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM accounts')).scalar_one() == 1
