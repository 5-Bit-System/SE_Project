"""Same-origin, cookie-authenticated portal API. Raw provider errors never escape."""

import asyncio
import json
import logging
import secrets
import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.auth import COOKIE, revoke_connections, set_session, throttle
from app.auth import portal as account_portal
from app.auth import repository as auth_repository
from app.auth.dependencies import call as auth_call
from app.auth.dependencies import require_account
from app.integrations.daotao import runtime, store
from app.integrations.daotao.snapshot import PortalFailure, collection_review

router = APIRouter()
logger = logging.getLogger(__name__)


async def session(request):
    principal = await require_account(request)
    link = await auth_call(auth_repository.portal_link, principal['account_id'])
    if not link:
        raise HTTPException(409, 'vnu_not_connected')
    return account_portal.connection(principal, link)


async def credentials(request, *, subject=None):
    # Parse manually so framework validation never echoes a submitted password.
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 4096:
            raise HTTPException(413, "invalid_credentials")
    try:
        value = json.loads(raw)
        if subject is None and (not isinstance(value, dict) or set(value) != {'username', 'password'}):
            raise ValueError
        if subject is not None and (not isinstance(value, dict) or set(value) != {"password"}):
            raise ValueError
        username = subject if subject is not None else value["username"]
        password = value["password"]
        if not isinstance(username, str) or not isinstance(password, str):
            raise ValueError
        if not username.strip() or not password or len(username) > 128 or len(password) > 512:
            raise ValueError
        return {"username": username.strip(), "password": password}
    except (ValueError, TypeError, KeyError, UnicodeError):
        raise HTTPException(400, "invalid_credentials") from None


async def safe_call(fn, *args):
    try:
        return await asyncio.to_thread(fn, *args)
    except PortalFailure as exc:
        raise HTTPException(409, str(exc)) from None
    except Exception:
        raise HTTPException(503, "storage_unavailable") from None


@router.post("/auth/portal")
async def retired_login():
    raise HTTPException(410, 'use_system_login')


@router.post('/auth/vnu')
async def student_login(request: Request):
    submitted = await credentials(request)
    submitted['mode'] = 'signin'
    await throttle(request, 'vnu_login', submitted['username'].casefold(), 10, 900)
    try:
        result = await runtime.collect(submitted)
    except PortalFailure as exc:
        code = str(exc)
        status = {'identity_unverified': 401, 'timeout': 504, 'busy': 429,
                  'browser_unavailable': 503, 'network_access_denied': 503,
                  'interaction_required': 409}.get(code, 502)
        raise HTTPException(status, code) from None
    except Exception:
        raise HTTPException(502, 'portal_unavailable') from None
    finally:
        submitted.clear()
    raw, link, warning = await auth_call(account_portal.signin, result)
    try:
        principal = await auth_call(auth_repository.session_from_token, raw)
        if not principal:
            raise HTTPException(401, 'session_expired')
        value = account_portal.connection(principal, link)
        if isinstance(result.get('snapshot'), dict):
            value.latest_collection = collection_review(result['snapshot'],
                'retained' if warning == 'incomplete_snapshot' else 'accepted')
        await auth_call(account_portal.check, value)
        runtime.install_portal(value, result.get('cookies', []), value.portal_version)
        previous = await auth_call(auth_repository.revoke_token, request.cookies.get(COOKIE, ''))
        for session_id in previous:
            revoke_connections(session_id=session_id)
    except Exception:
        for session_id in await auth_call(auth_repository.revoke_token, raw):
            revoke_connections(session_id=session_id)
        raise
    response = JSONResponse({'authenticated': True, 'warning': warning})
    set_session(response, raw)
    return response


