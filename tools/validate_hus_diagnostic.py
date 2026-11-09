"""Validate exposed development cases offline; never invoke RAG or grant review."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from tools.validate_hus_holdout import normalize, rows, safe_path, sha
from tools.validate_hus_holdout import validate_pack as validate_parent

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = ROOT / "data/hus/evaluation/diagnostic_dev_v1"
PARENT = "data/hus/evaluation/p11_holdout_v1"
PAYLOADS = {"questions.jsonl", "gold.jsonl", "cases.jsonl", "README.md", "casebook.md"}
TAGS = {"natural_language", "synonym", "negation", "course_name", "course_code", "out_of_scope"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_pack(pack: Path = DEFAULT_PACK, repo_root: Path = ROOT) -> dict:
    """Verify source bindings and development bookkeeping, not semantic quality."""
    pack, repo_root = Path(pack), Path(repo_root)
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    require(manifest["schema_version"] == "1.0", "unknown schema")
    require(manifest["split"] == "diagnostic_development" and manifest["holdout_eligible"] is False,
            "development pack cannot claim independent holdout")
    require(manifest["independent_human_review"] is False and manifest["rag_inference_run"] is False
            and manifest["retrieval_metrics"] is None, "unattested review or inference")
    require(manifest["source_pack"] == PARENT, "unexpected source pack")
    require(manifest["parent_split_status"] == "exposed_for_development_not_final_holdout",
            "parent holdout exposure must be recorded")
    require(set(manifest["files"]) == PAYLOADS, "unexpected payload set")
    for name, expected in manifest["files"].items():
        raw = (pack / name).read_bytes()
        require(sha(raw) == expected, f"payload hash mismatch: {name}")
        require(b"\r" not in raw, f"payload requires LF: {name}")
    # Frozen originals and baseline artifacts stay byte-identical. Runtime code is
    # recorded separately as a preparation snapshot, so later tuning is permitted.
    protected = manifest["protected_inputs_sha256"]
    baseline_files = {p.relative_to(repo_root).as_posix() for directory in
                      [PARENT, "data/hus/evaluation/runs/p12_baseline_v1", "data/hus/evaluation/decisions/p2_v1"]
                      for p in (repo_root / directory).rglob("*") if p.is_file()}
    require(set(protected) == baseline_files, "protected baseline file set mismatch")
    for name, expected in protected.items():
        require(sha(safe_path(repo_root, name).read_bytes()) == expected, f"protected baseline hash mismatch: {name}")
    parent = repo_root / PARENT
    validate_parent(parent, repo_root)
    parents = {q["question_id"]: q for q in rows(parent / "questions.jsonl")}
    parent_gold = {g["question_id"]: g for g in rows(parent / "gold.jsonl")}
    questions, gold, cases = [rows(pack / name) for name in
                              ["questions.jsonl", "gold.jsonl", "cases.jsonl"]]
    ids = [q["question_id"] for q in questions]
    require(len(set(ids)) == len(ids) == manifest["question_count"] == 96, "question count or duplicate ID")
    require([g["question_id"] for g in gold] == ids == [c["question_id"] for c in cases], "ID join mismatch")
    unique = [(normalize(q["request"]["question"]), q["request"]["major"], q["request"]["version"],
               q["request"]["allow_generated_reference"]) for q in questions]
    require(all(key[0] for key in unique), "empty question")
    require(len(set(unique)) == len(unique), "duplicate request")
    old_texts = {normalize(q["request"]["question"]) for q in parents.values()}
    require(not {key[0] for key in unique} & old_texts, "exact parent question overlap")
    coverage = Counter()
    per_major_tags = {}
    contrasts = {}
    parent_counts = Counter()
    for q, g, case in zip(questions, gold, cases, strict=True):
        request = q["request"]
        require(set(request) == {"question", "major", "version", "allow_generated_reference"}, "request leaks gold hints")
        require(type(request["allow_generated_reference"]) is bool, "invalid opt-in type")
        pid = case["parent_question_id"]
        require(pid in parents, "unknown parent")
        parent_counts.update([pid])
        original = parents[pid]["request"]
        require((request["major"], request["version"]) == (original["major"], original["version"]), "parent scope mismatch")
        require(request["allow_generated_reference"] == original["allow_generated_reference"], "parent opt-in mismatch")
        expected = dict(parent_gold[pid], question_id=q["question_id"])
        require(g == expected, "gold differs from pinned source-grounded parent")
        require(case["review_status"] == "ai_authored_draft_not_human_accepted", "unattested case review")
        require(case["tags"] and set(case["tags"]) <= TAGS, "invalid coverage tags")
        coverage.update(case["tags"])
        per_major_tags.setdefault(request["major"], set()).update(case["tags"])
        if case["contrast_group"] is not None:
            contrasts.setdefault(case["contrast_group"], []).append(request)
    require(set(parent_counts) == set(parents) and set(parent_counts.values()) == {2}, "parent coverage mismatch")
    require(len(contrasts) == 4, "contrast group coverage mismatch")
    for group in contrasts.values():
        prompts = {}
        for request in group:
            prompts.setdefault(request["question"], []).append(request["allow_generated_reference"])
        require(len(prompts) == 2 and all(sorted(flags) == [False, True] for flags in prompts.values()),
                "contrast pairs must differ only in opt-in")
    require(all(tags == TAGS for tags in per_major_tags.values()), "missing per-major coverage")
    by_major = dict(Counter(q["request"]["major"] for q in questions))
    by_category = dict(Counter(g["category"] for g in gold))
    require(by_major == manifest["by_major"] and len(by_major) == 4 and set(by_major.values()) == {24}, "major counts")
    require(by_category == manifest["by_category"] and dict(coverage) == manifest["by_tag"], "coverage counts")
    require(len({q["request"]["question"] for q in questions}) == manifest["unique_question_texts"],
            "unique text count mismatch")
    return {"status": "valid_development_draft", "questions": len(questions), "by_major": by_major,
            "by_category": by_category, "by_tag": dict(coverage), "baseline_preserved": True,
            "holdout_eligible": False, "parent_split_status": manifest["parent_split_status"],
            "independent_human_review": False, "rag_inference_run": False, "retrieval_metrics": None,
            "semantic_equivalence": "pending human review; inheritance is not semantic proof",
            "manifest_sha256": sha((pack / "manifest.json").read_bytes())}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, help="Write a new report, never overwrite")
    args = parser.parse_args(argv)
    try:
        report = json.dumps(validate_pack(args.pack, args.repo_root), ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(report)
        print(report, end="")
        return 0
    except (ValueError, OSError, KeyError, TypeError, IndexError) as exc:
        print(f"Diagnostic validation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
