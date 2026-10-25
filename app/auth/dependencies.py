"""Shared system-auth boundary for API routes and VNU jobs."""

import asyncio
import hmac

from fastapi import HTTPException, Request

from app.auth import repository
from app.auth.security import AuthFailure, csrf

COOKIE = 'study_app_session'


async def call(fn, *args, **kwargs):
    try:
        return await asyncio.to_thread(fn, *args, **kwargs)
    except AuthFailure as exc:
        raise HTTPException(exc.status, exc.code) from None
    except Exception:
        raise HTTPException(503, 'storage_unavailable') from None


async def optional_account(request):
    raw = request.cookies.get(COOKIE, '')
    if not raw:
        return None
    return await call(repository.session_from_token, raw)


async def require_account(request, *, allow_password_change=False):
    principal = await optional_account(request)
    if not principal:
        raise HTTPException(401, 'session_expired')
    if principal['must_change_password'] and not allow_password_change:
        raise HTTPException(403, 'password_change_required')
    if request.method not in {'GET', 'HEAD'}:
        provided = request.headers.get('x-csrf-token', '')
        if not hmac.compare_digest(provided, csrf(request.cookies[COOKIE])):
            raise HTTPException(403, 'csrf_rejected')
    return principal


async def require_admin(request):
    principal = await require_account(request)
    if principal['role'] != 'admin':
        raise HTTPException(403, 'forbidden')
    return principal


async def verified_account(request: Request):
    return await require_account(request)


async def retired_profile():
    raise HTTPException(410, 'use_account_profile')