@router.post('/me/portal-connection')
async def login(request: Request):
    principal = await require_account(request)
    submitted = await credentials(request)
    try:
        result = await runtime.collect(submitted)
    except PortalFailure as exc:
        code = str(exc)
        status_code = {"identity_unverified": 409, "timeout": 504, "busy": 429,
                       "browser_unavailable": 503, "network_access_denied": 503,
                       "interaction_required": 409}.get(code, 502)
        raise HTTPException(status_code, code) from None
    except Exception as exc:
        logger.warning("Portal login stage=worker code=%s", type(exc).__name__)
        raise HTTPException(502, "portal_unavailable") from None
    finally:
        submitted.clear()
    link, warning = await auth_call(account_portal.connect, principal, result)
    principal = await require_account(request)
    value = account_portal.connection(principal, link)
    version = value.portal_version
    value.latest_collection = collection_review(result['snapshot'],
        'retained' if warning == 'incomplete_snapshot' else 'accepted')
    await auth_call(account_portal.check, value)
    try:
        runtime.install_portal(value, result.get('cookies', []), version)
    except PortalFailure as exc:
        raise HTTPException(409, str(exc)) from None
    return {'connected': True, 'warning': warning}


@router.get('/me/portal-connection')
async def connection_status(request: Request):
    principal = await require_account(request)
    link = await auth_call(auth_repository.portal_link, principal['account_id'])
    value = runtime.sessions.get('app:' + principal['session_id'])
    return {'linked': bool(link), 'connected': bool(value and value.portal
            and value.portal['expiry'] > time.monotonic())}


@router.get("/me/profile")
async def profile(request: Request):
    principal = await require_account(request)
    link = await auth_call(auth_repository.portal_link, principal['account_id'])
    if not link:
        return {'subject': None, 'profile': {}, 'snapshot': None, 'fetched_at': None,
                'last_synced_at': None, 'expires_in': principal['expires_in']}
    value = account_portal.connection(principal, link)
    result = await safe_call(store.profile, value.owner)
    await auth_call(account_portal.check, value)
    result["expires_in"] = principal['expires_in']
    result['latest_collection'] = value.latest_collection
    return result


@router.delete('/me/portal-connection')
async def logout(request: Request):
    principal = await require_account(request)
    value = runtime.sessions.get('app:' + principal['session_id'])
    if value:
        runtime.revoke(value)
    await asyncio.gather(*(j["task"] for j in runtime.jobs.values()
                           if j.get("session") is value and j["state"] == "saving"),
                         return_exceptions=True)
    return {'disconnected': True}


async def sync_job(job, value, submitted):
    version = job.get("portal_version", value.portal_version)
    captured = None
    try:
        if value.app_session_id:
            await auth_call(account_portal.check, value)
        if job["state"] != "running":
            return
        if not runtime.session_active(value):
            raise PortalFailure('vnu_reauth_required' if value.app_session_id else 'session_expired')
        if value.portal_version != version:
            raise PortalFailure("vnu_reauth_required" if not value.portal else "cancelled")
        result = await runtime.collect(submitted)
        if result["subject"] != value.subject:
            if value.app_session_id:
                runtime.clear_portal(value)
            else:
                runtime.revoke(value)
            raise PortalFailure("identity_unverified")
        if value.app_session_id:
            await auth_call(account_portal.check, value)
        if job["state"] != "running":
            return
        if not runtime.session_active(value):
            raise PortalFailure('vnu_reauth_required' if value.app_session_id else 'session_expired')
        if value.portal_version != version:
            raise PortalFailure("vnu_reauth_required" if not value.portal else "cancelled")
        if "cookies" in result:
            runtime.install_portal(value, result["cookies"], version)
        captured = result['snapshot']
        job["state"] = "saving"
        saving = asyncio.create_task(auth_call(account_portal.save, value, result['snapshot'], result.get('profile'))
                                     if value.app_session_id else safe_call(store.save, value.owner,
                                     value.generation, result['snapshot'], result.get('profile')))
        try:
            job["result"] = await asyncio.shield(saving)
        except asyncio.CancelledError:
            # A DB thread cannot be cancelled. Wait rather than report a false rollback.
            job["result"] = await saving
        job["state"] = "done"
        if runtime.session_active(value):
            value.latest_collection = collection_review(captured, job['result'])
    except asyncio.CancelledError:
        job["state"] = "cancelled"
        if runtime.session_active(value):
            runtime.clear_portal(value)
    except Exception as exc:
        job["state"] = "failed"
        job["error"] = exc.detail if isinstance(exc, HTTPException) else (
            str(exc) if isinstance(exc, PortalFailure) else "portal_unavailable")
        if captured is not None and runtime.session_active(value):
            value.latest_collection = collection_review(captured,
                'retained' if job['error'] == 'incomplete_snapshot' else 'failed')
        if value.app_session_id and job['error'] in {'session_expired', 'password_change_required', 'forbidden', 'vnu_not_connected'}:
            runtime.revoke(value)
        if job["error"] == "vnu_reauth_required" and value.portal_version == version:
            runtime.clear_portal(value)
    finally:
        submitted.clear()


