import asyncio
import threading
import time

import pytest

from app.api.portal import sync_job
from app.integrations.daotao import runtime, store


def test_cancel_while_reading_never_saves(monkeypatch):
    saved = []
    monkeypatch.setattr(store, "save", lambda *args: saved.append(args))

    async def scenario():
        entered = asyncio.Event()

        async def collect(value):
            entered.set()
            await asyncio.Event().wait()

        monkeypatch.setattr(runtime, "collect", collect)
        submitted = {"password": "synthetic"}
        value = runtime.Session("owner", "synthetic", 0, time.monotonic() + 30)
        monkeypatch.setitem(runtime.sessions, "synthetic-session", value)
        job = {"owner": "owner", "state": "running"}
        task = asyncio.create_task(sync_job(job, value, submitted))
        await entered.wait()
        task.cancel()
        await task
        assert job["state"] == "cancelled"
        assert submitted == {}

    asyncio.run(scenario())
    assert not saved


def test_shutdown_during_commit_waits_and_reports_saved(monkeypatch):
    entered, release = threading.Event(), threading.Event()

    def save(*args):
        entered.set()
        assert release.wait(3)
        return "saved"

    async def collect(value):
        return {"subject": "synthetic", "snapshot": {}}

    monkeypatch.setattr(store, "save", save)
    monkeypatch.setattr(runtime, "collect", collect)

    async def scenario():
        value = runtime.Session("owner", "synthetic", 0, time.monotonic() + 30)
        monkeypatch.setitem(runtime.sessions, "synthetic-session", value)
        job = {"owner": "owner", "state": "running"}
        task = asyncio.create_task(sync_job(job, value, {"password": "synthetic"}))
        assert await asyncio.to_thread(entered.wait, 3)
        assert job["state"] == "saving"
        task.cancel()
        await asyncio.sleep(0)
        release.set()
        await task
        assert job["state"] == "done"
        assert job["result"] == "saved"

    asyncio.run(scenario())


@pytest.mark.parametrize("revoked", [False, True])
def test_late_sync_does_not_save_after_expiry_or_revocation(monkeypatch, revoked):
    saved = []
    monkeypatch.setattr(store, "save", lambda *args: saved.append(args))

    async def scenario():
        value = runtime.Session("owner", "synthetic", 0, time.monotonic() + 30)
        monkeypatch.setitem(runtime.sessions, "synthetic-session", value)

        async def collect(credentials):
            if revoked:
                runtime.sessions.pop("synthetic-session")
            else:
                value.expiry = 0
            return {"subject": "synthetic", "snapshot": {}}

        monkeypatch.setattr(runtime, "collect", collect)
        submitted = {"password": "synthetic"}
        job = {"owner": "owner", "state": "running"}
        await sync_job(job, value, submitted)
        assert job["state"] == "failed"
        assert job["error"] == "session_expired"
        assert submitted == {}

    asyncio.run(scenario())
    assert not saved
