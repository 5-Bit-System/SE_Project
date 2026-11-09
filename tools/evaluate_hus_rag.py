"""Run the frozen reviewer candidate once on the standalone app, without tuning."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from tools.hus_rag_metrics import collect_predictions, score_cases, summarize
from tools.validate_hus_holdout import DEFAULT_PACK, ROOT, rows, validate_pack


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))


def write_rows(path, values):
    path.write_bytes("".join(json.dumps(v, ensure_ascii=False, sort_keys=True) + "\n" for v in values).encode("utf-8"))


def capture_response(response, calls):
    captured = {"http_status": response.status_code, "raw_response_text": response.text,
                "retrieval_calls": deepcopy(calls), "response_json_error": None}
    try:
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON response object")
        captured["response"] = payload
    except ValueError as exc:
        captured.update(response={}, response_json_error=f"{type(exc).__name__}: {str(exc)[:300]}")
    return captured


def verify_saved_run(run: Path):
    """Recompute scores from recorded observations; no runtime app or HTTP imported."""
    run = Path(run).resolve()
    manifest = json.loads((run / "manifest.json").read_bytes())
    for name, expected in manifest["files_sha256"].items():
        path = (run / name).resolve()
        if not path.is_relative_to(run) or digest(path) != expected:
            raise ValueError(f"Saved run hash mismatch: {name}")
    report = json.loads((run / "report.json").read_bytes())
    pack = ROOT / report["pack"]
    preflight = validate_pack(pack, ROOT)
    if preflight["pack_manifest_sha256"] != report["pack_manifest_sha256"]:
        raise ValueError("Saved run uses a different frozen candidate")
    predictions, audits = rows(run / "predictions.jsonl"), rows(run / "citation_audits.jsonl")
    if [p["question_id"] for p in predictions] != [a["question_id"] for a in audits]:
        raise ValueError("Prediction/audit join mismatch")
    observed = [{**p, "citation_integrity": a} for p, a in zip(predictions, audits, strict=True)]
    cases = score_cases(rows(pack / "questions.jsonl"), rows(pack / "gold.jsonl"),
                        rows(pack / "evidence.jsonl"), observed)
    if cases != rows(run / "scored_cases.jsonl") or summarize(cases) != report["metrics"]:
        raise ValueError("Saved score/report differs from recomputed metrics")
    for major, metrics in report["by_major"].items():
        if summarize([c for c in cases if c["major"] == major]) != metrics:
            raise ValueError("Saved per-major metrics differ")
    for category, metrics in report["by_category"].items():
        if summarize([c for c in cases if c["category"] == category]) != metrics:
            raise ValueError("Saved per-category metrics differ")
    return {"reproduced": True, "questions": len(cases), "new_rag_inference": False,
            "metrics": report["metrics"], "pack_manifest_sha256": preflight["pack_manifest_sha256"],
            "recorded_code_matches_current": {p: digest(ROOT / p) == h for p, h in report["evaluation_code_sha256"].items()}}


class TracedRetriever:
    """Observe the exact search made by the answerer; never alter its arguments/results."""

    def __init__(self, retriever):
        self.retriever = retriever
        self.calls = []

    def search(self, *args, **kwargs):
        hits = self.retriever.search(*args, **kwargs)
        self.calls.append({"query": args[0] if args else kwargs.get("query"),
                           "parameters": deepcopy(kwargs),
                           "hits": [{"chunk_id": h.chunk.chunk_id, "dataset": h.chunk.dataset,
                                     "major": h.chunk.major, "version": h.chunk.version,
                                     "course_code": h.chunk.metadata.get("course_code"),
                                     "field": h.chunk.metadata.get("field"), "score": h.score,
                                     "matched_terms": list(h.matched_terms)} for h in hits]})
        return hits


def audit_prediction(observation, oracle, client, binary_cache):
    """Reuse source/page ownership oracle; additionally fetch actual emitted local files."""
    answer = observation.get("response", {}).get("hus_answer") or {}
    request = observation["request"]
    codes = set(re.findall(r"\b[A-Z]{3}\d{4}[A-Z]?\b", request["question"].upper()))
    try:
        assert observation["http_status"] == 200 and answer, "HTTP/response failure"
        oracle.check(answer, request["major"], dataset=answer.get("dataset"),
                     version=request.get("version"), code=next(iter(codes)) if len(codes) == 1 else None,
                     expected=answer["status"])
        for citation in answer["citations"]:
            if citation["evidence_kind"] not in {"pdf", "file"}:
                continue
            url, expected = citation["open_url"], citation["document_sha256"]
            if url not in binary_cache:
                response = client.get(url.split("#")[0])
                assert response.status_code == 200, "source binary HTTP failure"
                assert hashlib.sha256(response.content).hexdigest() == expected, "source binary hash failure"
                if citation["evidence_kind"] == "pdf":
                    assert response.headers["content-type"].startswith("application/pdf")
                    assert response.content.startswith(b"%PDF-"), "not PDF bytes"
                else:
                    assert response.content.startswith(b"PK"), "not DOCX bytes"
                binary_cache[url] = {"sha256": expected, "bytes": len(response.content),
                                     "content_type": response.headers["content-type"]}
        return {"question_id": observation["question_id"], "passed": True, "error": None}
    except (AssertionError, KeyError, TypeError, ValueError, StopIteration) as exc:
        return {"question_id": observation["question_id"], "passed": False,
                "error": f"{type(exc).__name__}: {str(exc)[:500]}"}


def run_evaluation(pack: Path, out: Path):
    from fastapi.testclient import TestClient

    from app.hus.demo import app
    from app.services.hus_service import get_hus_answerer
    from tools.verify_hus_e2e import EvidenceOracle

    pack, out = Path(pack).resolve(), Path(out).resolve()
    preflight = validate_pack(pack, ROOT)
    if out.is_relative_to(pack) or out == pack:
        raise ValueError("Evaluation output must not modify the frozen candidate")
    if out.exists():
        raise ValueError("Output exists; choose a new run directory")
    if preflight["runtime_matches_baseline"] is not True:
        raise ValueError("Runtime differs from frozen P1-1 baseline; use a separately declared evaluation version")
    manifest = json.loads((pack / "manifest.json").read_bytes())
    answerer = get_hus_answerer()
    release_manifest = ROOT / manifest["source_release"] / "manifest.json"
    selected = json.loads(release_manifest.read_bytes())
    if answerer.data.release_identity["release_sha256"] != selected["release_sha256"]:
        raise ValueError("Runtime release differs from frozen evaluation source")
    out.mkdir(parents=True)
    start = datetime.now(timezone.utc).isoformat()
    source_before = {p: digest(ROOT / p) for p in manifest["source_inputs_sha256"]}
    pointer_before = digest(ROOT / "data/hus/rag/CURRENT.json")
    questions = rows(pack / "questions.jsonl")
    original = answerer.retriever
    traced = TracedRetriever(original)
    answerer.retriever = traced
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            def execute(request):
                traced.calls.clear()
                response = client.post("/hus/chat", json=request)
                return capture_response(response, traced.calls)
            predictions = collect_predictions(questions, execute)
    finally:
        answerer.retriever = original
    # Persist all observations before loading gold into the scorer.
    write_rows(out / "predictions.jsonl", predictions)
    gold, evidence = rows(pack / "gold.jsonl"), rows(pack / "evidence.jsonl")
    oracle, binary_cache = EvidenceOracle(), {}
    with TestClient(app, raise_server_exceptions=False) as client:
        audits = [audit_prediction(p, oracle, client, binary_cache) for p in predictions]
    write_rows(out / "citation_audits.jsonl", audits)
    observed = [{**prediction, "citation_integrity": audit}
                for prediction, audit in zip(predictions, audits, strict=True)]
    cases = score_cases(questions, gold, evidence, observed)
    write_rows(out / "scored_cases.jsonl", cases)
    metrics = summarize(cases)
    value = metrics["routed_recall_at_5"]["value"]
    frozen_after = validate_pack(pack, ROOT)
    assert frozen_after == preflight, "Frozen candidate/runtime changed during run"
    assert source_before == {p: digest(ROOT / p) for p in source_before}, "Source data changed during run"
    assert pointer_before == digest(ROOT / "data/hus/rag/CURRENT.json"), "CURRENT changed during run"
    code_paths = ["tools/evaluate_hus_rag.py", "tools/hus_rag_metrics.py", "tools/validate_hus_holdout.py",
                  "tools/verify_hus_e2e.py", "tests/hus/test_rag_evaluation.py"]
    report = {
        "schema_version": "1.0", "status": "provisional_candidate_measurement_not_independent_acceptance",
        "started_at_utc": start, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "pack": pack.relative_to(ROOT).as_posix(), "pack_manifest_sha256": preflight["pack_manifest_sha256"],
        "questions_sha256": preflight["questions_sha256"], "gold_sha256": preflight["gold_sha256"],
        "git_head_is_base_only": subprocess.check_output(
            ["git", "-c", "safe.directory=" + ROOT.as_posix(), "rev-parse", "HEAD"], text=True).strip(),
        "git_state": "uncommitted_worktree", "tested_commit": None,
        "release_identity": answerer.data.release_identity, "CURRENT_sha256": pointer_before,
        "baseline_runtime_sha256": manifest["baseline_runtime_sha256"],
        "evaluation_code_sha256": {p: digest(ROOT / p) for p in code_paths},
        "source_input_sha256": source_before,
        "human_accepted_questions": 0, "semantic_review": "pending",
        "holdout_inference_run": True, "used_for_retrieval_tuning": False,
        "split_access": "candidate evaluated and errors inspected; retire if later used for tuning",
        "P1_1_creation_flags_are_historical": True, "P1_2_accepted": False,
        "metrics": metrics,
        "by_major": {m: summarize([c for c in cases if c["major"] == m]) for m in sorted(manifest["by_major"])},
        "by_category": {k: summarize([c for c in cases if c["category"] == k]) for k in sorted(manifest["by_category"])},
        "top5_target": {"minimum": 0.9, "provisionally_met": value >= 0.9 if value is not None else None,
                        "independently_accepted": False},
        "source_binary_checks": binary_cache,
        "definitions": {
            "routed_recall_at_5": "Macro anchor recall on all20 F1/F3 positives using first actual retriever call top5; no call/hit is zero. Includes routing failures. Gold never supplied to runtime.",
            "f2_lookup_success": "Correct source-backed facts on all12 F2 positives; not Recall@5.",
            "source_supported_success_on_positive": "Conservative draft-anchor support on all32 positives; requires answered/correct family/scope, source oracle, matching anchor and F2 facts. Not semantic certification.",
            "citation_anchor_precision_lower_bound": "Anchored, source-oracle-valid, scope-correct citations divided by all emitted citations. F2 facts must match. Oracle is answer-level, so integrity failure rejects all citations conservatively. Alternative sources need human review.",
            "citation_integrity_answer_pass_rate": "Whole-answer independent quote/page/row/review/AI checks plus actual local binary GET/hash; denominator is answers that emitted citations. Does not assess relevance/semantic entailment or external website health.",
            "guardrail_success": "Exact expected refusal/clarification with no citations/facts on all16 guard cases.",
            "semantic_metrics": "Citation precision and source support by human semantic judgment remain null; AI draft gold is not independent human review.",
            "timing": "No latency or load benchmark claimed; TestClient is in-process HTTP, not browser acceptance.",
        },
        "product_database_modified": False, "vnu_contacted": False, "llm_used": False,
        "production_activated": False, "committed": False, "pushed": False,
    }
    write_json(out / "report.json", report)
    files = {p.name: digest(p) for p in out.iterdir() if p.is_file()}
    write_json(out / "manifest.json", {"schema_version": "1.0", "files_sha256": files,
                                        "pack_manifest_sha256": preflight["pack_manifest_sha256"]})
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--out", type=Path, help="New run directory; refuses overwrite")
    parser.add_argument("--verify-run", type=Path, help="Verify cached observations/scores without new inference")
    args = parser.parse_args(argv)
    try:
        if args.verify_run:
            if args.out:
                parser.error("--verify-run does not write a new --out")
            print(json.dumps(verify_saved_run(args.verify_run), ensure_ascii=False, indent=2))
            return 0
        if args.out is None:
            parser.error("--out is required for a new inference run")
        report = run_evaluation(args.pack, args.out)
    except (OSError, ValueError, AssertionError) as exc:
        print(f"Evaluation failed: {exc}")
        return 1
    print(json.dumps({"out": str(args.out), "status": report["status"],
                      "metrics": report["metrics"], "target": report["top5_target"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
