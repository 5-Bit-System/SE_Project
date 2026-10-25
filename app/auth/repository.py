"""Transactional system identity. Provider cookies never enter this repository."""

import uuid

from sqlalchemy import text

from app.auth.security import AuthFailure, digest, password_matches, token
from app.auth.settings import settings
from app.integrations.daotao.store import engine

PRINCIPAL = """
    SELECT a.id::text AS account_id,a.email,a.display_name,a.role,
           CASE WHEN a.role='admin' THEN a.must_change_password ELSE false END AS must_change_password,
           a.vnu_subject,s.auth_method,a.auth_version,s.id::text AS session_id,
           EXTRACT(EPOCH FROM LEAST(s.idle_expires_at,s.absolute_expires_at)-now())::integer AS expires_in
    FROM auth_sessions s JOIN accounts a ON a.id=s.account_id
    WHERE s.id=:session_id AND s.revoked_at IS NULL AND s.idle_expires_at>now()
      AND s.absolute_expires_at>now() AND s.auth_version=a.auth_version
      AND a.is_active AND (
        (a.role='admin' AND s.auth_method='local' AND a.email_verified_at IS NOT NULL)
        OR (a.role='student' AND s.auth_method='vnu' AND a.vnu_subject IS NOT NULL))
"""


def audit(conn, actor, target, action, result='ok'):
    conn.execute(text("""INSERT INTO auth_audit_events(actor_id,target_id,action,result)
        VALUES(:actor,:target,:action,:result)"""),
                 {'actor': actor, 'target': target, 'action': action, 'result': result})


def rate(action, key, limit, window):
    with engine().begin() as conn:
        count = conn.execute(text("""
            INSERT INTO auth_rate_limits(action,key_digest,window_start,attempts)
            VALUES(:action,:key,to_timestamp(floor(extract(epoch from now())/:window)*:window),1)
            ON CONFLICT(action,key_digest,window_start) DO UPDATE
            SET attempts=auth_rate_limits.attempts+1 RETURNING attempts
        """), {'action': action, 'key': digest(key, 'rate'), 'window': window}).scalar_one()
        conn.execute(text("DELETE FROM auth_rate_limits WHERE window_start<now()-interval '2 days'"))
    if count > limit:
        raise AuthFailure('rate_limited', 429)


def current(conn, session_id, *, allow_password_change=False, lock=False):
    if lock:
        # All writers lock the account before its session rows, including logout.
        conn.execute(text('SELECT a.id FROM accounts a JOIN auth_sessions s ON s.account_id=a.id '
                          'WHERE s.id=:session_id FOR UPDATE OF a'), {'session_id': session_id})
    row = conn.execute(text(PRINCIPAL + (' FOR UPDATE OF s' if lock else '')),
                       {'session_id': session_id}).mappings().one_or_none()
    if row is None:
        raise AuthFailure('session_expired', 401)
    result = dict(row)
    if result['must_change_password'] and not allow_password_change:
        raise AuthFailure('password_change_required', 403)
    return result


def session_from_token(raw):
    if not raw or len(raw) > 256:
        return None
    with engine().begin() as conn:
        session_id = conn.execute(text('SELECT id FROM auth_sessions WHERE token_digest=:digest'),
                                  {'digest': digest(raw)}).scalar_one_or_none()
        if session_id is None:
            return None
        try:
            current(conn, str(session_id), allow_password_change=True)
        except AuthFailure:
            return None
        conn.execute(text("""UPDATE auth_sessions SET last_seen_at=now(),
            idle_expires_at=LEAST(absolute_expires_at,now()+:idle*interval '1 second')
            WHERE id=:id"""), {'id': session_id, 'idle': settings().idle_seconds})
        return current(conn, str(session_id), allow_password_change=True)


def _create_session(conn, account, family_id=None, *, method='local'):
    raw, session_id = token(), str(uuid.uuid4())
    conn.execute(text("""INSERT INTO auth_sessions
        (id,account_id,token_digest,auth_version,family_id,auth_method,idle_expires_at,absolute_expires_at)
        VALUES(:id,:account,:digest,:version,:family,:method,now()+:idle*interval '1 second',
               now()+:absolute*interval '1 second')"""),
                 {'id': session_id, 'account': account['id'], 'digest': digest(raw),
                  'version': account['auth_version'], 'family': family_id or session_id, 'idle': settings().idle_seconds,
                  'absolute': settings().absolute_seconds, 'method': method})
    return raw


