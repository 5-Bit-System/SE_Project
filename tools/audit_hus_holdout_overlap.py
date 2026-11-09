"""Offline lexical leakage audit; similarities require a real semantic reviewer."""

from __future__ import annotations

import argparse
import ast
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

from tools.validate_hus_holdout import normalize, rows, safe_path, sha

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "data/hus/evaluation/holdout_v2_candidate"
CODE = re.compile(r"\b[A-Z]{3}\d{4}[A-Z]?\b", re.I)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def prompts(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"question", "query"} and isinstance(child, str):
                yield child
            else:
                yield from prompts(child)
    elif isinstance(value, list):
        for child in value:
            yield from prompts(child)


def static_prompts(path):
    """Read literal parametrized prompts and dict requests without importing tests."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg in {"question", "query"}:
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                found[(node.value.lineno, node.value.value)] = node.value.value
        if isinstance(node, ast.Dict):
            for key, val in zip(node.keys, node.values, strict=True):
                if isinstance(key, ast.Constant) and key.value in {"question", "query"}:
                    if isinstance(val, ast.Constant) and isinstance(val.value, str):
                        found[(val.lineno, val.value)] = val.value
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "parametrize":
            if len(node.args) < 2:
                continue
            try:
                names, values = ast.literal_eval(node.args[0]), ast.literal_eval(node.args[1])
            except (ValueError, TypeError):
                continue
            if isinstance(names, str):
                names = [part.strip() for part in names.split(",")]
            for index, name in enumerate(names):
                if name not in {"question", "query", "message"}:
                    continue
                for value in values:
                    text = value if len(names) == 1 else value[index]
                    if isinstance(text, str):
                        found[(node.lineno, text)] = text
    return [{"source_id": f"line:{line}", "question": text} for (line, text) in found]


def audit_pack(pack, out, *, repo_root=ROOT, regression_paths=None):
    pack, out, repo_root = Path(pack).resolve(), Path(out).resolve(), Path(repo_root).resolve()
    require(not out.exists(), "output exists; choose a new directory")
    protected = [pack, repo_root / "data/hus/rag", repo_root / "data/hus/evaluation/p11_holdout_v1",
                 repo_root / "data/hus/evaluation/diagnostic_dev_v1", repo_root / "data/hus/evaluation/runs",
                 repo_root / "data/hus/evaluation/decisions"]
    require(not any(out.is_relative_to(path) for path in protected), "output overlaps protected inputs")
    manifest = json.loads((pack / "manifest.json").read_bytes())
    qpath = pack / "questions.jsonl"
    require(sha(qpath.read_bytes()) == manifest["files"]["questions.jsonl"], "question hash mismatch")
    input_hashes = {qpath.relative_to(repo_root).as_posix(): sha(qpath.read_bytes()),
                    (pack / "manifest.json").relative_to(repo_root).as_posix(): sha((pack / "manifest.json").read_bytes())}
    old = []
    for name, expected in manifest["development_inputs_sha256"].items():
        path = safe_path(repo_root, name)
        require(sha(path.read_bytes()) == expected, f"development hash mismatch: {name}")
        input_hashes[name] = expected
        for index, row in enumerate(rows(path)):
            for text in prompts(row):
                old.append({"source_path": name, "source_id": row.get("question_id", f"row:{index + 1}"),
                            "question": text})
    regression_count = 0
    paths = (sorted((repo_root / "tests/hus").glob("test_*.py")) if regression_paths is None else regression_paths)
    for path in paths:
        path = Path(path)
        name = path.relative_to(repo_root).as_posix()
        input_hashes[name] = sha(path.read_bytes())
        extracted = static_prompts(path)
        regression_count += len(extracted)
        old.extend(dict(item, source_path=name) for item in extracted)
    prepared = [(item, normalize(item["question"]), set(normalize(item["question"]).split())) for item in old]
    neighbors = []
    for question in rows(qpath):
        text = question["request"]["question"]
        norm, tokens = normalize(text), set(normalize(text).split())
        codes = {code.upper() for code in CODE.findall(text)}
        ranked = []
        for item, old_norm, old_tokens in prepared:
            jaccard = len(tokens & old_tokens) / len(tokens | old_tokens) if tokens | old_tokens else 0.0
            chars = SequenceMatcher(None, norm, old_norm, autojunk=False).ratio()
            ranked.append({**item, "token_jaccard": jaccard, "character_similarity": chars,
                           "exact_normalized_match": norm == old_norm,
                           "same_course_codes": sorted(codes & {code.upper() for code in CODE.findall(item["question"])})})
        ranked.sort(key=lambda row: (row["exact_normalized_match"], row["token_jaccard"], row["character_similarity"]), reverse=True)
        exact = any(item["exact_normalized_match"] for item in ranked)
        strong = any(item["token_jaccard"] >= .65 or item["character_similarity"] >= .85 for item in ranked)
        neighbors.append({"question_id": question["question_id"], "exact_duplicate": exact,
                          "strong_lexical_risk": strong, "human_review_required": True,
                          "neighbors": ranked[:3]})
    report = {"status": "lexical_audit_only_pending_human_review", "questions": len(neighbors),
              "comparison_count": len(neighbors) * len(old), "prior_prompt_occurrences": len(old),
              "regression_prompt_count": regression_count,
              "exact_duplicate_cases": sum(item["exact_duplicate"] for item in neighbors),
              "strong_lexical_risk_cases": sum(item["strong_lexical_risk"] for item in neighbors),
              "input_sha256": input_hashes, "human_accepted_reviews": 0,
              "auditor_sha256": sha(Path(__file__).read_bytes()),
              "static_prompt_forms": ["literal dictionaries", "literal keyword arguments", "literal parametrize cases"],
              "dynamic_prompt_coverage": "not exhaustive; reviewer must inspect dynamic/templated cases",
              "semantic_independence": "not_established_requires_human_review",
              "holdout_approved": False, "new_rag_inference": False,
              "limits": "Word/character overlap cannot establish equivalent meaning or independent authorship."}
    out.mkdir(parents=True)
    (out / "neighbors.jsonl").write_bytes("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in neighbors).encode())
    (out / "report.json").write_bytes((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    hashes = {path.name: sha(path.read_bytes()) for path in out.iterdir() if path.is_file()}
    (out / "manifest.json").write_bytes((json.dumps({"files_sha256": hashes}, indent=2) + "\n").encode())
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=PACK)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = audit_pack(args.pack, args.out)
        print(json.dumps({key: value for key, value in result.items() if key != "input_sha256"}, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Overlap audit failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
