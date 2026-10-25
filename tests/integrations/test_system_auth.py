"""System identity and VNU ownership against disposable PostgreSQL only."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.auth import mail, repository
from app.auth.security import csrf, password_hash, password_matches
from app.auth.settings import settings
from app.integrations.daotao import runtime, store
from app.integrations.daotao.snapshot import snapshot
from app.main import app
from tests.database.test_hus_migration_runtime import runtime_engine  # noqa: F401

pytestmark = pytest.mark.hus_postgres
PASSWORD = 'A synthetic password phrase 2099!'




@pytest.fixture
def system(runtime_engine, monkeypatch):  # noqa: F811
    monkeypatch.setenv('APP_ENV', 'test')
    monkeypatch.setenv('AUTH_TOKEN_PEPPER', 'synthetic-auth-secret-with-more-than-32-characters')
    monkeypatch.setenv('EMAIL_BACKEND', 'fake')
    settings.cache_clear()
    monkeypatch.setattr(repository, 'engine', lambda: runtime_engine)
    monkeypatch.setattr(store, 'engine', lambda: runtime_engine)
    messages = []
    monkeypatch.setattr(mail, 'send_verification', lambda email, value: messages.append((email, value)))

    async def collect(value):
        subject = value.get('subject', value.get('username'))
        return {'authenticated': True, 'subject': subject, 'snapshot': snapshot([['1', 'TEST001', 'Synthetic course', '3', '8', 'B', '3']]),
                'profile': {'name': 'Synthetic student', 'program': None, 'cohort': None},
                'cookies': [{'name': 'synthetic', 'value': 'private-test-cookie',
                             'domain': 'daotao.vnu.edu.vn', 'path': '/dkmh/', 'expires': -1}]}

    monkeypatch.setattr(runtime, 'collect', collect)
    with TestClient(app, base_url='http://127.0.0.1:8000') as client:
        client.headers['origin'] = 'http://127.0.0.1:8000'
        yield client, runtime_engine, messages
    settings.cache_clear()


def register(client, messages, email='admin@sohoctap.test'):
    value = repository.register(email,email,'Synthetic administrator',password_hash(PASSWORD),'synthetic-nonce')
    messages.append((email,value))
    return value


def verified_login(client, messages, email='admin@sohoctap.test'):
    raw = register(client, messages, email)
    repository.verify_email(raw,'synthetic-nonce')
    with repository.engine().begin() as conn:
        conn.execute(text("UPDATE accounts SET role='admin' WHERE email=:email"),{'email':email})
    result=client.post('/auth/login',json={'email':email,'password':PASSWORD})
    assert result.status_code==200,result.text
    state=client.get('/auth/session').json()
    client.headers['x-csrf-token']=state['csrf_token']
    return state['account']


def test_password_change_rotates_and_revokes_old_session(system):
    client, _, messages = system
    verified_login(client, messages)
    old = client.cookies.get('study_app_session')
    replacement = 'Another strong synthetic password phrase!'
    assert client.post('/me/password', json={'current_password': PASSWORD, 'new_password': replacement}).status_code == 200
    assert client.get('/auth/session').json()['authenticated']
    client.cookies.clear()
    client.cookies.set('study_app_session', old)
    assert client.get('/auth/session').json() == {'authenticated': False}


def test_seed_is_persisted_idempotent_and_requires_password_change(system, monkeypatch, tmp_path):
    import uuid
    from pathlib import Path

    from database.tools import seed_system_accounts as seeder
    client, engine, _ = system
    monkeypatch.setattr(seeder, 'engine', lambda: engine)
    handoff = Path('backups/system_auth_20261025') / (tmp_path.name + '-' + uuid.uuid4().hex + '-seed.private.txt')
    assert seeder.seed(handoff) == 2
    original = handoff.read_bytes()
    assert seeder.seed(handoff) == 0
    assert handoff.read_bytes() == original
    with engine.connect() as conn:
        rows = conn.execute(text('SELECT email,role,password_hash,must_change_password,seeded_for_dev FROM accounts')).mappings().all()
        assert {row['role'] for row in rows} == {'admin', 'student'}
        assert all(row['must_change_password'] and row['seeded_for_dev'] and row['password_hash'].startswith('$argon2id$') for row in rows)
        assert conn.execute(text('SELECT count(*) FROM portal_users')).scalar_one() == 0
    temporary = original.decode().split('Temporary password: ')[1].splitlines()[0]
    assert client.post('/auth/login', json={'email': 'admin@sohoctap.test', 'password': temporary}).status_code == 200
    state = client.get('/auth/session').json()
    client.headers['x-csrf-token'] = state['csrf_token']
    assert client.get('/admin/users').json() == {'detail': 'password_change_required'}
    assert client.post('/me/portal-connection', json={'username': 'x', 'password': 'x'}).status_code == 403
    assert client.post('/me/password', json={'current_password': temporary, 'new_password': PASSWORD}).status_code == 200
    assert client.get('/admin/users').status_code == 200


def test_seed_collision_does_not_reset_an_existing_user(system, monkeypatch, tmp_path):
    from pathlib import Path

    from database.tools import seed_system_accounts as seeder
    client, engine, messages = system
    verified_login(client, messages, 'admin@sohoctap.test')
    monkeypatch.setattr(seeder, 'engine', lambda: engine)
    with pytest.raises(RuntimeError, match='conflicts'):
        seeder.seed(Path('backups/system_auth_20261025') / (tmp_path.name + '-collision.private.txt'))
    with engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM accounts')).scalar_one() == 1
        assert password_matches(conn.execute(text('SELECT password_hash FROM accounts')).scalar_one(), PASSWORD)






def test_logout_of_a_rotated_token_also_revokes_its_replacement(system):
    client, _, messages = system
    verified_login(client, messages)
    old = client.cookies.get('study_app_session')
    assert client.post('/me/password', json={'current_password': PASSWORD, 'new_password': 'A fresh synthetic replacement phrase!'}).status_code == 200
    replacement = client.cookies.get('study_app_session')
    client.cookies.clear()
    client.cookies.set('study_app_session', old, domain='127.0.0.1', path='/')
    client.headers['x-csrf-token'] = csrf(old)
    assert client.post('/auth/logout').status_code == 200
    client.cookies.set('study_app_session', replacement, domain='127.0.0.1', path='/')
    assert client.get('/auth/session').json() == {'authenticated': False}










def test_concurrent_password_rotation_and_logout_cannot_leave_a_live_session(system):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from app.auth.security import AuthFailure, password_hash
    client, _, messages = system
    principal = verified_login(client, messages)
    old = client.cookies.get('study_app_session')
    encoded = password_hash('Concurrent synthetic replacement phrase!')
    barrier = Barrier(2)
    def change():
        barrier.wait()
        try:
            return repository.change_password(principal, PASSWORD, encoded)
        except AuthFailure as error:
            assert error.code == 'session_expired'
            return None
    def logout():
        barrier.wait()
        repository.revoke_token(old)
    with ThreadPoolExecutor(max_workers=2) as workers:
        changing = workers.submit(change)
        leaving = workers.submit(logout)
        replacement = changing.result(timeout=10)
        leaving.result(timeout=10)
    assert repository.session_from_token(old) is None
    if replacement:
        assert repository.session_from_token(replacement) is None


def test_two_admins_cannot_concurrently_remove_all_admins(system):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from app.auth.security import AuthFailure
    client, engine, messages = system
    first = verified_login(client, messages, 'first-admin@sohoctap.test')
    proof = register(client, messages, 'second-admin@sohoctap.test')
    repository.verify_email(proof, 'synthetic-nonce')
    with engine.begin() as conn:
        conn.execute(text("UPDATE accounts SET role='admin'"))
    second = repository.session_from_token(repository.login('second-admin@sohoctap.test', PASSWORD))
    barrier = Barrier(2)
    def demote(actor, target):
        barrier.wait()
        try:
            repository.update_user(actor, target, {'role':'student'})
            return 'updated'
        except AuthFailure as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as workers:
        tasks = [workers.submit(demote, first, second['account_id']), workers.submit(demote, second, first['account_id'])]
        results = [task.result(timeout=10) for task in tasks]
    assert results.count('updated') == 1
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM accounts WHERE role='admin' AND is_active")).scalar_one() == 1


def test_production_readiness_rejects_active_development_accounts(system, monkeypatch, tmp_path):
    import uuid
    from pathlib import Path
    from types import SimpleNamespace

    from app.errors import StorageDataError
    from app.main import check_auth_ready
    from database.tools import seed_system_accounts as seeder
    _, engine, _ = system
    monkeypatch.setattr(seeder, 'engine', lambda: engine)
    seeder.seed(Path('backups/system_auth_20261025') / (uuid.uuid4().hex + '-production-gate.private.txt'))
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('EMAIL_BACKEND', 'smtp')
    monkeypatch.setenv('SMTP_SECURITY', 'starttls')
    monkeypatch.setenv('PUBLIC_BASE_URL', 'https://study.example.com')
    monkeypatch.setenv('AUTH_ALLOWED_ORIGINS', 'https://study.example.com')
    monkeypatch.setattr('app.main.get_settings', lambda: SimpleNamespace(storage_backend='postgres'))
    settings.cache_clear()
    with pytest.raises(StorageDataError, match='seed'):
        check_auth_ready()
