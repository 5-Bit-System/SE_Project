"""Bounded workers and session-scoped VNU cookies, held in process memory only."""

import asyncio
import hashlib
import json
import logging
import os
import secrets
import sys
import time
from dataclasses import dataclass, field

from app.integrations.daotao.session_state import MAX_INPUT_BYTES, validated_cookies
from app.integrations.daotao.snapshot import PortalFailure

slots = asyncio.Semaphore(2)
sessions = {}
jobs = {}
tasks = set()
logger = logging.getLogger(__name__)
cleanup_task = None
WORKER_ERRORS = {"identity_unverified", "interaction_required", "structure_changed",
                 "browser_unavailable", "portal_unavailable", "timeout", "vnu_reauth_required",
                 "portal_state_invalid"}
WORKER_STAGES = {"browser_start", "browser_context", "login", "resume", "profile", "transcript",
                 "identity", "parse"}
WORKER_KINDS = {"missing_dependency", "source_rejected", "timeout", "browser_error",
                "unexpected_error"}


@dataclass
class Session:
    owner: str
    subject: str
    generation: int
    expiry: float
    portal: dict | None = field(default=None, repr=False)
    portal_version: int = 0
    account_id: str | None = None
    app_session_id: str | None = None


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def session_active(value):
    if value.expiry <= time.monotonic():
        revoke(value)
        return False
    return any(active is value for active in sessions.values())


def clear_portal(value):
    if value.portal:
        value.portal["cookies"].clear()
    value.portal = None
    value.portal_version += 1


def install_portal(value, cookies, version):
    if not session_active(value) or value.portal_version != version:
        raise PortalFailure("cancelled")
    cookies = validated_cookies(cookies)
    clear_portal(value)
    if not cookies:
        return
    known_expiries = [c["expires"] for c in cookies if c.get("expires", -1) >= 0]
    expiry = value.expiry
    if known_expiries:
        expiry = min(expiry, time.monotonic() + min(known_expiries) - time.time())
    if expiry > time.monotonic():
        value.portal = {"cookies": cookies, "expiry": expiry}


def resume_request(value):
    if not session_active(value):
        raise PortalFailure("session_expired")
    if not value.portal or value.portal["expiry"] <= time.monotonic():
        clear_portal(value)
        raise PortalFailure("vnu_reauth_required")
    return {"mode": "resume", "subject": value.subject,
            "cookies": validated_cookies(value.portal["cookies"])}


def cancel_session(value):
    for job in jobs.values():
        if job.get("session") is value and job["state"] == "running":
            job["state"] = "cancelled"
            job["task"].cancel()


def revoke(value):
    clear_portal(value)
    for key, active in list(sessions.items()):
        if active is value:
            sessions.pop(key, None)
    cancel_session(value)


def revoke_owner(owner):
    for value in list(sessions.values()):
        if value.owner == owner:
            revoke(value)


def reap():
    now = time.monotonic()
    for value in list(sessions.values()):
        if value.expiry <= now:
            revoke(value)
        elif value.portal and value.portal["expiry"] <= now:
            clear_portal(value)
    for key, job in list(jobs.items()):
        if job["state"] not in {"running", "saving"} and job["created"] < now - 1800:
            jobs.pop(key, None)


def startup():
    global cleanup_task

    async def cleanup():
        while True:
            await asyncio.sleep(30)
            reap()

    cleanup_task = asyncio.create_task(cleanup())


def new_session(owner, subject, generation, cookies=None):
    now = time.monotonic()
    reap()
    if len(sessions) >= 1000:
        raise PortalFailure("busy")
    token = secrets.token_urlsafe(32)
    value = Session(owner, subject, generation, now + 1800)
    sessions[digest(token)] = value
    try:
        if cookies is not None:
            install_portal(value, cookies, value.portal_version)
    except Exception:
        revoke(value)
        raise
    return token


async def collect(credentials):
    body = json.dumps(credentials).encode("utf-8")
    if len(body) > MAX_INPUT_BYTES:
        raise PortalFailure("portal_state_invalid")
    if slots.locked():
        raise PortalFailure("busy")
    async with slots:
        env = {k: v for k, v in os.environ.items() if k not in {"DEBUG", "PWDEBUG"}}
        env["PYTHONIOENCODING"] = "utf-8"
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "app.integrations.daotao.worker",
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL, env=env,
            creationflags=0x08000000 if os.name == "nt" else 0,
        )
        try:
            output, _ = await asyncio.wait_for(process.communicate(
                body), timeout=120)
            if process.returncode != 0:
                logger.warning("Portal worker stage=exit code=%s", process.returncode)
                raise PortalFailure("worker_failed")
            try:
                result = json.loads(output.decode("utf-8"))
                if not isinstance(result, dict):
                    raise ValueError
                if "error" not in result:
                    if not isinstance(result.get('subject'), str):
                        raise ValueError
                    if credentials.get('mode') == 'signin':
                        if (result.get('authenticated') is not True
                                or result['subject'] != credentials['username'].strip().casefold()
                                or result.get('warning') not in {None, 'source_unavailable'}
                                or (result.get('snapshot') is None and result.get('warning') != 'source_unavailable')):
                            raise ValueError
                    if not isinstance(result.get('snapshot'), dict) and not (
                            credentials.get('mode') == 'signin' and result.get('snapshot') is None):
                        raise ValueError
            except (UnicodeError, ValueError):
                logger.warning("Portal worker stage=decode code=invalid_output")
                raise PortalFailure("worker_output_invalid") from None
            if "error" in result:
                # Worker diagnostics are strictly allowlisted, never raw exception text.
                code = result["error"]
                if not isinstance(code, str) or code not in WORKER_ERRORS:
                    code = "portal_unavailable"
                stage = result.get("stage")
                kind = result.get("kind")
                stage = stage if isinstance(stage, str) and stage in WORKER_STAGES else "unknown"
                kind = kind if isinstance(kind, str) and kind in WORKER_KINDS else "unknown"
                logger.warning("Portal worker stage=%s code=%s kind=%s", stage, code, kind)
                raise PortalFailure(code)
            if "cookies" in result:
                try:
                    result["cookies"] = validated_cookies(result["cookies"])
                except PortalFailure:
                    raise PortalFailure("worker_output_invalid") from None
            return result
        except TimeoutError:
            raise PortalFailure("timeout") from None
        finally:
            if process.returncode is None:
                if os.name == "nt":
                    killer = await asyncio.create_subprocess_exec(
                        "taskkill", "/PID", str(process.pid), "/T", "/F",
                        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
                        creationflags=0x08000000,
                    )
                    await killer.wait()
                else:
                    process.kill()
                await process.wait()


async def shutdown():
    global cleanup_task
    if cleanup_task:
        cleanup_task.cancel()
        await asyncio.gather(cleanup_task, return_exceptions=True)
        cleanup_task = None
    for value in list(sessions.values()):
        revoke(value)
    for task in list(tasks):
        if not task.cancelling():
            task.cancel()
    await asyncio.gather(*list(tasks), return_exceptions=True)
    sessions.clear()
    jobs.clear()