def login(normalized, password):
    with engine().connect() as conn:
        rows = conn.execute(text("SELECT * FROM accounts WHERE role='admin' AND "
                                 '(email_normalized=:email OR lower(username)=:email)'),
                            {'email': normalized}).mappings().all()
        row = rows[0] if len(rows) == 1 else None
    if not password_matches(row['password_hash'] if row else None, password) or row is None:
        raise AuthFailure('invalid_login', 401)
    with engine().begin() as conn:
        account = conn.execute(text('SELECT * FROM accounts WHERE id=:id FOR UPDATE'),
                               {'id': row['id']}).mappings().one()
        if account['password_hash'] != row['password_hash']:
            raise AuthFailure('invalid_login', 401)
        if account['role'] != 'admin':
            raise AuthFailure('invalid_login', 401)
        if not account['is_active']:
            raise AuthFailure('account_disabled', 403)
        if account['email_verified_at'] is None:
            raise AuthFailure('email_not_verified', 403)
        raw = _create_session(conn, account)
        audit(conn, account['id'], account['id'], 'login')
        return raw


def revoke_token(raw):
    if not raw or len(raw) > 256:
        return []
    with engine().begin() as conn:
        row = conn.execute(text("""SELECT a.id AS account_id,s.family_id FROM auth_sessions s
            JOIN accounts a ON a.id=s.account_id WHERE s.token_digest=:digest FOR UPDATE OF a"""),
                           {'digest': digest(raw)}).mappings().one_or_none()
        if row:
            revoked = conn.execute(text("""UPDATE auth_sessions SET revoked_at=COALESCE(revoked_at,now())
                WHERE family_id=:family RETURNING id"""), {'family': row['family_id']}).scalars().all()
            audit(conn, row['account_id'], row['account_id'], 'logout')
            return [str(value) for value in revoked]
        return []


def _issue_email(conn, account_id, registration_nonce):
    raw = token()
    conn.execute(text("""INSERT INTO email_verification_tokens
        (id,account_id,token_digest,registration_digest,expires_at)
        VALUES(:id,:account,:digest,:registration,now()+:ttl*interval '1 second')"""),
                 {'id': str(uuid.uuid4()), 'account': account_id, 'digest': digest(raw, 'email'),
                  'registration': digest(registration_nonce, 'registration') if registration_nonce else None,
                  'ttl': settings().verification_seconds})
    return raw


def register(email, normalized, display_name, encoded, nonce):
    with engine().begin() as conn:
        account_id = str(uuid.uuid4())
        created = conn.execute(text("""INSERT INTO accounts
            (username,id,email,email_normalized,display_name,password_hash,role,must_change_password)
            VALUES(:username,:id,:email,:normalized,:name,:password,'student',false)
            ON CONFLICT(email_normalized) WHERE email_normalized IS NOT NULL DO NOTHING RETURNING id"""),
                               {'username': 'local:' + account_id, 'id': account_id, 'email': email,
                                'normalized': normalized, 'name': display_name, 'password': encoded}).scalar_one_or_none()
        if created is None:
            return None
        raw = _issue_email(conn, created, nonce)
        audit(conn, None, created, 'register')
        return raw


def resend(normalized, nonce):
    with engine().begin() as conn:
        account = conn.execute(text("""SELECT * FROM accounts WHERE email_normalized=:email
            FOR UPDATE"""), {'email': normalized}).mappings().one_or_none()
        if not account or account['email_verified_at'] or not account['is_active']:
            return None
        prior = conn.execute(text("""SELECT registration_digest,created_at>now()-interval '60 seconds' AS recent
            FROM email_verification_tokens WHERE account_id=:id AND used_at IS NULL AND expires_at>now()
            ORDER BY created_at DESC"""), {'id': account['id']}).mappings().all()
        if len(prior) >= 3 or any(row['recent'] for row in prior):
            return None
        valid_nonce = nonce if nonce and any(row['registration_digest'] == digest(nonce, 'registration') for row in prior) else None
        return account['email'], _issue_email(conn, account['id'], valid_nonce)


def verify_email(raw, nonce, new_hash=None):
    if not isinstance(raw, str) or not 20 <= len(raw) <= 256:
        raise AuthFailure('verification_invalid')
    with engine().begin() as conn:
        account_id = conn.execute(text("""SELECT account_id FROM email_verification_tokens
            WHERE token_digest=:digest"""), {'digest': digest(raw, 'email')}).scalar_one_or_none()
        if not account_id:
            raise AuthFailure('verification_invalid')
        account = conn.execute(text('SELECT * FROM accounts WHERE id=:id FOR UPDATE'),
                               {'id': account_id}).mappings().one()
        proof = conn.execute(text("""SELECT * FROM email_verification_tokens
            WHERE token_digest=:digest AND used_at IS NULL AND expires_at>now() FOR UPDATE"""),
                             {'digest': digest(raw, 'email')}).mappings().one_or_none()
        if not proof or account['email_verified_at'] or not account['is_active']:
            raise AuthFailure('verification_invalid')
        same_browser = nonce and proof['registration_digest'] == digest(nonce, 'registration')
        if not same_browser and not new_hash:
            raise AuthFailure('verification_password_required', 409)
        conn.execute(text("""UPDATE accounts SET email_verified_at=now(),updated_at=now(),
            password_hash=COALESCE(:password,password_hash),must_change_password=false
            WHERE id=:id"""), {'password': new_hash, 'id': account_id})
        conn.execute(text('UPDATE email_verification_tokens SET used_at=now() WHERE account_id=:id'),
                     {'id': account_id})
        audit(conn, account_id, account_id, 'verify_email')


