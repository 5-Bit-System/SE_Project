"""Session and ownership regression tests; no live accounts or database."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth import repository
from app.auth.security import AuthFailure
from app.hus import chat_history_repository as history
from app.hus.router import router


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv('HUS_CHAT_HISTORY_DIR', str(tmp_path))
    monkeypatch.setattr('app.auth.dependencies.csrf', lambda raw: 'test-csrf')

    def session(raw):
        if raw == 'broken':
            raise AuthFailure('storage_unavailable', 503)
        if raw not in {'alice', 'bob', 'password-change'}:
            return None
        return {'account_id': raw, 'must_change_password': raw == 'password-change'}

    monkeypatch.setattr(repository, 'session_from_token', session)
    history.append_message('bob', 'data_science', {'role': 'user', 'reply': 'Bob private'})
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as value:
        yield value


def send(client, method, headers=None):
    kwargs = {'headers': headers or {}}
    if method == 'POST':
        kwargs['json'] = {'major': 'data_science', 'role': 'user', 'reply': 'Alice message'}
    return client.request(method, '/hus/chat/history?major=data_science', **kwargs)


@pytest.mark.parametrize('method', ['GET', 'POST', 'DELETE'])
@pytest.mark.parametrize('token,status', [(None, 401), ('expired', 401), ('broken', 503), ('password-change', 403)])
def test_invalid_identity_cannot_use_header(client, method, token, status):
    if token:
        client.cookies.set('study_app_session', token)
    response = send(client, method, {'X-Account-ID': 'bob', 'X-CSRF-Token': 'test-csrf'})
    assert response.status_code == status
    assert history.get_history('bob', 'data_science')[0]['reply'] == 'Bob private'


@pytest.mark.parametrize('method', ['POST', 'DELETE'])
@pytest.mark.parametrize('token', ['', 'wrong'])
def test_mutations_require_csrf(client, method, token):
    client.cookies.set('study_app_session', 'bob')
    assert send(client, method, {'X-CSRF-Token': token}).status_code == 403
    assert len(history.get_history('bob', 'data_science')) == 1


def test_owner_lifecycle_ignores_spoofed_account(client):
    client.cookies.set('study_app_session', 'alice')
    headers = {'X-Account-ID': 'bob', 'X-CSRF-Token': 'test-csrf'}
    assert send(client, 'GET', headers).json()['messages'] == []
    assert send(client, 'POST', headers).status_code == 200
    result = send(client, 'GET', headers).json()
    assert result['account_id'] == 'alice'
    assert result['messages'][0]['reply'] == 'Alice message'
    assert send(client, 'DELETE', headers).status_code == 200
    assert send(client, 'GET', headers).json()['messages'] == []
    assert history.get_history('bob', 'data_science')[0]['reply'] == 'Bob private'
