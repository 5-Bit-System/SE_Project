"""Synthetic ASGI workload for VT-102; real auth/API/queue, fake VNU process and store."""

import asyncio
import json
import math
import time

import httpx

from app.auth.security import csrf
from app.integrations.daotao import runtime, store
from app.main import app
from tests.integrations.test_portal_sessions import cookie
from tests.support.system_auth import SyntheticAccounts


async def workload(monkeypatch, count=40):
    monkeypatch.setattr(runtime, "sessions", {})
    monkeypatch.setattr(runtime, "jobs", {})
    monkeypatch.setattr(runtime, "tasks", set())
    monkeypatch.setattr(runtime, "slots", asyncio.Semaphore(2))
    accounts = SyntheticAccounts(monkeypatch)
    release, two_started = asyncio.Event(), asyncio.Event()
    trace = {"active": 0, "maximum": 0, "collector": 0, "save": 0}
    timings = {"post": [], "retry": [], "poll": []}
    responses, clients = [], []

    class Process:
        returncode = None

        async def communicate(self, body):
            request = json.loads(body)
            trace["active"] += 1
            trace["collector"] += 1
            trace["maximum"] = max(trace["maximum"], trace["active"])
            if trace["active"] == 2:
                two_started.set()
            try:
                await release.wait()
                result = {"subject": request["subject"], "profile": {}, "snapshot": {
                    "digest": "invented-" + request["subject"], "completeness": "complete",
                    "attempts": []}}
                self.returncode = 0
                return json.dumps(result).encode(), b""
            finally:
                trace["active"] -= 1

    async def create_process(*args, **kwargs):
        return Process()

    def save(*args):
        trace["save"] += 1
        return "saved"

    monkeypatch.setattr(asyncio, "create_subprocess_exec", create_process)
    monkeypatch.setattr(store, "save", save)

    async def measured(client, category, method, path, **kwargs):
        started = time.perf_counter()
        response = await client.request(method, path, **kwargs)
        timings[category].append(time.perf_counter() - started)
        responses.append(response.status_code)
        return response

    async with app.router.lifespan_context(app):
        try:
            for index in range(count):
                client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                    base_url="http://127.0.0.1:8000", headers={"Origin": "http://127.0.0.1:8000"})
                accounts.issue(client, owner=f"vt102-synthetic-{index}", linked=True, cookies=[cookie()])
                raw = client.cookies.get("study_app_session")
                client.headers["X-CSRF-Token"] = csrf(raw)
                client.headers["Idempotency-Key"] = f"vt102-load-request-{index:04d}"
                clients.append(client)
            acknowledgements = await asyncio.gather(*[
                measured(client, "post", "POST", "/me/portal-sync") for client in clients])
            assert all(response.status_code == 202 for response in acknowledgements)
            ids = [response.json()["id"] for response in acknowledgements]
            assert len(set(ids)) == count
            await asyncio.wait_for(two_started.wait(), 3)
            retries = await asyncio.gather(*[
                measured(client, "retry", "POST", "/me/portal-sync") for client in clients])
            assert all(response.status_code == 202 for response in retries)
            assert [response.json()["id"] for response in retries] == ids
            pending = await asyncio.gather(*[
                measured(client, "poll", "GET", f"/me/portal-sync/{job_id}")
                for client, job_id in zip(clients, ids)])
            phases = [response.json().get("phase") for response in pending]
            assert phases.count("collecting") == min(2, count), phases
            assert phases.count("queued") == count - min(2, count), phases
            release.set()
            await asyncio.wait_for(asyncio.gather(*list(runtime.tasks)), 10)
            completed = await asyncio.gather(*[
                measured(client, "poll", "GET", f"/me/portal-sync/{job_id}")
                for client, job_id in zip(clients, ids)])
            assert all(response.json().get("progress_percent") == 100
                       and response.json().get("state") == "done" for response in completed)
            assert trace["collector"] == trace["save"] == len(runtime.jobs) == count
            assert trace["maximum"] == 2
        finally:
            release.set()
            await asyncio.gather(*list(runtime.tasks), return_exceptions=True)
            await asyncio.gather(*(client.aclose() for client in clients))

    def metrics(values):
        ordered = sorted(values)
        return {"samples": len(values), "min_ms": round(min(values) * 1000, 3),
                "avg_ms": round(sum(values) / len(values) * 1000, 3),
                "p95_ms": round(ordered[math.ceil(.95 * len(ordered)) - 1] * 1000, 3)}

    return {"actors": count, "environment": "ASGI in-process; synthetic VNU subprocess/store/auth repository",
            "maximum_collector_concurrency": trace["maximum"], "logical_jobs": count,
            "collector_calls": trace["collector"], "save_calls": trace["save"],
            "requests": len(responses), "error_rate": sum(code >= 400 for code in responses) / len(responses),
            "metrics": {name: metrics(values) for name, values in timings.items()}}
