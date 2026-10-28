"""F1 quote provenance and whole-document review boundaries across the expanded crawl set."""

import json
from pathlib import Path

import pytest

from app.hus.corpus import load_catalog, verify_artifacts
from app.hus.f1_corpus import build_f1, selected_spans

ROOT = Path("data/hus/qa/20261028/f1_expanded")


@pytest.fixture(scope="module")
def built():
    return build_f1(Path("data/hus"), ROOT / "contract/build_config.json", ROOT / "contract/selections.json")


def rows(built, name):
    return [json.loads(line) for line in built[name].splitlines()]


def test_all_F1_units_are_exact_crawled_quotes_from_reviewed_whole_documents(built):
    docs = load_catalog(Path("data/hus"))
    units = rows(built, "f1_units.jsonl")
    assert len({u["document_id"] for u in units}) == 5
    assert len(units) == 42
    for u in units:
        d, loc = docs[u["document_id"]], u["locator"]
        assert d.content[loc["start_char"]:loc["end_char"]] == u["text"]
        assert u["source_content_hash"] == d.content_hash
        assert u["content_origin"] == "crawled_source_quote"
        assert u["review_scope"] == "whole_document" and u["review_status"] == "include"
        assert u["review"]["reviewed_source_sha256"] == u["raw_sha256"]
        assert u["usage_scope"] == "descriptive" and u["validity_status"] == "unknown"


def test_expansion_keeps_both_4_major_coverage_and_distinct_CLC_talent_scopes(built):
    units = rows(built, "f1_units.jsonl")
    assert {u["major"] for u in units} == {"mathematics", "mathematics_informatics", "data_science", "computer_science"}
    clc = [u for u in units if u["document_id"] == "f8672cafba05d016"]
    assert clc and all(u["program_variant"] == "high_quality" and u["major"] == "computer_science" for u in clc)
    talent = [u for u in units if u["program_variant"] == "talent"]
    assert talent and all(u["major"] == "mathematics" for u in talent)
    assert all(u["program_version"] == "unknown" and u["admission_cohort"] == "unknown" for u in units)


def test_no_duplicate_overlapping_source_spans_or_discovery_links(built):
    units = rows(built, "f1_units.jsonl")
    assert len({u["unit_id"] for u in units}) == len(units)
    for a in units:
        assert "](" not in a["text"]
        for b in units:
            if a is b or a["document_id"] != b["document_id"]:
                continue
            x, y = a["locator"], b["locator"]
            assert not (x["start_char"] < y["end_char"] and y["start_char"] < x["end_char"])


def test_every_RAG_chunk_keeps_source_citation_and_exact_quote(built):
    units = {u["unit_id"]: u for u in rows(built, "f1_units.jsonl")}
    chunks = rows(built, "rag_chunks.jsonl")
    assert len(chunks) == 42
    assert len({c["chunk_id"] for c in chunks}) == len(chunks)
    for c in chunks:
        assert c["text"].endswith(units[c["unit_id"]]["text"])
        assert c["source_quote"] == units[c["unit_id"]]["text"]
        assert c["source_url"].startswith("http://mim.hus.vnu.edu.vn/")
        assert "chưa xác minh" in c["text"]


def test_missing_originals_mixed_major_and_course_goals_stay_outside_F1_answers(built):
    inventory = {r["document_id"]: r for r in rows(built, "source_inventory.jsonl")}
    assert len(inventory) == 106
    assert inventory["1f6ad01008734152"]["disposition"] == "quarantine"
    assert not inventory["1f6ad01008734152"]["answer_eligible"]
    for key in ("bc0a1f59b7ab202c", "098df9e79c1391af"):
        assert inventory[key]["reason"] == "course_level_objectives_are_F3_not_program_F1"
    pending = rows(built, "pending_F1_sections.jsonl")
    assert len({p["document_id"] for p in pending}) == 11
    assert all(not p["answer_eligible"] for p in pending)
    answer_ids = {d["document_id"] for d in rows(built, "documents.jsonl")}
    assert not answer_ids & {p["document_id"] for p in pending}
    docs = load_catalog(Path("data/hus"))
    for p in pending:
        assert docs[p["document_id"]].content[p["start"]:p["end"]] == p["quote"]


def test_sentence_split_preserves_abbreviations_and_lowercase_continuations():
    text = "Nghiên cứu mô hình v.v. đến các công cụ tính toán. Sinh viên ứng dụng kết quả."
    spans = selected_spans(text, {"line": 0, "split": "sentences"})
    assert [text[a:b] for a, b in spans] == [
        "Nghiên cứu mô hình v.v. đến các công cụ tính toán.", "Sinh viên ứng dụng kết quả."]


def test_unknown_split_method_rejected():
    with pytest.raises(ValueError):
        selected_spans("A source paragraph.", {"line": 0, "split": "invent_text"})


def test_independent_release_reproduces_and_prior_F1_and_F3_artifacts_remain(built):
    verify_artifacts(ROOT / "release", built)
    original = Path("data/hus/qa/20261028/audit/answer_chunks.jsonl").read_text(encoding="utf-8")
    assert len(original.splitlines()) == 8
    generated = json.loads(Path("data/hus/qa/20261028/f3_reference/release/manifest.json").read_text(encoding="utf-8"))
    assert generated["rag_chunks"] == 870
    assert all(q["result"] == "pass" for q in rows(built, "acceptance_questions.jsonl"))
