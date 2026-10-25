"""Local administrator authentication and shared app-session lifecycle."""

import asyncio
import hmac

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.auth import repository
from app.auth.dependencies import COOKIE, call, optional_account, require_account
from app.auth.security import csrf, password_hash
from app.auth.settings import settings
from app.integrations.daotao import runtime

router = APIRouter()
hash_slots = asyncio.Semaphore(4)


async def body(request, allowed, required):
    import json
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 4096:
            raise HTTPException(413, 'invalid_auth_request')
    try:
        value = json.loads(raw)
        if (not isinstance(value, dict) or set(value) - set(allowed) or not set(required) <= set(value)
                or any(not isinstance(v, str) for v in value.values())):
            raise ValueError
        return value
    except (ValueError, UnicodeError):
        raise HTTPException(400, 'invalid_auth_request') from None


async def encode(value):
    async with hash_slots:
        return await call(password_hash, value)


async def throttle(request, action, normalized='', limit=10, window=900):
    ip = request.client.host if request.client else 'unknown'
    await call(repository.rate, action + ':ip', ip, limit * 3, window)
    if normalized:
        await call(repository.rate, action + ':account', normalized, limit, window)


def set_session(response, raw):
    config = settings()
    response.set_cookie(COOKIE, raw, httponly=True, secure=config.base_url.startswith('https:'),
                        samesite='lax', max_age=config.absolute_seconds, path='/')
    response.delete_cookie('study_portal_session')


def revoke_connections(session_id=None, account_id=None):
    for value in list(runtime.sessions.values()):
        if ((session_id is not None and value.app_session_id == session_id)
                or (account_id is not None and value.account_id == account_id)):
            runtime.revoke(value)


@router.post('/auth/register')
@router.post('/auth/email/resend')
@router.post('/auth/email/verify')
async def retired_email_auth():
    raise HTTPException(410, 'use_vnu_login')


@router.post('/auth/login')
async def login(request: Request):
    value = await body(request, {'email', 'username', 'password'}, {'password'})
    if ('email' in value) == ('username' in value):
        raise HTTPException(400, 'invalid_auth_request')
    normalized = value.get('username', value.get('email', '')).strip().lower()
    if not 1 <= len(normalized) <= 254:
        raise HTTPException(400, 'invalid_auth_request')
    if not 1 <= len(value['password']) <= 128:
        raise HTTPException(400, 'invalid_auth_request')
    await throttle(request, 'login', normalized)
    async with hash_slots:
        raw = await call(repository.login, normalized, value['password'])
    value.clear()
    previous = await call(repository.revoke_token, request.cookies.get(COOKIE, ''))
    for session_id in previous:
        revoke_connections(session_id=session_id)
    response = JSONResponse({'authenticated': True})
    set_session(response, raw)
    return response


@router.get('/auth/session')
async def session_status(request: Request):
    principal = await optional_account(request)
    if not principal:
        return {'authenticated': False}
    return {'authenticated': True, 'account': principal, 'csrf_token': csrf(request.cookies[COOKIE])}


@router.get('/auth/me')
async def me(request: Request):
    return await require_account(request, allow_password_change=True)


@router.post('/auth/logout')
async def logout(request: Request):
    principal = await optional_account(request)
    if principal:
        await require_account(request, allow_password_change=True)
    elif request.cookies.get(COOKIE) and not hmac.compare_digest(
            request.headers.get('x-csrf-token', ''), csrf(request.cookies[COOKIE])):
        raise HTTPException(403, 'csrf_rejected')
    session_ids = await call(repository.revoke_token, request.cookies.get(COOKIE, ''))
    for session_id in session_ids:
        revoke_connections(session_id=session_id)
    await asyncio.gather(*(job['task'] for job in runtime.jobs.values()
                           if job['state'] == 'saving' and job['session'].app_session_id in session_ids),
                         return_exceptions=True)
    response = JSONResponse({'logged_out': True})
    response.delete_cookie(COOKIE)
    response.delete_cookie('study_portal_session')
    return response


@router.post('/me/password')
async def change_password(request: Request):
    principal = await require_account(request, allow_password_change=True)
    if principal['role'] != 'admin':
        raise HTTPException(403, 'use_vnu_password')
    value = await body(request, {'current_password', 'new_password'}, {'current_password', 'new_password'})
    await throttle(request, 'password', principal['account_id'])
    encoded = await encode(value['new_password'])
    raw = await call(repository.change_password, principal, value['current_password'], encoded)
    value.clear()
    revoke_connections(account_id=principal['account_id'])
    response = JSONResponse({'changed': True})
    set_session(response, raw)
    return response


@router.get('/admin/users')
async def users(request: Request, page: int = 1, q: str = ''):
    principal = await require_account(request)
    if principal['role'] != 'admin':
        raise HTTPException(403, 'forbidden')
    if not 1 <= page <= 100000 or len(q) > 100:
        raise HTTPException(400, 'invalid_auth_request')
    return await call(repository.list_users, principal, page, q)


@router.patch('/admin/users/{account_id}')
async def update_user(request: Request, account_id: str):
    import json
    import uuid
    principal = await require_account(request)
    if principal['role'] != 'admin':
        raise HTTPException(403, 'forbidden')
    try:
        uuid.UUID(account_id)
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 1024:
                raise ValueError
        changes = json.loads(raw)
        if (not isinstance(changes, dict) or not changes or set(changes) - {'role', 'is_active'}
                or ('role' in changes and changes['role'] not in {'student', 'admin'})
                or ('is_active' in changes and not isinstance(changes['is_active'], bool))):
            raise ValueError
    except (ValueError, TypeError, UnicodeError):
        raise HTTPException(400, 'invalid_auth_request') from None
    await call(repository.update_user, principal, account_id, changes)
    revoke_connections(account_id=account_id)
    return {'updated': True}
