"""Explicit Markdown approval is scoped, hash-bound and never original-PDF verification."""

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.hus.corpus import SourceManifest, load_catalog, read_json, verify_artifacts
from app.hus.f1_markdown_review import (
    AUTHORIZED_IDS, EXCLUDED_ID, MarkdownReviewFile, apply_markdown_review,
    build_f1_with_markdown, clean_display,
)
from app.hus.models import ReviewDecision

ROOT = Path("data/hus")
BASE = ROOT / "qa/20261028/f1_expanded"
CURRENT = ROOT / "qa/20261028/f1_markdown_approved"
REVIEW_PATH = CURRENT / "contract/markdown_review_decisions.json"


def rows(artifacts, name):
    return [json.loads(line) for line in artifacts[name].splitlines() if line.strip()]


@pytest.fixture(scope="module")
def built():
    return build_f1_with_markdown(ROOT, BASE / "contract/build_config.json",
                                  BASE / "contract/selections.json", REVIEW_PATH)


def test_ten_authorized_documents_are_accepted_and_careers_page_is_dropped(built):
    docs = rows(built, "documents.jsonl")
    assert len(docs) == 15
    accepted = {d["document_id"] for d in docs if d["review_status"] == "include_markdown"}
    assert accepted == AUTHORIZED_IDS and len(accepted) == 10
    assert EXCLUDED_ID not in {d["document_id"] for d in docs}
    assert built["pending_F1_sections.jsonl"] == b""
    inventory = {r["document_id"]: r for r in rows(built, "source_inventory.jsonl")}
    assert len(inventory) == 106
    assert inventory[EXCLUDED_ID]["disposition"] == "excluded_from_F1"
    assert inventory[EXCLUDED_ID]["reason"] == "user_requested_remove_mixed_Toan_Co_careers_page"
    assert sum(r["answer_eligible"] for r in inventory.values()) == 15


def test_markdown_approval_keeps_exact_source_quotes_and_does_not_claim_raw_verified(built):
    docs = load_catalog(ROOT)
    chunks = rows(built, "rag_chunks.jsonl")
    assert len(chunks) == 69
    assert len({c["chunk_id"] for c in chunks}) == 69
    for c in chunks:
        if c["review_status"] != "include_markdown":
            continue
        loc = c["locator"]
        assert c["source_quote"] == docs[c["document_id"]].content[loc["start_char"]:loc["end_char"]]
        assert c["text"].endswith(clean_display(c["source_quote"]))
        assert c["review_basis"] == "extracted_markdown" and c["review_scope"] == "selected_F1_sections"
        assert c["raw_original_verified"] is False and c["academic_verified"] is False
        assert c["raw_sha256"] is None
        assert c["program_version"] == c["review"]["version_as_stated_in_markdown"]
        assert c["admission_cohort"] == "unknown" and c["validity_status"] == "unknown"
        assert "chưa đối chiếu PDF/DOCX gốc" in c["text"]
        assert not any(line.lstrip().startswith("|") for line in c["source_quote"].splitlines())
        assert "PHẦN III" not in c["source_quote"]


def test_identical_CLC_narratives_do_not_get_duplicate_retrieval_weight(built):
    units = rows(built, "f1_units.jsonl")
    assert len(units) == 66
    duplicate = [u for u in units if u.get("retrieval_duplicate_of")]
    assert len(duplicate) == 3
    assert {u["document_id"] for u in duplicate} == {"8afffd3cada3d048"}
    chunks = rows(built, "rag_chunks.jsonl")
    assert not any(c["document_id"] == "8afffd3cada3d048" for c in chunks)
    assert any(any(p["document_id"] == "8afffd3cada3d048" for p in c.get("alternate_source_provenance", [])) for c in chunks)
    assert {u["program_version"] for u in duplicate} == {"2019"}


def test_further_study_spans_do_not_import_old_F2_credit_tables(built):
    for u in rows(built, "f1_units.jsonl"):
        if u["review_status"] == "include_markdown":
            assert "PHẦN III" not in u["source_quote"]
            assert "Khung ch" not in u["source_quote"]
    for key in ("23a0c1df14a5708a", "1e3ad5f9915aa051"):
        study = next(u for u in rows(built, "f1_units.jsonl") if u["document_id"] == key and u["field"] == "further_study")
        assert len(study["source_quote"]) == 200


@pytest.mark.parametrize("field", ["raw_original_verified", "current_validity_verified"])
def test_review_cannot_invent_original_or_current_verification(field):
    data = read_json(REVIEW_PATH)
    data["decisions"]["23a0c1df14a5708a"][field] = True
    with pytest.raises(ValidationError):
        MarkdownReviewFile.model_validate(data)


def test_original_review_gate_and_base_release_are_not_reclassified():
    decisions = read_json(ROOT / "corpus/review_decisions.json")["decisions"]
    assert all(decisions[k]["status"] == "needs_review" for k in AUTHORIZED_IDS)
    markdown = read_json(REVIEW_PATH)["decisions"]["23a0c1df14a5708a"]
    with pytest.raises(ValidationError):
        ReviewDecision.model_validate(markdown)
    original = read_json(BASE / "release/manifest.json")
    assert original["source_documents"] == 5 and original["rag_chunks"] == 42


@pytest.mark.parametrize("mutation", ["excluded_source", "missing_source", "stale_hash", "foreign_major", "overlap", "stale_quote"])
def test_bad_markdown_approvals_fail_closed(mutation):
    data = copy.deepcopy(read_json(REVIEW_PATH))
    key = "23a0c1df14a5708a"
    if mutation == "excluded_source":
        data["decisions"][EXCLUDED_ID] = data["decisions"][key]
    elif mutation == "missing_source":
        del data["decisions"][key]
    elif mutation == "stale_hash":
        data["decisions"][key]["source_content_hash"] = "0" * 64
    elif mutation == "foreign_major":
        data["decisions"][key]["major"] = "data_science"
    elif mutation == "overlap":
        data["decisions"][key]["sections"].append(data["decisions"][key]["sections"][0])
    else:
        data["decisions"][key]["sections"][0]["quote_sha256"] = "0" * 64
    decision = MarkdownReviewFile.model_validate(data)
    base = {p.name: p.read_bytes() for p in (BASE / "release").iterdir() if p.is_file()}
    manifest = SourceManifest.model_validate(read_json(ROOT / "corpus/source_manifest.json"))
    with pytest.raises(ValueError):
        apply_markdown_review(base, load_catalog(ROOT), manifest, ROOT, decision)


def test_display_cleanup_preserves_words_and_extraction_glyphs():
    text = "Mục tiêu chƣơng trình\n12\n<!-- Page 13 -->\nNội dung được giữ nguyên."
    assert clean_display(text) == "Mục tiêu chƣơng trình\nNội dung được giữ nguyên."


def test_current_release_is_reproducible_and_question_contracts_hold(built):
    verify_artifacts(CURRENT / "release", built)
    assert all(q["result"] == "pass" for q in rows(built, "acceptance_questions.jsonl"))
    m = json.loads(built["manifest.json"])
    assert m["source_documents_markdown_reviewed"] == 10 and m["source_documents_raw_compared"] == 5
    assert m["pending_source_documents"] == m["pending_sections"] == m["generated_F1_units"] == 0
