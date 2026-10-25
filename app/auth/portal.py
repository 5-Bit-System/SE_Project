"""Verified account-to-VNU claims and source writes share one DB transaction."""

import time
import uuid

from sqlalchemy import text

from app.auth import repository
from app.auth.security import AuthFailure
from app.integrations.daotao import runtime, store
from app.integrations.daotao.snapshot import PortalFailure


def connection(principal, link):
    key = 'app:' + principal['session_id']
    value = runtime.sessions.get(key)
    if value and (value.owner != link['owner'] or value.generation != link['generation']
                  or value.expiry <= time.monotonic()):
        runtime.revoke(value)
        value = None
    if value is None:
        runtime.reap()
        if len(runtime.sessions) >= 1000:
            raise AuthFailure('busy', 429)
        value = runtime.Session(link['owner'], link['subject'], link['generation'],
                                time.monotonic() + min(1800, principal['expires_in']))
        value.account_id = principal['account_id']
        value.app_session_id = principal['session_id']
        runtime.sessions[key] = value
    return value


def bound(conn, value, *, lock=False):
    principal = repository.current(conn, value.app_session_id, lock=lock)
    link = repository.portal_link(principal['account_id'], conn)
    if (not link or principal['account_id'] != value.account_id or link['owner'] != value.owner
            or link['subject'] != value.subject or link['generation'] != value.generation):
        raise AuthFailure('vnu_not_connected', 409)
    return principal


def check(value):
    with repository.engine().connect() as conn:
        return bound(conn, value)


def connect(principal, result):
    with repository.engine().begin() as conn:
        actor = repository.current(conn, principal['session_id'], lock=True)
        if actor.get('vnu_subject') and actor['vnu_subject'] != result['subject']:
            raise AuthFailure('vnu_already_linked', 409)
        identity_owner = conn.execute(text('SELECT id::text FROM accounts WHERE vnu_subject=:subject'),
                                      {'subject': result['subject']}).scalar_one_or_none()
        if identity_owner and identity_owner != principal['account_id']:
            raise AuthFailure('vnu_already_linked', 409)
        prior = repository.portal_link(principal['account_id'], conn)
        if prior and prior['subject'] != result['subject']:
            raise AuthFailure('vnu_already_linked', 409)
        owner = conn.execute(text("""INSERT INTO portal_users(id,subject) VALUES(:id,:subject)
            ON CONFLICT(provider,subject) DO UPDATE SET subject=EXCLUDED.subject
            RETURNING id::text AS owner,subject,generation"""),
                             {'id': str(uuid.uuid4()), 'subject': result['subject']}).mappings().one()
        claimed = conn.execute(text("""SELECT account_id::text FROM account_portal_links
            WHERE portal_owner_id=:owner FOR UPDATE"""), {'owner': owner['owner']}).scalar_one_or_none()
        if claimed and claimed != principal['account_id']:
            raise AuthFailure('vnu_already_linked', 409)
        conn.execute(text("""INSERT INTO account_portal_links(account_id,portal_owner_id)
            VALUES(:account,:owner) ON CONFLICT(account_id) DO NOTHING"""),
                     {'account': principal['account_id'], 'owner': owner['owner']})
        warning = None
        try:
            with conn.begin_nested():
                store.save(owner['owner'], owner['generation'], result['snapshot'], result.get('profile'), connection=conn)
        except PortalFailure as exc:
            if str(exc) != 'incomplete_snapshot':
                raise AuthFailure(str(exc), 409) from None
            warning = 'incomplete_snapshot'
        repository.audit(conn, principal['account_id'], principal['account_id'], 'connect_vnu')
        return dict(owner), warning


def signin(result):
    """Only the trusted fresh-login worker may supply this result.

    Identity is independent of the deletable source link. Serialize the first
    claim, reuse exact existing ownership, and never infer identity from email.
    """
    subject = result['subject']
    if (result.get('authenticated') is not True or not isinstance(subject, str)
            or not 1 <= len(subject) <= 128 or subject != subject.strip().casefold()):
        raise AuthFailure('identity_unverified', 401)
    with repository.engine().begin() as conn:
        conn.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:subject,18107026))'),
                     {'subject': subject})
        account = conn.execute(text('SELECT * FROM accounts WHERE vnu_subject=:subject FOR UPDATE'),
                               {'subject': subject}).mappings().one_or_none()
        claimed = conn.execute(text("""SELECT a.* FROM accounts a
            JOIN account_portal_links l ON l.account_id=a.id
            JOIN portal_users p ON p.id=l.portal_owner_id WHERE p.subject=:subject AND p.provider='vnu'"""),
                               {'subject': subject}).mappings().one_or_none()
        if claimed and (account is None or claimed['id'] != account['id']):
            # New links created concurrently by the retained connection endpoint
            # cannot silently transfer ownership or become an admin login.
            raise AuthFailure('vnu_already_linked', 409)
        if account is None:
            account_id = str(uuid.uuid4())
            account = conn.execute(text("""INSERT INTO accounts
                (username,id,vnu_subject,password_hash,role,must_change_password)
                VALUES(:username,:id,:subject,'!vnu-only','student',false) RETURNING *"""),
                                   {'username': 'vnu:' + account_id, 'id': account_id,
                                    'subject': subject}).mappings().one()
            repository.audit(conn, account_id, account_id, 'create_vnu_account')
        if account['role'] != 'student' or not account['is_active']:
            raise AuthFailure('account_disabled', 403)
        prior = repository.portal_link(str(account['id']), conn)
        if prior and prior['subject'] != subject:
            raise AuthFailure('vnu_already_linked', 409)
        owner = conn.execute(text("""INSERT INTO portal_users(id,subject) VALUES(:id,:subject)
            ON CONFLICT(provider,subject) DO UPDATE SET subject=EXCLUDED.subject
            RETURNING id::text AS owner,subject,generation"""),
                             {'id': str(uuid.uuid4()), 'subject': subject}).mappings().one()
        linked = conn.execute(text('SELECT account_id FROM account_portal_links WHERE portal_owner_id=:owner'),
                              {'owner': owner['owner']}).scalar_one_or_none()
        if linked and linked != account['id']:
            raise AuthFailure('vnu_already_linked', 409)
        conn.execute(text("""INSERT INTO account_portal_links(account_id,portal_owner_id)
            VALUES(:account,:owner) ON CONFLICT(account_id) DO NOTHING"""),
                     {'account': account['id'], 'owner': owner['owner']})
        warning = result.get('warning')
        if result.get('snapshot') is not None:
            try:
                with conn.begin_nested():
                    store.save(owner['owner'], owner['generation'], result['snapshot'],
                               result.get('profile'), connection=conn)
            except PortalFailure as exc:
                if str(exc) != 'incomplete_snapshot':
                    raise AuthFailure(str(exc), 409) from None
                warning = 'incomplete_snapshot'
        raw = repository._create_session(conn, account, method='vnu')
        repository.audit(conn, account['id'], account['id'], 'login_vnu')
        return raw, dict(owner), warning


def save(value, payload, details):
    with repository.engine().begin() as conn:
        bound(conn, value, lock=True)
        try:
            return store.save(value.owner, value.generation, payload, details, connection=conn)
        except PortalFailure as exc:
            raise AuthFailure(str(exc), 409) from None


def clear(principal):
    with repository.engine().begin() as conn:
        repository.current(conn, principal['session_id'], lock=True)
        link = repository.portal_link(principal['account_id'], conn)
        if link:
            store.clear(link['owner'], connection=conn)
            repository.audit(conn, principal['account_id'], principal['account_id'], 'delete_vnu')
        return link