def change_password(principal, old_password, new_hash):
    with engine().begin() as conn:
        actor = current(conn, principal['session_id'], allow_password_change=True, lock=True)
        if actor['role'] != 'admin' or actor['auth_method'] != 'local':
            raise AuthFailure('use_vnu_password', 403)
        account = conn.execute(text('SELECT * FROM accounts WHERE id=:id FOR UPDATE'),
                               {'id': principal['account_id']}).mappings().one()
        if not password_matches(account['password_hash'], old_password):
            raise AuthFailure('invalid_login', 401)
        updated = conn.execute(text("""UPDATE accounts SET password_hash=:password,
            must_change_password=false,auth_version=auth_version+1,password_changed_at=now(),updated_at=now()
            WHERE id=:id RETURNING *"""),
                               {'password': new_hash, 'id': account['id']}).mappings().one()
        conn.execute(text('UPDATE auth_sessions SET revoked_at=now() WHERE account_id=:id'),
                     {'id': account['id']})
        audit(conn, account['id'], account['id'], 'change_password')
        family = conn.execute(text('SELECT family_id FROM auth_sessions WHERE id=:id'),
                              {'id': principal['session_id']}).scalar_one()
        return _create_session(conn, updated, family)


def portal_link(account_id, conn=None):
    query = text("""SELECT p.id::text AS owner,p.subject,p.generation
        FROM account_portal_links l JOIN portal_users p ON p.id=l.portal_owner_id
        WHERE l.account_id=:id""")
    if conn is not None:
        row = conn.execute(query, {'id': account_id}).mappings().one_or_none()
    else:
        with engine().connect() as connection:
            row = connection.execute(query, {'id': account_id}).mappings().one_or_none()
    return dict(row) if row else None


def list_users(principal, page, query):
    with engine().connect() as conn:
        actor = current(conn, principal['session_id'])
        if actor['role'] != 'admin':
            raise AuthFailure('forbidden', 403)
        where = "(email ILIKE :query OR display_name ILIKE :query OR vnu_subject ILIKE :query)"
        params = {'query': '%' + query + '%', 'offset': (page - 1) * 25}
        total = conn.execute(text('SELECT count(*) FROM accounts WHERE ' + where), params).scalar_one()
        rows = conn.execute(text('SELECT id::text,email,vnu_subject,display_name,role,is_active,email_verified_at,'
                                 'created_at,seeded_for_dev FROM accounts WHERE ' + where +
                                 ' ORDER BY created_at,id LIMIT 25 OFFSET :offset'), params).mappings().all()
        return {'items': [dict(row) for row in rows], 'total': total, 'page': page, 'page_size': 25}


def update_user(principal, target, changes):
    with engine().begin() as conn:
        conn.execute(text('SELECT pg_advisory_xact_lock(18107025)'))
        actor = current(conn, principal['session_id'], lock=True)
        if actor['role'] != 'admin':
            raise AuthFailure('forbidden', 403)
        row = conn.execute(text('SELECT * FROM accounts WHERE id=:id FOR UPDATE'),
                           {'id': target}).mappings().one_or_none()
        if row is None:
            raise AuthFailure('account_not_found', 404)
        role, active = changes.get('role', row['role']), changes.get('is_active', row['is_active'])
        if role == 'admin' and row['role'] != 'admin' and (not row['email_verified_at'] or not row['password_hash'].startswith('$argon2id$')):
            raise AuthFailure('admin_credentials_required', 409)
        if str(row['id']) == actor['account_id'] and (role != 'admin' or not active):
            raise AuthFailure('cannot_disable_self', 409)
        if row['role'] == 'admin' and row['is_active'] and (role != 'admin' or not active):
            admins = conn.execute(text("SELECT count(*) FROM accounts WHERE role='admin' AND is_active AND email_verified_at IS NOT NULL")).scalar_one()
            if admins <= 1:
                raise AuthFailure('last_admin', 409)
        conn.execute(text("""UPDATE accounts SET role=:role,is_active=:active,
            auth_version=auth_version+1,updated_at=now() WHERE id=:id"""),
                     {'role': role, 'active': active, 'id': target})
        conn.execute(text('UPDATE auth_sessions SET revoked_at=now() WHERE account_id=:id'), {'id': target})
        audit(conn, actor['account_id'], target, 'update_user')
