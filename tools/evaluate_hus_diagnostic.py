"""Measure exposed diagnostic/dev cases on the standalone app; never a holdout run."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from tools.evaluate_hus_rag import (
    TracedRetriever,
    audit_prediction,
    capture_response,
    digest,
    write_json,
    write_rows,
)
from tools.hus_rag_metrics import collect_predictions, score_cases, summarize
from tools.validate_hus_diagnostic import DEFAULT_PACK, ROOT, validate_pack
from tools.validate_hus_holdout import rows


def prepare_output(pack: Path, out: Path):
    """Reserve a fresh output directory outside frozen data/runtime trees."""
    pack, out = Path(pack).resolve(), Path(out).resolve()
    if out.exists():
        raise ValueError("Output exists; choose a new run directory")
    protected = [pack, ROOT / "data/hus/rag", ROOT / "data/hus/evaluation/p11_holdout_v1",
                 ROOT / "data/hus/evaluation/holdout_v2_candidate", ROOT / "data/hus/evaluation/holdout_v2_review",
                 ROOT / "data/hus/evaluation/runs/p12_baseline_v1", ROOT / "data/hus/evaluation/decisions/p2_v1"]
    if any(out.is_relative_to(path.resolve()) for path in protected):
        raise ValueError("Output must not modify a frozen pack, baseline or runtime data")
    out.mkdir(parents=True)


def collect_run(questions, out: Path, execute):
    """Persist every observation before the caller loads any scoring targets."""
    predictions = collect_predictions(questions, execute)
    write_rows(Path(out) / "predictions.jsonl", predictions)
    return predictions


def observe_route(question, classify):
    """Observe the classifier independently of gold and downstream scope guards."""
    dataset, field = classify(question)
    return {"dataset": dataset, "field": field,
            "stage": "classifier_before_scope_and_evidence_guards"}


def audit_development_prediction(observation, target, evidence_by_id, oracle, client, binary_cache):
    """Bind name-only F2 auditing to its pinned record after prediction collection.

    The legacy oracle needs a course code, while the request can contain only a
    name. Gold is used only for this offline audit, never to resolve the request.
    """
    if target["category"] != "f2":
        return audit_prediction(observation, oracle, client, binary_cache)
    refs = [evidence_by_id[eid]["source_ref"] for eid in target["evidence_ids"]]
    codes = {ref["identity"].rsplit(":", 1)[-1] for ref in refs if ref["identity_field"] == "record_id"}
    if len(codes) != 1 or not all(re.fullmatch(r"[A-Z]{3}\d{4}[A-Z]?", code) for code in codes):
        return {"question_id": observation["question_id"], "passed": False, "error": "Invalid pinned F2 course code"}
    expected_code = next(iter(codes))

    class BoundOracle:
        def check(self, answer, major, **kwargs):
            if answer.get("status") == "answered" and answer.get("dataset") == "f2":
                assert answer.get("facts", {}).get("course_code") == expected_code, "F2 answer code differs from source anchor"
                assert kwargs.get("code") in {None, expected_code}, "F2 query code differs from source anchor"
                kwargs["code"] = expected_code
            return oracle.check(answer, major, **kwargs)

    return audit_prediction(observation, BoundOracle(), client, binary_cache)


def development_summary(cases):
    metrics = summarize(cases)
    # The shared legacy metric has a historical denominator in its key. Dev has
    # 24 missing/out-of-scope cases, so use a count-neutral label here.
    metrics["abstention_on_missing_or_out_of_scope"] = metrics.pop("abstention_on_12_missing_or_out_of_scope")
    return metrics


def build_scores(questions, gold, evidence, predictions, audits):
    ids = [q["question_id"] for q in questions]
    if [audit["question_id"] for audit in audits] != ids:
        raise ValueError("Prediction/audit IDs must join every question in order")
    if len(predictions) != len(audits):
        raise ValueError("Prediction/audit count mismatch")
    observed = [{**prediction, "citation_integrity": audit}
                for prediction, audit in zip(predictions, audits, strict=True)]
    cases = score_cases(questions, gold, evidence, observed)
    return cases, development_summary(cases)


def runtime_hashes():
    paths = sorted((ROOT / "app/hus").glob("*.py"))
    paths.extend(ROOT / name for name in ["app/schemas/hus.py", "app/services/hus_service.py"])
    return {path.relative_to(ROOT).as_posix(): digest(path) for path in paths}


def evaluation_hashes():
    names = ["tools/evaluate_hus_diagnostic.py", "tools/evaluate_hus_rag.py", "tools/hus_rag_metrics.py",
             "tools/validate_hus_diagnostic.py", "tools/validate_hus_holdout.py", "tools/verify_hus_e2e.py",
             "tools/hus_rag_layer_metrics.py"]
    return {name: digest(ROOT / name) for name in names}


def artifact_hashes():
    """Pin the selected release, binaries, UI and dependencies without activation."""
    data_root = ROOT / "data/hus/rag"
    selector = json.loads((data_root / "CURRENT.json").read_bytes())
    release = (data_root / selector["release_path"]).resolve()
    if not release.is_relative_to(data_root.resolve()):
        raise ValueError("Selected release escapes data root")
    paths = set((ROOT / "app/hus").rglob("*.py"))
    paths.update((ROOT / "app/static").glob("hus-rag-demo.*"))
    paths.update(path for path in release.rglob("*") if path.is_file())
    paths.update(path for path in (ROOT / "data/hus/citation_assets").rglob("*") if path.is_file())
    paths.update(ROOT / name for name in ["app/schemas/hus.py", "app/services/hus_service.py",
                                        "requirements.txt", "requirements-dev.txt", "requirements-lock.txt",
                                        "data/hus/rag/CURRENT.json"])
    return {path.relative_to(ROOT).as_posix(): digest(path) for path in sorted(paths)}


def environment_snapshot():
    return {"python": sys.version, "executable": sys.executable,
            "distributions": [list(item) for item in sorted({(d.metadata["Name"], d.version)
                                                             for d in importlib.metadata.distributions()})]}


def build_layers(questions, gold, evidence, predictions, audits):
    from tools.hus_rag_layer_metrics import layer_metrics

    observed = [{**p, "citation_integrity": audit}
                for p, audit in zip(predictions, audits, strict=True)]
    return layer_metrics(questions, gold, evidence, observed)


def run_evaluation(pack: Path, out: Path):
    pack, out = Path(pack).resolve(), Path(out).resolve()
    preflight = validate_pack(pack, ROOT)
    prepare_output(pack, out)
    started = datetime.now(timezone.utc).isoformat()
    code_before, evaluator_before = runtime_hashes(), evaluation_hashes()
    artifacts_before, environment_before = artifact_hashes(), environment_snapshot()
    pointer_before = digest(ROOT / "data/hus/rag/CURRENT.json")
    manifest = json.loads((pack / "manifest.json").read_bytes())
    parent = ROOT / manifest["source_pack"]
    parent_manifest = json.loads((parent / "manifest.json").read_bytes())
    source_before = {path: digest(ROOT / path) for path in parent_manifest["source_inputs_sha256"]}

    from fastapi.testclient import TestClient

    from app.hus.demo import app
    from app.hus.question_routing import question_intent
    from app.services.hus_service import get_hus_answerer
    from tools.verify_hus_e2e import EvidenceOracle

    answerer = get_hus_answerer()
    source_release = ROOT / parent_manifest["source_release"]
    selected = json.loads((source_release / "manifest.json").read_bytes())
    if answerer.data.release_identity["release_sha256"] != selected["release_sha256"]:
        raise ValueError("Runtime release differs from diagnostic source release")
    questions = rows(pack / "questions.jsonl")
    original = answerer.retriever
    traced = TracedRetriever(original)
    answerer.retriever = traced
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            def execute(request):
                traced.calls.clear()
                routing = observe_route(request["question"], question_intent)
                response = client.post("/hus/chat", json=request)
                return {**capture_response(response, traced.calls), "routing_observation": routing}

            predictions = collect_run(questions, out, execute)
    finally:
        answerer.retriever = original

    # Scoring targets are loaded only after all predictions are persisted. The
    # preflight validator checks gold integrity but never injects it into requests.
    gold = rows(pack / "gold.jsonl")
    evidence = rows(parent / "evidence.jsonl")
    by_evidence = {item["evidence_id"]: item for item in evidence}
    oracle, binary_cache = EvidenceOracle(), {}
    with TestClient(app, raise_server_exceptions=False) as client:
        audits = [audit_development_prediction(prediction, target, by_evidence, oracle, client, binary_cache)
                  for prediction, target in zip(predictions, gold, strict=True)]
    write_rows(out / "citation_audits.jsonl", audits)
    cases, metrics = build_scores(questions, gold, evidence, predictions, audits)
    write_rows(out / "scored_cases.jsonl", cases)
    layers = build_layers(questions, gold, evidence, predictions, audits)
    write_json(out / "layered_metrics.json", layers)
    if (validate_pack(pack, ROOT) != preflight or runtime_hashes() != code_before
            or evaluation_hashes() != evaluator_before
            or artifact_hashes() != artifacts_before or environment_snapshot() != environment_before
            or {path: digest(ROOT / path) for path in source_before} != source_before
            or digest(ROOT / "data/hus/rag/CURRENT.json") != pointer_before):
        raise ValueError("Code, pack, baseline or source changed during dev measurement")
    report = {
        "schema_version": "1.1", "status": "development_measurement_not_independent_acceptance",
        "started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "pack": pack.relative_to(ROOT).as_posix(), "pack_manifest_sha256": preflight["manifest_sha256"],
        "questions_sha256": manifest["files"]["questions.jsonl"], "gold_sha256": manifest["files"]["gold.jsonl"],
        "git_head_is_base_only": subprocess.check_output(
            ["git", "-c", "safe.directory=" + ROOT.as_posix(), "rev-parse", "HEAD"], text=True).strip(),
        "git_state": "uncommitted_worktree", "tested_commit": None,
        "runtime_sha256": code_before, "evaluation_code_sha256": evaluator_before,
        "artifact_sha256": artifacts_before, "environment": environment_before,
        "artifact_and_environment_unchanged_during_run": True,
        "source_input_sha256": source_before, "CURRENT_sha256": pointer_before,
        "release_identity": answerer.data.release_identity, "split": "diagnostic_development",
        "holdout_inference_run": False, "development_inference_run": True,
        "independent_human_review": False, "holdout_eligible": False,
        "parent_split_status": manifest["parent_split_status"], "baseline_preserved": True,
        "metrics": metrics,
        "quality_layers_file": "layered_metrics.json",
        "by_major": {major: development_summary([case for case in cases if case["major"] == major])
                     for major in sorted(manifest["by_major"])},
        "by_category": {category: development_summary([case for case in cases if case["category"] == category])
                        for category in sorted(manifest["by_category"])},
        "source_binary_checks": binary_cache,
        "limits": [
            "Development paraphrases reuse exposed source anchors; no independent quality acceptance.",
            "Recall uses all F1/F3 positives and the first actual search top5, including routing misses.",
            "F2 uses structured facts plus source anchors, not Recall@5.",
            "Alternative citations can be correct; conservative anchor scoring requires human semantic review.",
            "Citation oracle checks source/page/review/AI and GET/hash, not semantic entailment or web health.",
            "In-process TestClient HTTP only; no browser, load, product database or production acceptance.",
        ],
        "product_database_modified": False, "vnu_contacted": False, "llm_used": False,
        "production_activated": False, "committed": False, "pushed": False,
    }
    write_json(out / "report.json", report)
    write_json(out / "manifest.json", {"schema_version": "1.0", "files_sha256": {
        path.name: digest(path) for path in sorted(out.iterdir()) if path.is_file()},
        "pack_manifest_sha256": preflight["manifest_sha256"]})
    return report


def verify_saved_run(run: Path):
    """Replay cached scores only; no app/HTTP/RAG import or inference."""
    run = Path(run).resolve()
    manifest = json.loads((run / "manifest.json").read_bytes())
    for name, expected in manifest["files_sha256"].items():
        path = (run / name).resolve()
        if not path.is_relative_to(run) or digest(path) != expected:
            raise ValueError(f"Saved run hash mismatch: {name}")
    report = json.loads((run / "report.json").read_bytes())
    pack = ROOT / report["pack"]
    preflight = validate_pack(pack, ROOT)
    if preflight["manifest_sha256"] != report["pack_manifest_sha256"]:
        raise ValueError("Saved run uses a different diagnostic pack")
    pack_manifest = json.loads((pack / "manifest.json").read_bytes())
    cases, metrics = build_scores(rows(pack / "questions.jsonl"), rows(pack / "gold.jsonl"),
                                  rows(ROOT / pack_manifest["source_pack"] / "evidence.jsonl"),
                                  rows(run / "predictions.jsonl"), rows(run / "citation_audits.jsonl"))
    if cases != rows(run / "scored_cases.jsonl") or metrics != report["metrics"]:
        raise ValueError("Saved scores/report differ from recomputed development metrics")
    for key, field in [("by_major", "major"), ("by_category", "category")]:
        for group, stored in report[key].items():
            if development_summary([case for case in cases if case[field] == group]) != stored:
                raise ValueError(f"Saved {key} metrics differ")
    if report.get("quality_layers_file"):
        layers = build_layers(rows(pack / "questions.jsonl"), rows(pack / "gold.jsonl"),
                              rows(ROOT / pack_manifest["source_pack"] / "evidence.jsonl"),
                              rows(run / "predictions.jsonl"), rows(run / "citation_audits.jsonl"))
        if layers != json.loads((run / report["quality_layers_file"]).read_bytes()):
            raise ValueError("Saved layered metrics differ from recomputed observations")
    return {"reproduced": True, "questions": len(cases), "new_rag_inference": False,
            "holdout_eligible": False, "metrics": metrics,
            "recorded_runtime_matches_current": report["runtime_sha256"] == runtime_hashes(),
            "recorded_evaluator_matches_current": report["evaluation_code_sha256"] == evaluation_hashes(),
            "recorded_artifacts_match_current": (report["artifact_sha256"] == artifact_hashes()
                                                   if "artifact_sha256" in report else None),
            "recorded_environment_matches_current": (report["environment"] == environment_snapshot()
                                                       if "environment" in report else None)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--out", type=Path, help="Fresh directory; never overwrite")
    parser.add_argument("--verify-run", type=Path, help="Verify cached artifacts without inference")
    args = parser.parse_args(argv)
    try:
        if args.verify_run:
            if args.out:
                parser.error("--verify-run cannot write --out")
            result = verify_saved_run(args.verify_run)
        else:
            if args.out is None:
                parser.error("--out is required for a new development run")
            report = run_evaluation(args.pack, args.out)
            result = {"out": str(args.out), "status": report["status"], "metrics": report["metrics"]}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, AssertionError, KeyError) as exc:
        print(f"Diagnostic measurement failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
