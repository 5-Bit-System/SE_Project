"""100 concurrent workers over actual loopback HTTP with a fresh synthetic-only server."""

import argparse
import asyncio
import csv
import json
import math
import os
import platform
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import httpx

from tools.bt3.http_fixture import CASES, PROGRAM, check_response, write_fixture
from tools.bt3.run_evidence import EVIDENCE, ROOT, git


@contextmanager
def synthetic_server(thread_tokens: int = 0):
    """Identify our server with a per-run marker and stop our complete child process tree."""
    with tempfile.TemporaryDirectory(prefix="bt3-synthetic-") as temporary:
        directory = Path(temporary)
        data = directory / "catalogs"
        write_fixture(data)
        with socket.socket() as reserved:
            reserved.bind(("127.0.0.1", 0))
            port = reserved.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        run_id = uuid.uuid4().hex  # Lifecycle identity only; fixture/query data remain deterministic.
        essentials = {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "COMSPEC", "PATHEXT"}
        env = {key: value for key, value in os.environ.items() if key.upper() in essentials}
        env.update(STORAGE_BACKEND="json", DATABASE_MODEL="hus", DATABASE_URL="",
                   APP_ENV="test", EMAIL_BACKEND="fake", GEMINI_API_KEY="",
                   RECOMMENDATION_LLM_ENABLED="false", PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                   AUTH_TOKEN_PEPPER="synthetic-bt3-no-real-credentials-000000000000",
                   PUBLIC_BASE_URL=base, AUTH_ALLOWED_ORIGINS=base)
        with (directory / "server.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                [sys.executable, "-m", "tools.bt3.fixture_server", "--data", str(data),
                 "--port", str(port), "--run-id", run_id, "--thread-tokens", str(thread_tokens)],
                cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
            try:
                deadline = time.monotonic() + 30
                last_probe = "not attempted"
                with httpx.Client(trust_env=False, timeout=1) as probe:
                    while True:
                        if process.poll() is not None:
                            raise RuntimeError("Synthetic server exited: " +
                                               (directory / "server.log").read_text(encoding="utf-8"))
                        try:
                            response = probe.get(base + "/bt3-test-marker")
                            last_probe = f"HTTP {response.status_code}"
                            if response.status_code == 200 and response.json().get("kind") == "bt3-synthetic-only":
                                last_probe = f"test marker PID={response.json().get('pid')}; launcher PID={process.pid}"
                            if (response.status_code == 200
                                    and response.json().get("kind") == "bt3-synthetic-only"
                                    and response.json().get("run_id") == run_id):
                                break
                        except httpx.TransportError as exc:
                            last_probe = f"{type(exc).__name__}: {exc}"
                        if time.monotonic() >= deadline:
                            raise TimeoutError("Synthetic server not ready within 30 seconds; " + last_probe)
                        # Bounded polling of observable readiness, never a fixed ready-after-sleep assumption.
                        time.sleep(0.02)
                yield base
            finally:
                if process.poll() is None:
                    try:
                        with httpx.Client(trust_env=False, timeout=2) as control:
                            control.post(base + "/bt3-test-shutdown", params={"run_id": run_id})
                        process.wait(timeout=10)
                    except (httpx.TransportError, subprocess.TimeoutExpired):
                        if os.name == "nt":
                            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                           capture_output=True, check=True)
                        else:
                            process.terminate()
                        process.wait(timeout=5)


def request_args(case: int):
    params = CASES[case][0]
    return ("/courses" if params is None else "/courses/search",
            {"program_id": PROGRAM, **(params or {})})


