"""Run isolated loopback RAG workers, monitor HTTP, activate and roll back locally."""

from __future__ import annotations

import argparse
import importlib.abc
import json
import socket
import subprocess
import sys
import time
import uuid
from collections import Counter, defaultdict, deque
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path

from starlette.requests import Request

from tools.hus_ops_state import (
    atomic_write,
    digest,
    encoded,
    loopback_url,
    require,
    rollback,
    transition,
    verify_files,
)

ROOT = Path(__file__).resolve().parents[1]
BANNED_IMPORTS = ("app.hus.crawler", "app.advisor", "app.api", "app.recommendation", "app.rules",
                  "app.catalog", "app.profiles", "app.auth", "app.integrations", "app.services.advisor_service")


def route_name(path):
    if path == "/hus/chat":
        return "chat"
    if path.startswith("/hus/sources/"):
        return "source"
    if path.startswith("/ops/"):
        return "operations"
    if path == "/hus/config":
        return "config"
    if path == "/" or path.startswith("/static/"):
        return "ui"
    return "other"


class Observations:
    def __init__(self, instance, build, event_path):
        self.instance, self.build, self.event_path = instance, build, event_path
        self.counts, self.durations = Counter(), defaultdict(lambda: deque(maxlen=512))

    def record(self, method, path, status, elapsed, request_id):
        route = route_name(path)
        method = method if method in {"GET", "POST", "HEAD"} else "other"
        event = {"recorded_at": datetime.now(timezone.utc).isoformat(), "instance": self.instance,
                 "request_id": request_id, "method": method, "route": route,
                 "http_status": status, "duration_ms": round(elapsed * 1000, 3),
                 "build_sha256": self.build["build_sha256"],
                 "release_sha256": self.build["release_sha256"]}
        self.counts[route, str(status)] += 1
        self.durations[route].append(event["duration_ms"])
        with self.event_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, sort_keys=True) + "\n")

    def metrics(self):
        latency = {}
        for route, samples in self.durations.items():
            values = sorted(samples)
            latency[route] = {"window_samples": len(values), "p50_ms": values[(len(values) - 1) // 2],
                              "p95_ms": values[max(0, (95 * len(values) + 99) // 100 - 1)]}
        service = [(route, status, count) for (route, status), count in self.counts.items() if route != "operations"]
        requests = sum(count for _, _, count in service)
        errors = sum(count for _, status, count in service if int(status) >= 500)
        return {"instance": self.instance, **self.build,
                "http_counts": {route + ":" + status: count for (route, status), count in sorted(self.counts.items())},
                "service_requests": requests, "service_5xx": errors,
                "service_5xx_ratio": errors / requests if requests else None,
                "latency": latency, "latency_window_limit": 512,
                "duration_measurement": "middleware time to response headers; excludes streamed body transfer",
                "prompt_or_response_text_logged": False}


def reject_external_network_and_product_imports():
    class RejectProduct(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if any(fullname == prefix or fullname.startswith(prefix + ".") for prefix in BANNED_IMPORTS):
                raise ImportError("operational rehearsal forbids product/crawler import: " + fullname)
    sys.meta_path.insert(0, RejectProduct())

    def audit(event, args):
        if event == "socket.connect":
            address = args[1]
            if isinstance(address, tuple) and address[0] not in {"127.0.0.1", "::1"}:
                raise PermissionError("operational rehearsal forbids external connections")
        if event == "socket.getaddrinfo" and args[0] not in {"127.0.0.1", "::1", "localhost", None}:
            raise PermissionError("operational rehearsal forbids external DNS")
    sys.addaudithook(audit)


def worker_app(root, instance, events):
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    from app.hus.demo import app as demo
    from app.services.hus_service import get_hus_answerer

    build = json.loads((root / "build_manifest.json").read_bytes())
    require(build["build_sha256"] == digest(encoded(build["files_sha256"])), "build manifest identity differs")
    verify_files(root, build["files_sha256"])
    answerer = get_hus_answerer()
    require(answerer.data.release_identity["release_sha256"] == build["release_sha256"], "worker release differs")
    require(not answerer.citation_resolver.assets.problem, "citation registry unavailable")
    observation = Observations(instance, {k: build[k] for k in
                              ["build_sha256", "release_id", "release_sha256", "registry_sha256"]}, events)
    healthy = {"ready": True}
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def observe(request: Request, call_next):
        start, request_id = time.monotonic(), uuid.uuid4().hex
        if not request.client or request.client.host not in {"127.0.0.1", "::1"}:
            return JSONResponse({"detail": "loopback rehearsal only"}, status_code=403)
        try:
            if not healthy["ready"] and not request.url.path.startswith("/ops/"):
                response = JSONResponse({"detail": "RAG worker is not ready"}, status_code=503)
            else:
                response = await call_next(request)
        except Exception:
            response = JSONResponse({"detail": "RAG worker failed"}, status_code=500)
        response.headers.update({"X-HUS-Instance": instance, "X-HUS-Build": build["build_sha256"],
                                 "X-HUS-Release": build["release_sha256"], "X-HUS-Request-ID": request_id,
                                 "Cache-Control": "no-store"})
        observation.record(request.method, request.url.path, response.status_code, time.monotonic() - start, request_id)
        return response

    @app.get("/ops/live")
    def live():
        return {"live": True, "instance": instance}

    @app.get("/ops/ready")
    def ready():
        try:
            verify_files(root, build["files_sha256"])
            healthy["ready"] = True
        except (ValueError, OSError):
            healthy["ready"] = False
        return JSONResponse({"ready": healthy["ready"], "instance": instance, **observation.build,
                             "scope": "local_operational_rehearsal", "production_eligible": False},
                            status_code=200 if healthy["ready"] else 503)

    @app.get("/ops/metrics")
    def metrics():
        return observation.metrics()

    app.mount("/", demo)
    return app


def gateway_app(pointer, event_path):
    import httpx
    from fastapi import FastAPI
    from fastapi.responses import Response

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.api_route("/{path:path}", methods=["GET", "HEAD", "POST"])
    async def forward(request: Request, path: str):
        if not request.client or request.client.host not in {"127.0.0.1", "::1"}:
            return Response(status_code=403)
        selected = None
        start = time.monotonic()
        try:
            # Capture once for the whole request; a transition cannot rebind it.
            selected_raw = pointer.read_bytes()
            selected = json.loads(selected_raw)
            require(selected.get("scope") == "local_operational_rehearsal", "not a rehearsal selector")
            base = loopback_url(selected["worker"]["base_url"])
            async with httpx.AsyncClient(timeout=10, trust_env=False, follow_redirects=False) as client:
                upstream = await client.request(request.method, base + "/" + path,
                                                params=request.query_params, content=await request.body(),
                                                headers={name: request.headers[name] for name in
                                                         ["content-type", "range", "if-range"] if name in request.headers})
            headers = {name: value for name, value in upstream.headers.items()
                       if name.lower() not in {"transfer-encoding", "connection", "content-encoding"}}
            headers["X-HUS-Selection"] = digest(selected_raw)
            response = Response(upstream.content, status_code=upstream.status_code, headers=headers)
        except (ValueError, OSError, KeyError, httpx.HTTPError):
            response = Response(encoded({"detail": "Selected RAG worker is unavailable"}),
                                status_code=503, media_type="application/json")
        with event_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"route": route_name(request.url.path), "http_status": response.status_code,
                                     "instance": (selected or {}).get("worker", {}).get("instance"),
                                     "duration_ms": round((time.monotonic() - start) * 1000, 3)}) + "\n")
        return response
    return app


def serve(app, status_path):
    import uvicorn

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    base = f"http://127.0.0.1:{sock.getsockname()[1]}"
    atomic_write(status_path, encoded({"base_url": base}))
    try:
        uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", log_level="error", access_log=False)).run(sockets=[sock])
    finally:
        sock.close()


def bundle(out):
    pointer = json.loads((ROOT / "data/hus/rag/CURRENT.json").read_bytes())
    release = (ROOT / "data/hus/rag" / pointer["release_path"]).resolve()
    require(release.is_relative_to(ROOT / "data/hus/rag/releases"), "release outside canonical root")
    manifest = json.loads((release / "manifest.json").read_bytes())
    registry = ROOT / "data/hus/citation_assets/registry.json"
    files = set((ROOT / "app/hus").rglob("*.py"))
    files.update(ROOT / p for p in ["app/__init__.py", "app/services/__init__.py", "app/services/hus_service.py",
                                  "app/schemas/__init__.py", "app/schemas/hus.py", "tools/hus_ops_state.py",
                                  "tools/rehearse_hus_operations.py", "requirements-lock.txt", "requirements-dev.txt",
                                  "app/static/hus-rag-demo.html", "app/static/hus-rag-demo.css", "app/static/hus-rag-demo.js",
                                  "data/hus/rag/CURRENT.json"] if (ROOT / p).is_file())
    files.add(release / "manifest.json")
    files.update(release / p for p in manifest["files"])
    files.add(registry)
    for sha, asset in json.loads(registry.read_bytes())["assets"].items():
        path = (registry.parent / asset["path"]).resolve()
        require(path.is_relative_to(registry.parent), "asset path escape")
        require(digest(path.read_bytes()) == sha, "citation binary hash mismatch")
        files.add(path)
    pins = {}
    for path in sorted(files):
        require(path.resolve().is_relative_to(ROOT), "bundle source outside checkout")
        relative = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        pins[relative] = digest(raw)
    build = {"build_sha256": digest(encoded(pins)), "files_sha256": pins,
             "release_id": pointer["release_id"], "release_sha256": pointer["release_sha256"],
             "registry_sha256": digest(registry.read_bytes()), "scope": "local_operational_rehearsal"}
    atomic_write(out / "build_manifest.json", encoded(build))
    return build


def start_child(stack, root, role, instance=None, pointer=None, state_root=None):
    import httpx

    state = state_root or root / "backups/operations"
    state.mkdir(parents=True)
    command = [sys.executable, "-X", "utf8", "-u", "-m", "tools.rehearse_hus_operations",
               "--role", role, "--state", str(state)]
    if instance:
        command.extend(["--instance", instance])
    if pointer:
        command.extend(["--pointer", str(pointer)])
    log = stack.enter_context((state / "process.log").open("wb"))
    process = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    def stop():
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    stack.callback(stop)
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        require(process.poll() is None, "child failed; inspect its process.log")
        if (state / "status.json").exists():
            base = loopback_url(json.loads((state / "status.json").read_bytes())["base_url"])
            try:
                with httpx.Client(timeout=1, trust_env=False) as client:
                    response = client.get(base + ("/ops/live" if role == "worker" else "/hus/config"))
                if response.status_code == 200:
                    return process, base, state
            except httpx.HTTPError:
                pass
        time.sleep(.1)
    raise TimeoutError("loopback child did not become live")


def run(out):
    import httpx

    out = Path(out).resolve()
    require(out.is_relative_to(ROOT / "backups") and out != ROOT / "backups" and not out.exists(),
            "use a new dedicated directory under backups")
    out.mkdir(parents=True)
    before = {}
    builds = {}
    for instance in ["blue", "green"]:
        builds[instance] = bundle(out / instance)
        before.update(builds[instance]["files_sha256"])
    atomic_write(out / "events.jsonl", b"")
    cases = []
    samples = []
    transitions = []

    def record(name, result=True):
        require(result, "rehearsal failed: " + name)
        cases.append({"name": name, "status": "pass"})

    with ExitStack() as stack, httpx.Client(timeout=20, trust_env=False, follow_redirects=False) as client:
        workers = {}
        processes = {}
        for name in ["blue", "green"]:
            process, base, state = start_child(stack, out / name, "worker", name)
            processes[name] = process
            value = client.get(base + "/ops/ready")
            record(name + "_ready", value.status_code == 200 and value.json()["ready"])
            workers[name] = {"base_url": base, "instance": name, **{key: builds[name][key] for key in
                             ["build_sha256", "release_id", "release_sha256", "registry_sha256"]}}

        def probe(base):
            value = client.get(loopback_url(base) + "/ops/ready")
            samples.append({"instance": value.json().get("instance"), "status": value.status_code, "ready": value.json().get("ready")})
            return value.json()

        traffic = out / "traffic"
        traffic.mkdir()
        (traffic / "LOCAL_REHEARSAL_ONLY").write_bytes(b"loopback-only\n")
        pointer = traffic / "ACTIVE_WORKER.json"
        atomic_write(pointer, encoded({"scope": "local_operational_rehearsal", "worker": workers["blue"]}))
        old = digest(pointer.read_bytes())
        _, gateway, gateway_state = start_child(stack, ROOT, "gateway", pointer=pointer,
                                                state_root=out / "gateway/backups/operations")
        receipts = {name: {"scope": "local_operational_rehearsal", "production_eligible": False,
                           "status": "pass", "worker": worker} for name, worker in workers.items()}
        for name, receipt in receipts.items():
            atomic_write(out / f"{name}_receipt.json", encoded(receipt))

        def ask(question, major="data_science", version="QD3569-2023", generated=False):
            result = client.post(gateway + "/hus/chat", json={"question": question, "major": major,
                                 "version": version, "allow_generated_reference": generated})
            record("chat_http_200", result.status_code == 200)
            return result, result.json()

        answer, value = ask("Xin chào")
        record("basic_chat", value["mode"] == "basic_chat" and answer.headers["x-hus-instance"] == "blue")
        _, value = ask("Giới thiệu ngành")
        record("F1_with_source", value["hus_answer"]["status"] == "answered" and bool(value["hus_answer"]["citations"]))
        response, value = ask("Tín chỉ MAT3533?")
        record("F2_fact", value["hus_answer"]["facts"]["value"] == 3)
        citation = value["hus_answer"]["citations"][0]
        binary = client.get(gateway + citation["open_url"].split("#")[0])
        record("PDF_binary_hash", binary.status_code == 200 and digest(binary.content) == citation["document_sha256"])
        ranged = client.get(gateway + citation["open_url"].split("#")[0], headers={"Range": "bytes=0-15"})
        record("PDF_range", ranged.status_code == 206 and ranged.content.startswith(b"%PDF-") and len(ranged.content) == 16)
        _, value = ask("Nội dung MAT3533?")
        record("F3_opt_in_required", value["hus_answer"]["status"] == "needs_clarification" and not value["hus_answer"]["citations"])
        _, value = ask("Nội dung MAT3533?", generated=True)
        record("F3_AI_label_null_link", value["hus_answer"]["status"] == "answered" and all(
            c["display_label"] == "kiến thức AI" and c["open_url"] is None for c in value["hus_answer"]["citations"]))
        _, value = ask("MAT3533 thi cuối kỳ bao nhiêu phần trăm?")
        record("missing_assessment_abstains", value["hus_answer"]["status"] == "no_information" and not value["hus_answer"]["facts"])
        _, value = ask("Tiên quyết MAT3325?", "mathematics", "QD3565-2023")
        locators = value["hus_answer"]["citations"]
        record("same_PDF_distinct_pages", [c["pdf_page"] for c in locators] == [13, 12])
        for source in locators:
            data = client.get(gateway + source["open_url"].split("#")[0])
            record("PDF_page_" + str(source["pdf_page"]), data.status_code == 200 and digest(data.content) == source["document_sha256"])
        record("invalid_input_422", client.post(gateway + "/hus/chat", json={"question": "x"}).status_code == 422)
        record("unknown_source_404", client.get(gateway + "/hus/sources/invalid").status_code == 404)

        # A changed candidate cannot receive traffic or certify readiness.
        damaged = out / "green/data/hus/rag/CURRENT.json"
        original = damaged.read_bytes()
        damaged.write_bytes(original + b" ")
        record("corrupt_candidate_unready", client.get(workers["green"]["base_url"] + "/ops/ready").status_code == 503)
        try:
            transition(pointer, workers["green"], receipts["green"], old, probe)
        except ValueError:
            record("corrupt_candidate_rejected", digest(pointer.read_bytes()) == old)
        else:
            raise AssertionError("corrupt candidate activated")
        damaged.write_bytes(original)
        record("candidate_restored", probe(workers["green"]["base_url"])["ready"])
        try:
            transition(pointer, workers["green"], receipts["green"], "0" * 64, probe)
        except ValueError:
            record("stale_activation_rejected", digest(pointer.read_bytes()) == old)
        else:
            raise AssertionError("stale activation passed")
        active = transition(pointer, workers["green"], receipts["green"], old, probe)
        transitions.append(active)
        response, value = ask("Tín chỉ MAT3533?")
        record("green_serves_after_switch", response.headers["x-hus-instance"] == "green"
               and response.headers["x-hus-selection"] == active["selector_sha256"] and value["hus_answer"]["facts"]["value"] == 3)
        for name, worker in workers.items():
            snapshot = client.get(worker["base_url"] + "/ops/metrics").json()
            atomic_write(out / f"{name}_metrics.json", encoded(snapshot))
        processes["green"].terminate()
        processes["green"].wait(timeout=8)
        outage = client.post(gateway + "/hus/chat", json={"question": "Xin chào", "major": "data_science"})
        record("active_outage_503", outage.status_code == 503)
        samples.append({"instance": "green", "status": 503, "ready": False, "cause": "process_stopped"})
        transitions.append(rollback(pointer, old, active["selector_sha256"], probe))
        response, _ = ask("Tín chỉ MAT3533?")
        record("rollback_blue_serves", response.headers["x-hus-instance"] == "blue" and digest(pointer.read_bytes()) == old)
        record("rollback_restored_bytes", pointer.read_bytes() == (traffic / "history" / f"{old}.json").read_bytes())
        atomic_write(out / "blue_final_metrics.json", encoded(client.get(workers["blue"]["base_url"] + "/ops/metrics").json()))
        for name in ["blue", "green"]:
            verify_files(out / name, builds[name]["files_sha256"])
        atomic_write(out / "gateway_events.jsonl", (gateway_state / "events.jsonl").read_bytes())
        for name in ["blue", "green"]:
            atomic_write(out / f"{name}_events.jsonl", (out / name / "backups/operations/events.jsonl").read_bytes())
        record("no_product_imports", not any(name == p or name.startswith(p + ".")
               for name in sys.modules for p in BANNED_IMPORTS))
    verify_files(ROOT, before)
    record("source_code_and_data_unchanged")
    summary = {"scope": "local_operational_rehearsal", "status": "pass", "production_eligible": False,
               "production_activated": False, "actual_production_monitoring": False,
               "same_release_process_switch_only": True, "cases": cases, "monitor_samples": samples,
               "transitions": transitions, "builds": {name: {k: v for k, v in build.items() if k != "files_sha256"}
                                                        for name, build in builds.items()},
               "source_input_files_unchanged": len(before), "prompt_or_response_text_logged": False,
               "crawler_or_external_network_permitted_in_children": False,
               "RAG_quality_acceptance": False, "review_state_changed": False,
               "all_child_processes_stopped": True, "committed": False, "pushed": False}
    atomic_write(out / "report.json", encoded(summary))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--role", choices=["worker", "gateway"])
    parser.add_argument("--state", type=Path)
    parser.add_argument("--instance")
    parser.add_argument("--pointer", type=Path)
    args = parser.parse_args()
    if args.role:
        require(args.state is not None and args.state.resolve().is_relative_to(ROOT / "backups"),
                "child state must stay under its workspace backups")
        reject_external_network_and_product_imports()
        if args.role == "worker":
            app = worker_app(ROOT, args.instance, args.state / "events.jsonl")
        else:
            app = gateway_app(args.pointer, args.state / "events.jsonl")
        serve(app, args.state / "status.json")
    else:
        require(args.out is not None, "--out is required")
        report = run(args.out)
        print(json.dumps({"status": report["status"], "cases": len(report["cases"]),
                          "production_activated": False, "report": str(args.out / "report.json")}))


if __name__ == "__main__":
    main()
