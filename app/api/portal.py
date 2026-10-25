"""Same-origin, cookie-authenticated portal API. Raw provider errors never escape."""

import asyncio
import json
import logging
import secrets
import time

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.integrations.daotao import runtime, store
from app.integrations.daotao.snapshot import PortalFailure, collection_review

router = APIRouter()
COOKIE = "study_portal_session"
logger = logging.getLogger(__name__)


def session(request):
    key = runtime.digest(request.cookies.get(COOKIE, ""))
    value = runtime.sessions.get(key)
    if value is None or value.expiry <= time.monotonic():
        runtime.sessions.pop(key, None)
        if value is not None:
            runtime.cancel_session(value)
        raise HTTPException(401, "session_expired")
    return value


async def credentials(request):
    # Parse manually so framework validation never echoes a submitted password.
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 4096:
            raise HTTPException(413, "invalid_credentials")
    try:
        value = json.loads(raw)
        username, password = value["username"], value["password"]
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
async def login(request: Request):
    submitted = await credentials(request)
    old = request.cookies.get(COOKIE)
    if old:
        previous = runtime.sessions.pop(runtime.digest(old), None)
        if previous:
            runtime.cancel_owner(previous.owner)
    try:
        result = await runtime.collect(submitted)
    except PortalFailure as exc:
        code = str(exc)
        status_code = {"identity_unverified": 401, "timeout": 504, "busy": 429,
                       "browser_unavailable": 503, "interaction_required": 409}.get(code, 502)
        raise HTTPException(status_code, code) from None
    except Exception as exc:
        logger.warning("Portal login stage=worker code=%s", type(exc).__name__)
        raise HTTPException(502, "portal_unavailable") from None
    finally:
        submitted.clear()
    owner, generation = await safe_call(store.owner, result["subject"])
    # A returning user may view their old snapshot even if this read is incomplete.
    try:
        saved = await safe_call(store.save, owner, generation, result["snapshot"], result.get("profile"))
        warning = None
    except HTTPException as exc:
        if exc.detail != "incomplete_snapshot":
            raise
        warning = "incomplete_snapshot"
        saved = "retained"
    token = runtime.new_session(owner, result["subject"], generation)
    runtime.sessions[runtime.digest(token)].latest_collection = collection_review(result["snapshot"], saved)
    if warning:
        logger.warning("Portal collection retained report=%s", json.dumps(
            runtime.sessions[runtime.digest(token)].latest_collection, sort_keys=True))
    old = request.cookies.get(COOKIE)
    if old:
        runtime.sessions.pop(runtime.digest(old), None)
    response = JSONResponse({"authenticated": True, "warning": warning})
    response.set_cookie(COOKIE, token, httponly=True, samesite="strict", max_age=1800,
                        secure=request.url.scheme == "https")
    return response


@router.get("/auth/me")
def me(request: Request):
    return {"subject": session(request).subject}


@router.get("/me/profile")
async def profile(request: Request):
    value = session(request)
    result = await safe_call(store.profile, value.owner)
    if not runtime.session_active(value):
        raise HTTPException(401, "session_expired")
    result["expires_in"] = max(0, int(value.expiry - time.monotonic()))
    result["latest_collection"] = value.latest_collection
    return result


@router.post("/auth/logout")
async def logout(request: Request):
    # Logout must also clear an already expired/revoked cookie.
    value = runtime.sessions.pop(runtime.digest(request.cookies.get(COOKIE, "")), None)
    if value is None:
        response = JSONResponse({"logged_out": True})
        response.delete_cookie(COOKIE)
        return response
    runtime.cancel_owner(value.owner)
    # Once a transaction is committing, finish it before acknowledging logout.
    await asyncio.gather(*(j["task"] for j in runtime.jobs.values()
                           if j["owner"] == value.owner and j["state"] == "saving"),
                         return_exceptions=True)
    response = JSONResponse({"logged_out": True})
    response.delete_cookie(COOKIE)
    return response


async def sync_job(job, value, submitted):
    captured = None
    try:
        result = await runtime.collect(submitted)
        if result["subject"] != value.subject:
            raise PortalFailure("identity_unverified")
        if job["state"] != "running":
            return
        if not runtime.session_active(value):
            raise PortalFailure("session_expired")
        captured = result["snapshot"]
        job["state"] = "saving"
        saving = asyncio.create_task(safe_call(store.save, value.owner, value.generation,
                                              result["snapshot"], result.get("profile")))
        try:
            job["result"] = await asyncio.shield(saving)
        except asyncio.CancelledError:
            # A DB thread cannot be cancelled. Wait rather than report a false rollback.
            job["result"] = await saving
        job["state"] = "done"
        value.latest_collection = collection_review(captured, job["result"])
    except asyncio.CancelledError:
        job["state"] = "cancelled"
    except Exception as exc:
        job["state"] = "failed"
        job["error"] = exc.detail if isinstance(exc, HTTPException) else (
            str(exc) if isinstance(exc, PortalFailure) else "portal_unavailable")
        if captured is not None and runtime.session_active(value):
            value.latest_collection = collection_review(captured,
                "retained" if job["error"] == "incomplete_snapshot" else "failed")
            if job["error"] == "incomplete_snapshot":
                logger.warning("Portal collection retained report=%s",
                               json.dumps(value.latest_collection, sort_keys=True))
    finally:
        submitted.clear()


@router.post("/me/portal-sync", status_code=202)
async def sync(request: Request):
    value = session(request)
    submitted = await credentials(request)
    if submitted["username"].casefold() != value.subject:
        raise HTTPException(400, "identity_unverified")
    if any(j["owner"] == value.owner and j["state"] in {"running", "saving"}
           for j in runtime.jobs.values()):
        raise HTTPException(409, "busy")
    for key, job in list(runtime.jobs.items()):
        if job["state"] not in {"running", "saving"} and job["created"] < time.monotonic() - 1800:
            runtime.jobs.pop(key, None)
    if len(runtime.jobs) >= 1000:
        raise HTTPException(429, "busy")
    job_id = secrets.token_urlsafe(24)
    job = {"owner": value.owner, "session": value,
           "state": "running", "created": time.monotonic()}
    task = asyncio.create_task(sync_job(job, value, submitted))
    job["task"] = task
    runtime.jobs[job_id] = job
    runtime.tasks.add(task)
    task.add_done_callback(runtime.tasks.discard)
    return {"id": job_id, "state": "running"}


def owned_job(request, job_id):
    value = session(request)
    job = runtime.jobs.get(job_id)
    if job is None or job["owner"] != value.owner:
        raise HTTPException(404, "job_not_found")
    return job


@router.get("/me/portal-sync/{job_id}")
def job_status(request: Request, job_id: str):
    job = owned_job(request, job_id)
    return {k: v for k, v in job.items() if k in {"state", "error", "result"}}


@router.delete("/me/portal-sync/{job_id}")
async def cancel(request: Request, job_id: str):
    job = owned_job(request, job_id)
    if job["state"] == "running":
        job["state"] = "cancelled"
        job["task"].cancel()
        await job["task"]
    elif job["state"] == "saving":
        await job["task"]
    return {"state": job["state"]}


@router.delete("/me/portal-data")
async def clear(request: Request):
    value = session(request)
    runtime.cancel_owner(value.owner)
    await safe_call(store.clear, value.owner)
    for key, active in list(runtime.sessions.items()):
        if active.owner == value.owner:
            runtime.sessions.pop(key, None)
    response = JSONResponse({"deleted": True})
    response.delete_cookie(COOKIE)
    return response
