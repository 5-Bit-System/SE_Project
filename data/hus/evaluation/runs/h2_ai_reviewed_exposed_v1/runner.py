"""One-off H2 AI-reviewed exposed benchmark; no runtime or shared scorer changes.

Only --out performs new inference. --validate-only and --verify-run are offline.
Run from any directory with the repository's pinned Python environment.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(parent for parent in Path(__file__).resolve().parents
            if (parent / "tools/evaluate_hus_diagnostic.py").is_file())
sys.path.insert(0, str(ROOT))

from tools.evaluate_hus_diagnostic import (  # noqa: E402
    artifact_hashes,
    audit_development_prediction,
    build_layers,
    build_scores,
    collect_run,
    environment_snapshot,
    evaluation_hashes,
    observe_route,
    runtime_hashes,
)
from tools.evaluate_hus_rag import (  # noqa: E402
    TracedRetriever,
    capture_response,
    digest,
    write_json,
    write_rows,
)
from tools.validate_hus_holdout import pointer, rows, safe_path  # noqa: E402

DEFAULT_PACK = ROOT / "data/hus/evaluation/ai_reviewed_exposed_v1"
PROTECTED = ROOT / "backups/h2_ai_review_finalize/protected_before.json"
STATUS = "ai_reviewed_exposed_evaluation"
REQUIRED_PAYLOADS = {"questions.jsonl", "gold.jsonl", "evidence.jsonl"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_bytes())


def protected_snapshot():
    expected = read_json(PROTECTED)
    actual = {name: digest(safe_path(ROOT, name)) for name in expected}
    require(actual == expected, "A protected runtime/data/frozen-review input changed")
    return actual


def validate_pack(pack):
    """Strict derivative contract, independently of old human/holdout validators."""
    pack = Path(pack).resolve()
    require(pack.is_relative_to((ROOT / "data/hus/evaluation").resolve()), "Pack outside evaluation tree")
    manifest = read_json(pack / "manifest.json")
    require(manifest["status"] == STATUS, "Pack must declare AI-reviewed exposed status")
    require(manifest["exposed"] is True, "Exposure must be declared")
    require(manifest["independent_human_review"] is False, "Human review cannot be claimed")
    require(manifest["independent_holdout_accepted"] is False, "Independent acceptance cannot be claimed")
    payloads = manifest["files_sha256"]
    require(REQUIRED_PAYLOADS <= payloads.keys(), "Missing frozen evaluation payload")
    for name, expected in payloads.items():
        path = safe_path(pack, name)
        require(digest(path) == expected, f"Pack payload changed: {name}")
        require(b"\r" not in path.read_bytes(), f"Pack payload must use LF: {name}")
    parents = manifest["parent_inputs_sha256"]
    require(parents and "data/hus/evaluation/holdout_v2_candidate/manifest.json" in parents,
            "Missing original candidate hash binding")
    require(any("holdout_v2_ai_review_v1/" in name for name in parents), "Missing AI review binding")
    for name, expected in parents.items():
        require(digest(safe_path(ROOT, name)) == expected, f"Parent/review input changed: {name}")
    release = safe_path(ROOT, manifest["source_release"])
    require(digest(release / "manifest.json") == manifest["source_release_manifest_sha256"],
            "Pinned source release manifest changed")
    source_rows = {}
    for name, expected in manifest["source_inputs_sha256"].items():
        path = safe_path(ROOT, name)
        require(path.is_relative_to(release), "Source input outside declared release")
        require(digest(path) == expected, f"Source input changed: {name}")
        source_rows[name] = rows(path)
    questions, gold, evidence = [rows(pack / name) for name in
                                 ["questions.jsonl", "gold.jsonl", "evidence.jsonl"]]
    ids = [q["question_id"] for q in questions]
    require(len(ids) == len(set(ids)) == manifest["question_count"] == 56, "Expected all56 unique questions")
    require([g["question_id"] for g in gold] == ids, "Gold/question ordered join mismatch")
    original_questions = ROOT / "data/hus/evaluation/holdout_v2_candidate/questions.jsonl"
    require((pack / "questions.jsonl").read_bytes() == original_questions.read_bytes(),
            "Derivative questions must remain byte-identical to original H2")
    require(dict(Counter(q["request"]["major"] for q in questions)) == manifest["by_major"], "Major counts differ")
    require(dict(Counter(g["category"] for g in gold)) == manifest["by_category"], "Category counts differ")
    by_id = {e["evidence_id"]: e for e in evidence}
    require(len(by_id) == len(evidence) == manifest["evidence_count"], "Duplicate or missing evidence")
    families = {}
    for evidence_row in evidence:
        ref = evidence_row["source_ref"]
        require(ref["path"] in source_rows, "Evidence source is not pinned")
        candidates = [r for r in source_rows[ref["path"]] if r.get(ref["identity_field"]) == ref["identity"]]
        require(len(candidates) == 1, "Missing or ambiguous source identity")
        source = candidates[0]
        require(pointer(source, ref["json_pointer"]) == evidence_row["value"], "Evidence/source pointer differs")
        scope = source.get("scope") or {"major": source["major"], "curriculum_version": source["curriculum_version"]}
        require((evidence_row["major"], evidence_row["version"]) == (scope["major"], scope["curriculum_version"]),
                "Evidence/source scope differs")
        require(evidence_row["citation"] == source.get("citation"), "Evidence/source citation differs")
        review = (source.get("catalog_review") or {}).get("status", source.get("review_status", (
            source.get("citation") or {}).get("review_status", "needs_review")))
        require(evidence_row["review_status"] == review, "Source review status was promoted")
        require(evidence_row["content_origin"] == source.get("content_origin", "canonical_source"), "Source origin differs")
        require(evidence_row["purpose"] in {"positive_support", "generated_reference", "absence_check"}, "Invalid evidence purpose")
        if evidence_row["purpose"] == "absence_check":
            require(evidence_row["value"] is None, "Absence anchor must reference null")
        families[evidence_row["evidence_id"]] = source.get("family", Path(ref["path"]).name[:2]).lower()
    for question, target in zip(questions, gold, strict=True):
        request = question["request"]
        require(set(request) == {"question", "major", "version", "allow_generated_reference"}, "Request leaks scoring hints")
        require(type(request["allow_generated_reference"]) is bool, "Opt-in must be boolean")
        require(target["review_status"] == "ai_reviewed", "Gold must declare AI review")
        refs = [by_id[eid] for eid in target["evidence_ids"]]
        for e in refs:
            require(families[e["evidence_id"]] == target["expected_dataset"], "Anchor dataset differs")
            require(e["major"] == request["major"], "Anchor/request major differs")
            if target["expected_dataset"] != "f1" or request["version"] is not None:
                require(e["version"] == request["version"], "Anchor/request version differs")
        category = target["category"]
        if category in {"f1", "f2", "f3"}:
            require(target["expected_dataset"] == category and target["expected_status"] == "answered" and refs,
                    "Invalid positive target")
            require(all(e["purpose"] != "absence_check" for e in refs), "Null evidence cannot support positive answer")
        elif category == "opt_in_required":
            require(target["expected_dataset"] == "f3" and request["allow_generated_reference"] is False
                    and target["expected_status"] == "needs_clarification" and not target["expected_citations"],
                    "Invalid opt-in target")
        else:
            require(category in {"missing_evidence", "out_of_scope"} and target["expected_status"] == "no_information"
                    and not target["expected_citations"] and not target["expected_facts"], "Invalid refusal target")
            require((refs and all(e["purpose"] == "absence_check" for e in refs)) if category == "missing_evidence"
                    else (not refs and bool(target["policy_reason"])), "Invalid missing/policy evidence")
        if category == "f2":
            facts = {e["source_ref"]["json_pointer"][1:].replace("/", "."): e["value"] for e in refs}
            require(target["expected_facts"] == facts, "F2 facts differ from pinned source")
        if target["expected_dataset"] == "f3" and category != "missing_evidence":
            require(target["academic_verified"] is False and target["authorizes_eligibility"] is False
                    and target["evidence_label"] == "kiến thức AI" and all(e["content_origin"] == "generated" for e in refs),
                    "Generated evidence was promoted or mislabelled")
            if category == "f3":
                require(request["allow_generated_reference"] is True, "Generated positive requires opt-in")
    return {"status": STATUS, "questions": len(questions), "evidence_ids": len(evidence),
            "manifest_sha256": digest(pack / "manifest.json"), "files_sha256": payloads,
            "independent_human_review": False, "independent_holdout_accepted": False}


def snapshot():
    return {"runtime_sha256": runtime_hashes(), "evaluation_code_sha256": evaluation_hashes(),
            "artifact_sha256": artifact_hashes(), "environment": environment_snapshot(),
            "protected_inputs_sha256": protected_snapshot(), "runner_sha256": digest(Path(__file__))}


def scores(pack, predictions, audits):
    questions, gold, evidence = [rows(pack / name) for name in
                                 ["questions.jsonl", "gold.jsonl", "evidence.jsonl"]]
    cases, metrics = build_scores(questions, gold, evidence, predictions, audits)
    layers = build_layers(questions, gold, evidence, predictions, audits)
    # Keep numerical fields and inherited legacy assumptions byte-for-byte.
    # The wrapper explains that AI review is authorized separately from those assumptions.
    layers["measurement_policy"] = {"status": STATUS, "human_review_required": False,
                                    "independent_human_review": False, "independent_holdout_accepted": False,
                                    "legacy_semantic_fields": "Remain null; any later AI semantic annotation is a separate artifact."}
    return questions, gold, cases, metrics, layers


def reserve_output(out):
    out = Path(out).resolve()
    runs = (ROOT / "data/hus/evaluation/runs").resolve()
    require(out.parent == runs, "New output must be a direct child of data/hus/evaluation/runs")
    require(not out.exists(), "Output already exists; choose a fresh run directory")
    out.mkdir(parents=True)
    return out


def run(pack, out):
    pack = Path(pack).resolve()
    preflight = validate_pack(pack)
    before = snapshot()
    out = reserve_output(out)
    started = datetime.now(timezone.utc).isoformat()
    shutil.copyfile(Path(__file__), out / "runner.py")
    write_json(out / "input_snapshot.json", before)
    # Runtime imports occur only inside the explicit new-inference path.
    from fastapi.testclient import TestClient

    from app.hus.demo import app
    from app.hus.question_routing import question_intent
    from app.services.hus_service import get_hus_answerer
    from tools.verify_hus_e2e import EvidenceOracle

    manifest = read_json(pack / "manifest.json")
    answerer = get_hus_answerer()
    selected = read_json(ROOT / manifest["source_release"] / "manifest.json")
    require(answerer.data.release_identity["release_sha256"] == selected["release_sha256"], "Runtime release differs")
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
    # All observations are saved before scorer targets are loaded here.
    gold, evidence = rows(pack / "gold.jsonl"), rows(pack / "evidence.jsonl")
    by_evidence = {row["evidence_id"]: row for row in evidence}
    oracle, binary_cache = EvidenceOracle(), {}
    with TestClient(app, raise_server_exceptions=False) as client:
        audits = [audit_development_prediction(p, g, by_evidence, oracle, client, binary_cache)
                  for p, g in zip(predictions, gold, strict=True)]
    write_rows(out / "citation_audits.jsonl", audits)
    questions, gold, cases, metrics, layers = scores(pack, predictions, audits)
    write_rows(out / "scored_cases.jsonl", cases)
    write_json(out / "layered_metrics.json", layers)
    require(validate_pack(pack) == preflight and snapshot() == before, "Input/code/environment changed during measurement")
    from tools.evaluate_hus_diagnostic import development_summary
    report = {"schema_version": "1.0", "status": STATUS, "split": "ai_reviewed_exposed",
              "exposed": True, "human_review_required": False, "independent_human_review": False,
              "independent_holdout_accepted": False, "human_accepted_questions": 0, "holdout_eligible": False,
              "inference_run": True, "new_rag_inference": True, "holdout_inference_run": False,
              "parent_creation_flags_are_historical": True, "runtime_tuning_performed": False,
              "started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
              "pack": pack.relative_to(ROOT).as_posix(), "pack_manifest_sha256": preflight["manifest_sha256"],
              "input_snapshot_file": "input_snapshot.json", "runner_file": "runner.py",
              "runner_sha256": before["runner_sha256"], "runner_original": Path(__file__).relative_to(ROOT).as_posix(),
              "git_head_is_base_only": subprocess.check_output(["git", "-c", "safe.directory=" + ROOT.as_posix(),
                                                                "rev-parse", "HEAD"], text=True).strip(),
              "git_state": "uncommitted_worktree", "tested_commit": None,
              "release_identity": answerer.data.release_identity, "metrics": metrics,
              "by_major": {major: development_summary([case for case in cases if case["major"] == major])
                           for major in sorted(manifest["by_major"])},
              "by_category": {category: development_summary([case for case in cases if case["category"] == category])
                              for category in sorted(manifest["by_category"])},
              "quality_layers_file": "layered_metrics.json", "source_binary_checks": binary_cache,
              "inputs_unchanged_during_run": True,
              "limits": ["AI-reviewed exposed evaluation, without human or independent quality certification.",
                         "Legacy scorer semantic fields remain null; AI semantic judgments belong in a separate bound report.",
                         "Legacy source-supported success requires any valid expected anchor, not coverage of every claim or anchor.",
                         "Q043/Q044 multi-anchor retrieval recall averages all required anchors; answer completeness needs separate review.",
                         "Q048 legacy facts compares raw_variants=[] to runtime source-row representation [null]; no silent normalization.",
                         "Classifier is observed before guards; retrieval is first real search top5; F2 is structured lookup.",
                         "In-process TestClient only; no browser, latency/load, live website health or production acceptance."],
              "product_database_modified": False, "vnu_contacted": False, "llm_used_for_runtime": False,
              "production_activated": False, "committed": False, "pushed": False}
    write_json(out / "report.json", report)
    write_json(out / "manifest.json", {"schema_version": "1.0", "status": STATUS,
               "pack_manifest_sha256": preflight["manifest_sha256"],
               "files_sha256": {path.name: digest(path) for path in sorted(out.iterdir()) if path.is_file()}})
    return report


def verify(run_dir):
    """Replay recorded scores only; imports no runtime app, HTTP client or oracle."""
    run_dir = Path(run_dir).resolve()
    manifest = read_json(run_dir / "manifest.json")
    for name, expected in manifest["files_sha256"].items():
        require(digest(safe_path(run_dir, name)) == expected, f"Saved output changed: {name}")
    report = read_json(run_dir / "report.json")
    require(report["status"] == STATUS and report["independent_holdout_accepted"] is False, "Invalid report policy")
    pack = safe_path(ROOT, report["pack"])
    preflight = validate_pack(pack)
    require(preflight["manifest_sha256"] == report["pack_manifest_sha256"] == manifest["pack_manifest_sha256"],
            "Saved pack differs")
    questions, gold, cases, metrics, layers = scores(pack, rows(run_dir / "predictions.jsonl"),
                                                    rows(run_dir / "citation_audits.jsonl"))
    require(cases == rows(run_dir / "scored_cases.jsonl") and metrics == report["metrics"], "Saved score differs")
    require(layers == read_json(run_dir / "layered_metrics.json"), "Saved layered score differs")
    from tools.evaluate_hus_diagnostic import development_summary
    for key, field in [("by_major", "major"), ("by_category", "category")]:
        expected = {group: development_summary([case for case in cases if case[field] == group])
                    for group in sorted({case[field] for case in cases})}
        require(expected == report[key], f"Saved {key} differs")
    before = read_json(run_dir / "input_snapshot.json")
    require(digest(run_dir / "runner.py") == report["runner_sha256"] == before["runner_sha256"], "Saved runner differs")
    current = snapshot()
    return {"reproduced": True, "status": STATUS, "questions": len(questions), "new_rag_inference": False,
            "independent_human_review": False, "independent_holdout_accepted": False,
            "recorded_inputs_match_current": before == current, "metrics": metrics}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out", type=Path, help="Fresh run directory; performs new RAG inference")
    mode.add_argument("--verify-run", type=Path, help="Replay saved scores without new inference")
    mode.add_argument("--validate-only", action="store_true", help="Validate inputs only; no runtime imports")
    args = parser.parse_args()
    try:
        if args.verify_run:
            result = verify(args.verify_run)
        elif args.validate_only:
            result = {**validate_pack(args.pack), "protected_files": len(protected_snapshot()), "new_rag_inference": False}
        else:
            report = run(args.pack, args.out)
            result = {"out": str(args.out), "status": report["status"], "metrics": report["metrics"]}
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (OSError, ValueError, AssertionError, KeyError, TypeError, StopIteration) as exc:
        print(f"AI exposed measurement failed: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
