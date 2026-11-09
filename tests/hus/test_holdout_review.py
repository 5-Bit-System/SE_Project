"""A review gate cannot turn prepared AI data into independent human approval."""

import csv
import hashlib
import importlib
import io
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module():
    assert (ROOT / "tools/validate_hus_holdout_review.py").exists(), "review gate is not implemented"
    return importlib.import_module("tools.validate_hus_holdout_review")


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def fixture_rows(count=56):
    # Invented review records test validation rules; they are never project signoffs.
    questions, gold, reviews = [], [], []
    for index in range(count):
        qid = f"SYNTHETIC-{index:03}"
        question = {"question_id": qid, "request": {"major": f"major-{index % 4}", "question": "invented"}}
        target = {"question_id": qid, "category": ["f1", "f2", "f3", "missing_evidence",
                                                       "out_of_scope", "opt_in_required"][index % 6]}
        questions.append(question)
        gold.append(target)
        reviews.append({"question_id": qid, "question_sha256": digest(question), "gold_sha256": digest(target),
                        "decision": "pending", "reviewer": None, "reviewer_kind": None,
                        "reviewed_at": None, "independent_of_runtime_tuning": False,
                        "source_checked": False, "answer_checked": False,
                        "semantic_overlap_checked": False, "alternative_evidence_checked": False,
                        "overlap_decision": None, "overlap_notes": None,
                        "alternative_evidence_ids": [], "alternative_evidence_notes": None,
                        "notes": None})
    return questions, gold, reviews


def accept(review):
    review.update(decision="accept", reviewer="SYNTHETIC TEST PERSON", reviewer_kind="human",
                  reviewed_at="2026-11-03T00:00:00+07:00", independent_of_runtime_tuning=True,
                  source_checked=True, answer_checked=True, semantic_overlap_checked=True,
                  alternative_evidence_checked=True, overlap_decision="acceptable_shared_topic",
                  overlap_notes="Synthetic test only: checked context and meaning, no case copied.",
                  alternative_evidence_notes="Synthetic test only: no additional equivalent evidence found.",
                  notes="Synthetic validation record, not a genuine reviewer signoff.")


def test_empty_review_remains_pending_with_zero_acceptance():
    questions, gold, reviews = fixture_rows()
    report = module().check_reviews(questions, gold, reviews, {})
    assert report["claimed_accepted_reviews"] == 0
    assert report["ready_for_human_freeze_confirmation"] is False
    assert report["human_identity_verified_by_tool"] is False


def test_forty_complete_claims_require_explicit_human_finalization():
    questions, gold, reviews = fixture_rows()
    for review in reviews[:40]:
        accept(review)
    report = module().check_reviews(questions, gold, reviews, {})
    assert report["claimed_accepted_reviews"] == 40
    assert report["ready_for_human_freeze_confirmation"] is True
    assert report["independent_holdout_certified"] is False


@pytest.mark.parametrize("mutation,match", [
    (lambda r: r.update(reviewer_kind="ai"), "human"),
    (lambda r: r.update(reviewer=" "), "reviewer"),
    (lambda r: r.update(reviewed_at="2026-11-03"), "timezone"),
    (lambda r: r.update(question_sha256="wrong"), "binding"),
    (lambda r: r.update(source_checked=False), "checked"),
    (lambda r: r.update(semantic_overlap_checked=False), "checked"),
    (lambda r: r.update(independent_of_runtime_tuning=False), "independent"),
    (lambda r: r.update(overlap_decision="exclude"), "overlap"),
    (lambda r: r.update(alternative_evidence_ids=["unknown-id"]), "alternative"),
])
def test_incomplete_or_unsupported_signoff_is_rejected(mutation, match):
    questions, gold, reviews = fixture_rows()
    accept(reviews[0])
    mutation(reviews[0])
    with pytest.raises(ValueError, match=match):
        module().check_reviews(questions, gold, reviews, {})


def test_duplicate_and_stale_review_ids_are_rejected():
    questions, gold, reviews = fixture_rows()
    reviews[1] = reviews[0].copy()
    with pytest.raises(ValueError, match="join"):
        module().check_reviews(questions, gold, reviews, {})


def test_csv_worksheet_can_be_read_without_filling_a_signature(tmp_path):
    _, _, reviews = fixture_rows(1)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(reviews[0]))
    writer.writeheader()
    row = dict(reviews[0], alternative_evidence_ids="[]")
    writer.writerow(row)
    path = tmp_path / "review.csv"
    path.write_text(buffer.getvalue(), encoding="utf-8")
    loaded = module().load_reviews(path)
    assert loaded[0]["source_checked"] is False
    assert loaded[0]["reviewer"] is None
    assert loaded[0]["decision"] == "pending"


def test_evidence_catalog_cannot_invent_a_quote_even_when_review_is_pending(tmp_path):
    original = ROOT / "data/hus/evaluation/holdout_v2_review/evidence_catalog.jsonl"
    catalog = [json.loads(line) for line in original.read_text(encoding="utf-8").splitlines()]
    catalog[0]["value"] = "fabricated source quote"
    path = tmp_path / "catalog.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in catalog), encoding="utf-8")
    with pytest.raises(ValueError, match="source value"):
        module().validate_reviews(evidence_catalog_path=path)


def test_name_only_alternative_is_bound_to_the_gold_course_not_just_major_version():
    from tools.validate_hus_holdout import pointer, rows

    pack = ROOT / "data/hus/evaluation/holdout_v2_candidate"
    questions, gold = rows(pack / "questions.jsonl"), rows(pack / "gold.jsonl")
    catalog = rows(ROOT / "data/hus/evaluation/holdout_v2_review/evidence_catalog.jsonl")
    item = next(row for row in catalog if row["source_ref"]["path"].endswith("f2_records.jsonl"))
    source_rows = rows(ROOT / item["source_ref"]["path"])
    other = next(row for row in source_rows if row["major"] == item["major"]
                 and row["record_id"] != item["source_ref"]["identity"])
    item["source_ref"]["identity"] = other["record_id"]
    item["value"] = pointer(other, item["source_ref"]["json_pointer"])
    item["citation"] = other["citation"]
    item["review_status"] = other["catalog_review"]["status"]
    for question in questions:
        question["request"]["question"] = "Synthetic name-only question without a course code"
    with pytest.raises(ValueError, match="anchor course"):
        module().validate_catalog(pack, questions, gold, {item["evidence_id"]: item})
