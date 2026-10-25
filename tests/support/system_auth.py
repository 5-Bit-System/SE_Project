"""Explicit in-memory repository doubles for offline VNU/API tests only.

Real database authentication, verification and ownership transactions are tested
separately in test_system_auth.py against disposable PostgreSQL.
"""
import uuid

from app.auth import portal, repository
from app.auth.security import AuthFailure, csrf, token
from app.integrations.daotao import runtime, store
from app.integrations.daotao.snapshot import PortalFailure


class SyntheticAccounts:
    def __init__(self, monkeypatch):
        self.sessions, self.links = {}, {}
        monkeypatch.setattr(repository, 'session_from_token', self.resolve)
        monkeypatch.setattr(repository, 'portal_link', lambda account: self.links.get(account))
        monkeypatch.setattr(repository, 'revoke_token', self.revoke)
        monkeypatch.setattr(repository, 'rate', lambda *args: None)
        monkeypatch.setattr(portal, 'check', self.check)
        monkeypatch.setattr(portal, 'connect', self.connect)
        monkeypatch.setattr(portal, 'save', self.save)
        monkeypatch.setattr(portal, 'clear', self.clear)

    def issue(self, client, owner='synthetic-a', subject=None, linked=False, cookies=None):
        raw = token()
        account = {'account_id': 'synthetic-account:' + owner, 'session_id': str(uuid.uuid4()),
                   'email': 'synthetic@sohoctap.test', 'display_name': 'Synthetic', 'role': 'student',
                   'must_change_password': False, 'auth_version': 0, 'expires_in': 1800}
        self.sessions[raw] = account
        client.cookies.clear()
        client.cookies.set('study_app_session', raw, domain='127.0.0.1', path='/')
        client.headers['x-csrf-token'] = csrf(raw)
        client.fake_accounts = self
        if linked:
            link = {'owner': owner, 'subject': subject or owner, 'generation': 0}
            self.links[account['account_id']] = link
            value = portal.connection(account, link)
            if cookies:
                runtime.install_portal(value, cookies, value.portal_version)
        return account

    def resolve(self, raw):
        account = self.sessions.get(raw)
        return account if account and account['expires_in'] > 0 else None

    def revoke(self, raw):
        account = self.sessions.pop(raw, None)
        return [account['session_id']] if account else []

    def current(self, session_id):
        for account in self.sessions.values():
            if account['session_id'] == session_id and account['expires_in'] > 0:
                return account
        raise AuthFailure('session_expired', 401)

    def check(self, value):
        account = self.current(value.app_session_id)
        link = self.links.get(account['account_id'])
        if not link or link['owner'] != value.owner or link['generation'] != value.generation:
            raise AuthFailure('vnu_not_connected', 409)
        return account

    def connect(self, account, result):
        self.current(account['session_id'])
        owner, generation = store.owner(result['subject'])
        warning = None
        try:
            store.save(owner, generation, result['snapshot'], result.get('profile'))
        except PortalFailure as exc:
            if str(exc) != 'incomplete_snapshot':
                raise
            warning = 'incomplete_snapshot'
        link = {'owner': owner, 'subject': result['subject'], 'generation': generation}
        self.links[account['account_id']] = link
        return link, warning

    def save(self, value, payload, details):
        self.check(value)
        try:
            return store.save(value.owner, value.generation, payload, details)
        except PortalFailure as exc:
            raise AuthFailure(str(exc), 409) from None

    def clear(self, account):
        self.current(account['session_id'])
        link = self.links.pop(account['account_id'], None)
        if link:
            store.clear(link['owner'])
        return link