async def measure(base: str, run: int):
    gate, ready = asyncio.Event(), asyncio.Queue()
    in_flight = peak = 0
    measurements = []
    limits = httpx.Limits(max_connections=100, max_keepalive_connections=100)
    async with httpx.AsyncClient(base_url=base, limits=limits, timeout=15, trust_env=False) as client:
        thread_tokens = (await client.get("/bt3-test-marker")).json()["thread_tokens"]
        # Warm-up uses the identical mix but is deliberately excluded from recorded latencies.
        for index in range(50):
            case = index % len(CASES)
            path, params = request_args(case)
            check_response(await client.get(path, params=params), case)

        async def worker(identity: int):
            nonlocal in_flight, peak
            ready.put_nowait(identity)
            await gate.wait()
            for iteration in range(20):
                case = (identity + iteration) % len(CASES)
                path, params = request_args(case)
                start = time.perf_counter()
                status, error = None, ""
                in_flight += 1
                peak = max(peak, in_flight)
                try:
                    response = await client.get(path, params=params)
                    status = response.status_code
                    check_response(response, case)
                except Exception as exc:
                    error = f"{type(exc).__name__}: {str(exc)[:160]}"
                finally:
                    in_flight -= 1
                elapsed = (time.perf_counter() - start) * 1000
                measurements.append(dict(run=run, worker=identity, iteration=iteration,
                                         case=case, status=status, ok=not error,
                                         latency_ms=round(elapsed, 6), error=error))

        tasks = [asyncio.create_task(worker(index)) for index in range(100)]
        for _ in range(100):
            await ready.get()
        start = time.perf_counter()
        gate.set()  # Exactly 100 workers are waiting here; not 100 sequential requests.
        await asyncio.gather(*tasks)
        duration = time.perf_counter() - start
    latencies = sorted(row["latency_ms"] for row in measurements)

    def percentile(p):
        return latencies[math.ceil(p * len(latencies)) - 1]

    errors = sum(not row["ok"] for row in measurements)
    summary = dict(run=run, workers=100, requests=len(measurements), warmup_requests=50,
                   server_thread_tokens=thread_tokens,
                   peak_in_flight=peak, duration_seconds=round(duration, 4),
                   success_count=len(measurements) - errors, error_count=errors,
                   p50_ms=percentile(.50), p95_ms=percentile(.95), max_ms=max(latencies),
                   passed=errors == 0 and peak == 100 and percentile(.95) <= 3000)
    return summary, measurements


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="performance")
    parser.add_argument("--thread-tokens", type=int, default=0,
                        help="0 keeps default; explicit value changes only the isolated test server")
    args = parser.parse_args()
    if Path(args.label).name != args.label:
        parser.error("Simple evidence label required")
    if not 0 <= args.thread_tokens <= 100:
        parser.error("Thread tokens must be 0 (default) or 1..100")
    summaries, rows = [], []
    for run in (1, 2, 3):
        with synthetic_server(args.thread_tokens) as base:
            summary, measured = asyncio.run(measure(base, run))
            summaries.append(summary)
            rows.extend(measured)
            print(json.dumps(summary), flush=True)
    record = dict(
        recorded_utc=datetime.now(timezone.utc).isoformat(), head=git("rev-parse", "HEAD"),
        branch=git("branch", "--show-current"), working_tree=git("status", "--porcelain=v1"),
        platform=platform.platform(), machine=platform.machine(), processor=platform.processor(),
        logical_cpus=os.cpu_count(), python=platform.python_version(),
        packages={name: version(name) for name in ("fastapi", "uvicorn", "httpx", "pydantic")},
        configuration=f"1 Uvicorn process; AnyIO thread tokens={args.thread_tokens or 'default'}; client separate process; loopback HTTP",
        fixture="240 courses in measured program + 3 single-course catalogs; invented; no DB or VNU",
        cache="No application result cache; JSON read/validated per request; warm OS file cache",
        percentile="nearest rank: sorted latency[ceil(p*n)-1]; milliseconds; full client body decode and contract checks included",
        design="3 fresh servers, each 50 warm-up then 100 workers x 20 requests; Event gate; 100 connection limit",
        runs=summaries, total_measured_requests=len(rows), passed=all(run["passed"] for run in summaries))
    (EVIDENCE / f"{args.label}-results.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (EVIDENCE / f"{args.label}-requests.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