def start_job(value, submitted):
    if not runtime.session_active(value):
        submitted.clear()
        raise HTTPException(401, "session_expired")
    if any(j["owner"] == value.owner and j["state"] in {"running", "saving"}
           for j in runtime.jobs.values()):
        submitted.clear()
        raise HTTPException(409, "busy")
    runtime.reap()
    if len(runtime.jobs) >= 1000:
        submitted.clear()
        raise HTTPException(429, "busy")
    job_id = secrets.token_urlsafe(24)
    job = {"owner": value.owner, "session": value,
           "state": "running", "created": time.monotonic(), "portal_version": value.portal_version}
    task = asyncio.create_task(sync_job(job, value, submitted))
    job["task"] = task
    runtime.jobs[job_id] = job
    runtime.tasks.add(task)
    task.add_done_callback(runtime.tasks.discard)
    return {"id": job_id, "state": "running"}


@router.post("/me/portal-sync", status_code=202)
async def sync(request: Request):
    value = await session(request)
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 4096:
            raise HTTPException(413, "invalid_sync_request")
    if raw.strip():
        try:
            if json.loads(raw) != {}:
                raise ValueError
        except (ValueError, UnicodeError):
            raise HTTPException(400, "invalid_sync_request") from None
    try:
        submitted = runtime.resume_request(value)
    except PortalFailure as exc:
        if str(exc) == 'vnu_reauth_required':
            # No job has failed: this is a normal interaction step for an
            # authenticated app user whose temporary provider state expired.
            return JSONResponse({'state': 'reauth_required'}, status_code=200)
        raise HTTPException(401 if str(exc) == "session_expired" else 409, str(exc)) from None
    return start_job(value, submitted)


@router.post("/me/portal-reauth", status_code=202)
async def reauthenticate(request: Request):
    value = await session(request)
    submitted = await credentials(request, subject=value.subject)
    submitted["mode"] = "login"
    return start_job(value, submitted)


async def owned_job(request, job_id):
    value = await session(request)
    job = runtime.jobs.get(job_id)
    if job is None or job["owner"] != value.owner or job.get("session") is not value:
        raise HTTPException(404, "job_not_found")
    return job


@router.get("/me/portal-sync/{job_id}")
async def job_status(request: Request, job_id: str):
    job = await owned_job(request, job_id)
    return {k: v for k, v in job.items() if k in {"state", "error", "result"}}


@router.delete("/me/portal-sync/{job_id}")
async def cancel(request: Request, job_id: str):
    job = await owned_job(request, job_id)
    if job["state"] == "running":
        job["state"] = "cancelled"
        job["task"].cancel()
        await asyncio.gather(job["task"], return_exceptions=True)
        if runtime.session_active(job["session"]):
            runtime.clear_portal(job["session"])
    elif job["state"] == "saving":
        await job["task"]
    return {"state": job["state"]}


@router.delete("/me/portal-data")
async def clear(request: Request):
    principal = await require_account(request)
    link = await auth_call(account_portal.clear, principal)
    if link:
        runtime.revoke_owner(link['owner'])
    return {'deleted': True}
