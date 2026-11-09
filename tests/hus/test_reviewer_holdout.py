"""Integrity checks protect the evaluation pack without running RAG on holdout questions."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from tools.validate_hus_holdout import HoldoutError, validate_pack

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "data/hus/evaluation/p11_holdout_v1"


def edit_rows(pack, name, mutate):
    path = pack / name
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    mutate(rows)
    path.write_bytes("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode("utf-8"))
    manifest_path = pack / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def refresh_review_bindings(pack):
    def digest(value):
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
    questions = [json.loads(line) for line in (pack / "questions.jsonl").read_text(encoding="utf-8").splitlines()]
    gold = [json.loads(line) for line in (pack / "gold.jsonl").read_text(encoding="utf-8").splitlines()]
    def mutate(reviews):
        for q, g, review in zip(questions, gold, reviews, strict=True):
            review.update(question_sha256=digest(q), gold_sha256=digest(g))
    edit_rows(pack, "review_decisions.jsonl", mutate)


@pytest.fixture
def copied_pack(tmp_path):
    return Path(shutil.copytree(PACK, tmp_path / "holdout"))


def test_candidate_is_balanced_grounded_and_not_human_accepted():
    report = validate_pack(PACK, ROOT)
    assert report["questions"] == 48
    assert set(report["by_major"].values()) == {12}
    assert report["status"] == "candidate_pending_independent_review"
    assert report["accepted_reviews"] == 0
    assert report["rag_inference_run"] is False


def test_hash_tampering_is_rejected(copied_pack):
    with (copied_pack / "questions.jsonl").open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(HoldoutError, match="hash"):
        validate_pack(copied_pack, ROOT)


def test_gold_cannot_point_at_another_major(copied_pack):
    def mutate(rows):
        rows[0]["evidence_ids"] = [rows[12]["evidence_ids"][0]]
    edit_rows(copied_pack, "gold.jsonl", mutate)
    with pytest.raises(HoldoutError, match="scope"):
        validate_pack(copied_pack, ROOT)


def test_source_quote_cannot_be_fabricated(copied_pack):
    edit_rows(copied_pack, "evidence.jsonl", lambda rows: rows[0].update(value="fabricated source"))
    with pytest.raises(HoldoutError, match="source value"):
        validate_pack(copied_pack, ROOT)


def test_generated_gold_cannot_be_promoted_to_official(copied_pack):
    def mutate(rows):
        next(r for r in rows if r["expected_dataset"] == "f3" and r["expected_status"] == "answered")["evidence_label"] = "official PDF"
    edit_rows(copied_pack, "gold.jsonl", mutate)
    with pytest.raises(HoldoutError, match="AI"):
        validate_pack(copied_pack, ROOT)


def test_duplicate_questions_are_rejected_even_with_valid_hashes(copied_pack):
    def mutate(rows):
        rows[1]["request"]["question"] = rows[0]["request"]["question"]
    edit_rows(copied_pack, "questions.jsonl", mutate)
    with pytest.raises(HoldoutError, match="duplicate question"):
        validate_pack(copied_pack, ROOT)


def test_unsupported_gold_fact_is_rejected(copied_pack):
    def mutate(rows):
        next(r for r in rows if r["expected_dataset"] == "f2" and r["expected_status"] == "answered")["expected_facts"] = {"credits": 999}
    edit_rows(copied_pack, "gold.jsonl", mutate)
    with pytest.raises(HoldoutError, match="gold facts"):
        validate_pack(copied_pack, ROOT)


def test_missing_evidence_case_cannot_demand_a_positive_answer(copied_pack):
    def mutate(rows):
        next(r for r in rows if r["category"] == "missing_evidence")["expected_status"] = "answered"
    edit_rows(copied_pack, "gold.jsonl", mutate)
    with pytest.raises(HoldoutError, match="abstention"):
        validate_pack(copied_pack, ROOT)


def test_source_review_cannot_be_upgraded(copied_pack):
    edit_rows(copied_pack, "evidence.jsonl", lambda rows: rows[0].update(review_status="official_verified"))
    with pytest.raises(HoldoutError, match="source review"):
        validate_pack(copied_pack, ROOT)


def test_reusing_a_development_question_is_rejected(copied_pack):
    manifest = json.loads((copied_pack / "manifest.json").read_text(encoding="utf-8"))
    path = next(p for p in manifest["development_inputs_sha256"] if p.endswith("evaluation/questions.jsonl"))
    first = json.loads((ROOT / path).read_text(encoding="utf-8").splitlines()[0])
    duplicate = first.get("question") or first["query"]
    edit_rows(copied_pack, "questions.jsonl", lambda rows: rows[0]["request"].update(question=duplicate))
    with pytest.raises(HoldoutError, match="development question overlap"):
        validate_pack(copied_pack, ROOT)


def test_generated_evidence_cannot_hide_behind_a_different_dataset(copied_pack):
    def mutate(rows):
        item = next(r for r in rows if r["category"] == "f3")
        item.update(expected_dataset="f1", evidence_label="official PDF",
                    academic_verified=True, authorizes_eligibility=True)
    edit_rows(copied_pack, "gold.jsonl", mutate)
    refresh_review_bindings(copied_pack)
    with pytest.raises(HoldoutError, match="dataset|AI"):
        validate_pack(copied_pack, ROOT)


def test_explicit_f1_version_cannot_borrow_another_edition(copied_pack):
    def mutate(rows):
        rows[1]["request"]["version"] = "QD3565-2023"
    edit_rows(copied_pack, "questions.jsonl", mutate)
    refresh_review_bindings(copied_pack)
    with pytest.raises(HoldoutError, match="version"):
        validate_pack(copied_pack, ROOT)
