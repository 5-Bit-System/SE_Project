"""Validate recorded human review claims offline; never certify a human identity."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

from tools.validate_hus_holdout import canonical, pointer, rows, safe_path, sha, validate_pack

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "data/hus/evaluation/holdout_v2_candidate"
CHECKS = ("source_checked", "answer_checked", "semantic_overlap_checked", "alternative_evidence_checked")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_reviews(questions, gold, reviews, evidence_catalog):
    """Check complete, hash-bound declarations; finalization still needs a human."""
    ids = [q["question_id"] for q in questions]
    require(len(ids) == len(set(ids)) and [g["question_id"] for g in gold] == ids
            and [r["question_id"] for r in reviews] == ids, "review/question/gold ID join mismatch")
    counts, majors, categories = Counter(), Counter(), Counter()
    for q, g, review in zip(questions, gold, reviews, strict=True):
        require(review["question_sha256"] == sha(canonical(q))
                and review["gold_sha256"] == sha(canonical(g)), "stale question/gold binding")
        decision = review["decision"]
        require(decision in {"pending", "accept", "reject", "revise"}, "invalid decision")
        counts.update([decision])
        if decision == "pending":
            continue
        require(review["reviewer_kind"] == "human", "review must declare a human reviewer")
        require(isinstance(review["reviewer"], str) and review["reviewer"].strip(), "missing real reviewer name")
        try:
            timestamp = datetime.fromisoformat(review["reviewed_at"])
            require(timestamp.tzinfo is not None and timestamp.utcoffset() is not None, "review requires timezone")
        except (ValueError, TypeError):
            raise ValueError("reviewed_at must include a valid timezone") from None
        require(review["independent_of_runtime_tuning"] is True, "reviewer must attest independent review")
        require(isinstance(review["notes"], str) and review["notes"].strip(), "missing review notes")
        if decision != "accept":
            continue
        require(all(review.get(key) is True for key in CHECKS), "all source/answer/overlap/alternatives must be checked")
        require(review["overlap_decision"] in {"distinct", "acceptable_shared_topic"}, "overlap requires revision/exclusion")
        require(isinstance(review["overlap_notes"], str) and review["overlap_notes"].strip(), "missing overlap rationale")
        require(isinstance(review["alternative_evidence_notes"], str)
                and review["alternative_evidence_notes"].strip(), "missing alternative evidence rationale")
        for eid in review["alternative_evidence_ids"]:
            require(eid in evidence_catalog, "unknown alternative evidence")
            allowed = evidence_catalog[eid].get("eligible_question_ids", [])
            require(q["question_id"] in allowed, "alternative evidence has incompatible scope/field")
        majors.update([q["request"]["major"]])
        categories.update([g["category"]])
    ready = counts["accept"] >= 40 and set(majors) == {q["request"]["major"] for q in questions}
    ready = ready and all(count >= 8 for count in majors.values())
    ready = ready and set(categories) == {g["category"] for g in gold}
    return {"status": "review_claims_ready_for_human_confirmation" if ready else "pending_real_human_review",
            "questions": len(ids), "decisions": dict(counts), "claimed_accepted_reviews": counts["accept"],
            "minimum_required": 40, "accepted_by_major": dict(majors), "accepted_by_category": dict(categories),
            "ready_for_human_freeze_confirmation": ready,
            "human_identity_verified_by_tool": False, "independent_holdout_certified": False,
            "rag_inference_run": False,
            "limits": "Validates declarations, not identity, source semantics or actual independent human work."}


def load_reviews(path):
    path = Path(path)
    if path.suffix.lower() != ".csv":
        return rows(path)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        result = list(csv.DictReader(stream))
    for review in result:
        for key in (*CHECKS, "independent_of_runtime_tuning"):
            value = review[key].strip().lower()
            require(value in {"true", "false", ""}, f"{key} must be true or false")
            review[key] = value == "true"
        for key in ["reviewer", "reviewer_kind", "reviewed_at", "overlap_decision", "overlap_notes",
                    "alternative_evidence_notes", "notes"]:
            review[key] = review[key].strip() or None
        review["alternative_evidence_ids"] = json.loads(review["alternative_evidence_ids"] or "[]")
    return result


def validate_catalog(pack, questions, gold, catalogue):
    manifest = json.loads((Path(pack) / "manifest.json").read_bytes())
    sources = {name: rows(safe_path(ROOT, name)) for name in manifest["source_inputs_sha256"]}
    by_q = {q["question_id"]: q for q in questions}
    by_g = {g["question_id"]: g for g in gold}
    anchors = {e["evidence_id"]: e for e in rows(Path(pack) / "evidence.jsonl")}
    for entry in catalogue.values():
        ref = entry["source_ref"]
        require(ref["path"] in sources, "alternative source is outside pinned inputs")
        matches = [r for r in sources[ref["path"]] if r.get(ref["identity_field"]) == ref["identity"]]
        require(len(matches) == 1, "alternative source identity is missing/ambiguous")
        source = matches[0]
        require(pointer(source, ref["json_pointer"]) == entry["value"], "alternative source value mismatch")
        require(source.get("citation") == entry["citation"], "alternative source citation mismatch")
        scope = source.get("scope") or {"major": source["major"], "curriculum_version": source["curriculum_version"]}
        require((entry["major"], entry["version"]) == (scope["major"], scope["curriculum_version"]),
                "alternative source scope mismatch")
        review = (source.get("catalog_review") or {}).get("status", source.get("review_status",
                  (source.get("citation") or {}).get("review_status", "needs_review")))
        require(entry["review_status"] == review
                and entry["content_origin"] == source.get("content_origin", "canonical_source"),
                "alternative source review/origin mismatch")
        family = source.get("family", Path(ref["path"]).name[:2]).lower()
        for qid in entry["eligible_question_ids"]:
            require(qid in by_q, "alternative references unknown question")
            request, target = by_q[qid]["request"], by_g[qid]
            require(scope["major"] == request["major"] and family == target["expected_dataset"],
                    "alternative question scope/family mismatch")
            if request["version"] is not None:
                require(scope["curriculum_version"] == request["version"], "alternative question version mismatch")
            else:
                require(scope["curriculum_version"] in {anchors[eid]["version"] for eid in target["evidence_ids"]},
                        "alternative source edition differs from pinned anchors")
            codes = set(re.findall(r"\b[A-Z]{3}\d{4}[A-Z]?\b", request["question"].upper()))
            if family != "f1":
                anchor_codes = set()
                for eid in target["evidence_ids"]:
                    anchor_ref = anchors[eid]["source_ref"]
                    for anchor_source in sources[anchor_ref["path"]]:
                        if anchor_source.get(anchor_ref["identity_field"]) == anchor_ref["identity"]:
                            anchor_codes.add(anchor_source.get("course_code"))
                require(source.get("course_code") in anchor_codes, "alternative differs from anchor course")
            if codes and family != "f1":
                require(source.get("course_code") in codes, "alternative course mismatch")
            if family in {"f1", "f3"}:
                require(source.get("field") == target["expected_field"], "alternative field mismatch")
            if family == "f2":
                allowed = {"/" + field.replace(".", "/") for field in target["expected_facts"]}
                require(ref["json_pointer"] in allowed, "alternative structured field mismatch")


def validate_reviews(pack=PACK, reviews_path=None, evidence_catalog_path=None):
    preflight = validate_pack(Path(pack), ROOT)
    questions, gold = [rows(Path(pack) / name) for name in ["questions.jsonl", "gold.jsonl"]]
    if reviews_path is None:
        reviews = [dict(r, independent_of_runtime_tuning=False, source_checked=False, answer_checked=False,
                        overlap_decision=None, overlap_notes=None, alternative_evidence_ids=[],
                        alternative_evidence_notes=None) for r in rows(Path(pack) / "review_decisions.jsonl")]
    else:
        reviews = load_reviews(Path(reviews_path))
    evidence_catalog = ({e["evidence_id"]: e for e in rows(Path(evidence_catalog_path))}
                        if evidence_catalog_path else {})
    validate_catalog(pack, questions, gold, evidence_catalog)
    result = check_reviews(questions, gold, reviews, evidence_catalog)
    result["candidate_manifest_sha256"] = preflight["pack_manifest_sha256"]
    result["review_file_sha256"] = sha(Path(reviews_path).read_bytes()) if reviews_path else None
    result["evidence_catalog_sha256"] = sha(Path(evidence_catalog_path).read_bytes()) if evidence_catalog_path else None
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=PACK)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--evidence-catalog", type=Path)
    parser.add_argument("--out", type=Path, help="New report only, refuses overwrite")
    args = parser.parse_args(argv)
    try:
        report = json.dumps(validate_reviews(args.pack, args.reviews, args.evidence_catalog), ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(report)
        print(report, end="")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Human review validation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
