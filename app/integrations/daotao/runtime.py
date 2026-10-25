"""Bounded workers and short-lived web sessions; no portal cookies survive a job."""

import asyncio
import hashlib
import json
import logging
import os
import secrets
import sys
import time
from dataclasses import dataclass

from app.integrations.daotao.snapshot import PortalFailure

slots = asyncio.Semaphore(2)
sessions = {}
jobs = {}
tasks = set()
logger = logging.getLogger(__name__)


@dataclass
class Session:
    owner: str
    subject: str
    generation: int
    expiry: float
    latest_collection: dict | None = None


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def session_active(value):
    return value.expiry > time.monotonic() and any(
        active is value for active in sessions.values())


def cancel_session(value):
    for job in jobs.values():
        if job.get("session") is value and job["state"] == "running":
            job["state"] = "cancelled"
            job["task"].cancel()


def new_session(owner, subject, generation):
    now = time.monotonic()
    for key, value in list(sessions.items()):
        if value.expiry <= now:
            sessions.pop(key, None)
    if len(sessions) >= 1000:
        raise PortalFailure("busy")
    token = secrets.token_urlsafe(32)
    sessions[digest(token)] = Session(owner, subject, generation, now + 1800)
    return token


async def collect(credentials):
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
                json.dumps(credentials).encode()), timeout=120)
            if process.returncode != 0:
                logger.warning("Portal worker stage=exit code=%s", process.returncode)
                raise PortalFailure("worker_failed")
            try:
                result = json.loads(output.decode("utf-8"))
                if not isinstance(result, dict):
                    raise ValueError
                if "error" not in result and (
                        not isinstance(result.get("subject"), str)
                        or not isinstance(result.get("snapshot"), dict)):
                    raise ValueError
            except (UnicodeError, ValueError):
                logger.warning("Portal worker stage=decode code=invalid_output")
                raise PortalFailure("worker_output_invalid") from None
            if "error" in result:
                raise PortalFailure(result["error"])
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


def cancel_owner(owner):
    for job in jobs.values():
        if job["owner"] == owner and job["state"] == "running":
            job["state"] = "cancelled"
            job["task"].cancel()


async def shutdown():
    for task in list(tasks):
        task.cancel()
    await asyncio.gather(*list(tasks), return_exceptions=True)
    sessions.clear()
    jobs.clear()
