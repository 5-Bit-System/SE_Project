"""Check a source-grounded reviewer pack offline, without querying or tuning RAG."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACK = ROOT / "data/hus/evaluation/p11_holdout_v1"
MAJORS = {"mathematics", "mathematics_informatics", "computer_science", "data_science"}
PAYLOADS = {"questions.jsonl", "gold.jsonl", "evidence.jsonl", "review_decisions.jsonl",
            "README.md", "reviewer_packet.md"}
AI_LABEL = "kiến thức AI"


class HoldoutError(ValueError):
    """The pack does not satisfy the frozen candidate contract."""


def require(condition, message):
    if not condition:
        raise HoldoutError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def normalize(question):
    text = unicodedata.normalize("NFKD", question.casefold())
    return " ".join(re.findall(r"[^\W_]+", "".join(c for c in text if not unicodedata.combining(c))))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def safe_path(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), "source path escapes repository")
    return path


def pointer(value, path):
    require(path.startswith("/"), "invalid JSON pointer")
    for part in path[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def question_strings(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"question", "query"} and isinstance(child, str):
                yield normalize(child)
            else:
                yield from question_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from question_strings(child)


def validate_pack(pack: Path = DEFAULT_PACK, repo_root: Path = ROOT) -> dict:
    """Validate integrity, isolation and draft-gold constraints; not answer quality."""
    pack, repo_root = Path(pack), Path(repo_root)
    try:
        return _validate(pack, repo_root)
    except (OSError, KeyError, TypeError, json.JSONDecodeError, IndexError) as exc:
        raise HoldoutError(f"Malformed or missing pack/source input: {exc}") from exc


def _validate(pack, repo_root):
    manifest = json.loads((pack / "manifest.json").read_text(encoding="utf-8"))
    require(manifest["schema_version"] == "1.0", "unknown schema")
    require(set(manifest["files"]) == PAYLOADS, "unexpected payload set")
    require(manifest["status"] == "candidate_pending_independent_review", "candidate status changed")
    require(manifest["split"] == "prospective_holdout_candidate", "invalid holdout split")
    for flag in ["independent_human_review", "rag_inference_run", "used_for_retrieval_tuning",
                 "human_author_independence_claimed"]:
        require(manifest[flag] is False, f"unattested flag: {flag}")
    require(manifest["retrieval_metrics"] is None, "P1-1 must not invent metrics")
    for name, expected in manifest["files"].items():
        raw = (pack / name).read_bytes()
        require(sha(raw) == expected, f"payload hash mismatch: {name}")
        require(b"\r" not in raw, f"payload must be UTF-8/LF: {name}")
    source_root = safe_path(repo_root, manifest["source_release"])
    require(sha((source_root / "manifest.json").read_bytes()) == manifest["release_manifest_sha256"],
            "release manifest hash mismatch")
    source_rows = {}
    for path, expected in manifest["source_inputs_sha256"].items():
        source = safe_path(repo_root, path)
        require(source.is_relative_to(source_root), "source outside pinned release")
        require(sha(source.read_bytes()) == expected, f"source hash mismatch: {path}")
        source_rows[path] = rows(source)
    development = set()
    for path, expected in manifest["development_inputs_sha256"].items():
        source = safe_path(repo_root, path)
        require(sha(source.read_bytes()) == expected, f"development input hash mismatch: {path}")
        for row in rows(source):
            development.update(question_strings(row))

    questions, gold, evidence, reviews = (rows(pack / name) for name in
                                         ["questions.jsonl", "gold.jsonl", "evidence.jsonl",
                                          "review_decisions.jsonl"])
    qids = [q["question_id"] for q in questions]
    require(len(set(qids)) == len(qids) >= 40, "duplicate IDs or fewer than 40 questions")
    require(len(questions) == manifest["question_count"], "question count mismatch")
    require([g["question_id"] for g in gold] == qids, "gold question join mismatch")
    require([r["question_id"] for r in reviews] == qids, "review question join mismatch")
    by_major = Counter(q["request"]["major"] for q in questions)
    require(set(by_major) == MAJORS and len(set(by_major.values())) == 1, "unbalanced major coverage")
    require(dict(by_major) == manifest["by_major"], "major count mismatch")
    by_category = Counter(g["category"] for g in gold)
    require(dict(by_category) == manifest["by_category"], "category count mismatch")
    require(set(by_category) == {"f1", "f2", "f3", "missing_evidence", "out_of_scope", "opt_in_required"},
            "missing required evaluation category")
    normalized = [normalize(q["request"]["question"]) for q in questions]
    require(all(normalized) and len(set(normalized)) == len(normalized), "duplicate question")
    require(not set(normalized) & development, "development question overlap")
    ev = {e["evidence_id"]: e for e in evidence}
    require(len(ev) == len(evidence) == manifest["evidence_count"], "duplicate evidence or count mismatch")
    evidence_families = {}
    for e in evidence:
        ref = e["source_ref"]
        require(ref["path"] in source_rows, "unhashed evidence source")
        matches = [r for r in source_rows[ref["path"]] if r.get(ref["identity_field"]) == ref["identity"]]
        require(len(matches) == 1, "source identity missing or ambiguous")
        source = matches[0]
        family = source.get("family", Path(ref["path"]).name[:2]).lower()
        require(family in {"f1", "f2", "f3"}, "unknown evidence dataset")
        evidence_families[e["evidence_id"]] = family
        require(pointer(source, ref["json_pointer"]) == e["value"], "source value mismatch")
        scope = source.get("scope") or {"major": source["major"], "curriculum_version": source["curriculum_version"]}
        require((e["major"], e["version"]) == (scope["major"], scope["curriculum_version"]), "source scope mismatch")
        require(e["citation"] == source.get("citation"), "source citation changed")
        expected_review = (source.get("catalog_review") or {}).get(
            "status", source.get("review_status", (source.get("citation") or {}).get("review_status", "needs_review")))
        require(e["review_status"] == expected_review, "source review changed")
        require(e["content_origin"] == source.get("content_origin", "canonical_source"), "source origin changed")
        require(e["purpose"] in {"positive_support", "generated_reference", "absence_check"}, "invalid evidence purpose")
        if e["purpose"] == "absence_check":
            require(e["value"] is None, "absence check must reference a null source value")
    for q, g, review in zip(questions, gold, reviews, strict=True):
        request = q["request"]
        require(set(request) == {"question", "major", "version", "allow_generated_reference"},
                "question request leaks gold dataset/field/code hints")
        require(type(request["allow_generated_reference"]) is bool, "opt-in must be boolean")
        refs = [ev[eid] for eid in g["evidence_ids"]]
        category = g["category"]
        if category in {"f1", "f2", "f3"}:
            require(g["expected_dataset"] == category, "category/gold dataset mismatch")
        if category == "opt_in_required":
            require(g["expected_dataset"] == "f3", "opt-in dataset mismatch")
        for e in refs:
            require(evidence_families[e["evidence_id"]] == g["expected_dataset"], "evidence dataset mismatch")
            require(e["major"] == request["major"], "evidence scope mismatch")
            if g["expected_dataset"] != "f1" or request["version"] is not None:
                require(e["version"] == request["version"], "evidence version scope mismatch")
        require(g["review_status"] == "pending_independent_review", "unattested gold acceptance")
        if category in {"missing_evidence", "out_of_scope"}:
            require(g["expected_status"] == "no_information" and g["expected_citations"] == []
                    and not g["expected_facts"], "abstention case cannot demand positive facts/citations")
            if category == "missing_evidence":
                require(refs and all(e["purpose"] == "absence_check" for e in refs), "missing absence check")
            else:
                require(not refs and g["policy_reason"], "out-of-scope must use policy, not false source evidence")
        elif category == "opt_in_required":
            require(request["allow_generated_reference"] is False
                    and g["expected_status"] == "needs_clarification"
                    and g["expected_citations"] == [], "missing opt-in clarification")
        else:
            require(g["expected_status"] == "answered" and refs, "answered case missing evidence")
            require(all(e["purpose"] != "absence_check" for e in refs), "absence is not positive support")
        if category == "f2":
            facts = {e["source_ref"]["json_pointer"][1:].replace("/", "."): e["value"] for e in refs}
            require(g["expected_facts"] == facts, "unsupported gold facts")
        generated = any(e["content_origin"] == "generated" and e["purpose"] != "absence_check" for e in refs)
        if generated or (g["expected_dataset"] == "f3" and category != "missing_evidence"):
            require(g["expected_dataset"] == "f3" and g["evidence_label"] == AI_LABEL and g["academic_verified"] is False
                    and g["authorizes_eligibility"] is False
                    and all(e["content_origin"] == "generated" for e in refs), "AI gold promoted or mislabelled")
            if category == "f3":
                require(request["allow_generated_reference"] is True, "AI answer missing opt-in")
        require(review["decision"] == "pending" and all(review[k] is None for k in
                ["reviewer", "reviewed_at", "reviewer_kind"]), "candidate must not invent independent reviewer")
        require(review["question_sha256"] == sha(canonical(q))
                and review["gold_sha256"] == sha(canonical(g)), "stale review binding")
    return {"status": manifest["status"], "questions": len(questions), "evidence_ids": len(evidence),
            "by_major": dict(by_major), "by_category": dict(by_category), "accepted_reviews": 0,
            "normalized_development_questions": len(development), "exact_development_overlap": 0,
            "semantic_overlap": "pending independent reviewer",
            "rag_inference_run": False, "retrieval_metrics": None,
            "runtime_matches_baseline": all(sha(safe_path(repo_root, p).read_bytes()) == h for p, h in
                                            manifest["baseline_runtime_sha256"].items()),
            "pack_manifest_sha256": sha((pack / "manifest.json").read_bytes()),
            "questions_sha256": manifest["files"]["questions.jsonl"],
            "gold_sha256": manifest["files"]["gold.jsonl"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, help="Write a new validation report; refuses overwrite")
    args = parser.parse_args(argv)
    try:
        report = validate_pack(args.pack, args.repo_root)
        output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(output)
        print(output, end="")
        return 0
    except (HoldoutError, OSError) as exc:
        print(f"Holdout validation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
