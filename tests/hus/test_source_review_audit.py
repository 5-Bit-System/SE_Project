"""Synthetic source-review regressions; never grant academic approval."""

import hashlib
from pathlib import Path

import pytest

from tools.audit_hus_source_review import (
    SourceReviewError,
    audit_candidate,
    audit_span,
    captured_context,
    check_binary_hash,
    page_triage,
    pdf_texts,
    run_audit,
)


def pages():
    return [{"page": number, "raw_sha256": "raw", "text": text,
             "text_sha256": hashlib.sha256(text.encode()).hexdigest()}
            for number, text in [(1, "alpha"), (2, "beta")]]


def span():
    return {"start_char": 0, "end_char": 10, "source_quote": "alpha\nbeta", "pdf_pages": [1, 2],
            "offset_scope": "joined_source_pages_with_one_newline_each"}


def test_hash_mismatch_is_not_a_recovered_original():
    with pytest.raises(SourceReviewError, match="hash"):
        check_binary_hash(b"changed", hashlib.sha256(b"original").hexdigest())


def test_cross_page_quote_has_exact_ownership():
    result = audit_span(span(), captured_context(pages(), "raw"), 2, ["alpha", "beta"])
    assert result["capture_quote_match"] and result["capture_pages_match"]
    assert result["physical_pages_valid"] and result["reextracted_quote_found"]


def test_incorrect_page_cannot_pass_when_quote_matches():
    value = span()
    value["pdf_pages"] = [1]
    result = audit_span(value, captured_context(pages(), "raw"), 2, ["alpha", "beta"])
    assert result["capture_quote_match"] and not result["capture_pages_match"]


def test_quote_or_offset_change_is_reported():
    value = span()
    value.update(start_char=1, source_quote="fabricated")
    result = audit_span(value, captured_context(pages(), "raw"), 2, ["alpha", "beta"])
    assert not result["capture_quote_match"]


def test_capture_hash_and_order_are_checked_before_quotes():
    value = pages()
    value[0]["text"] = "forged"
    with pytest.raises(SourceReviewError, match="text hash"):
        captured_context(value, "raw")
    with pytest.raises(SourceReviewError, match="raw hash"):
        captured_context(pages(), "other")
    with pytest.raises(SourceReviewError, match="contiguous"):
        captured_context([pages()[1]], "raw")


def test_missing_binary_cannot_gain_physical_page_verification():
    result = audit_span(span(), captured_context(pages(), "raw"), None, None)
    assert result["capture_quote_match"]
    assert result["physical_pages_valid"] is None
    assert result["reextracted_quote_found"] is None


def test_low_text_page_is_queued_without_claiming_blank_or_ocr_complete():
    result = page_triage("source", 3, " \n ", False)
    assert result["needs_visual_or_ocr"] is True
    assert result["blank_verified"] is False and result["ocr_completed"] is False
    assert result["review_status"] == "pending"


def test_exact_identity_never_grants_official_f3_or_current_validity():
    candidate = {"candidate_id": "candidate", "document_id": "doc", "raw_sha256": "raw",
                 "source_major": "mathematics_informatics", "source_publication_year": 2021,
                 "declared_curriculum_decision": None, "canonical_record_id": "program:MAT9998",
                 "course_code_as_printed": "MAT9998", "title_as_extracted": "Synthetic course",
                 "identity_issues": [], "fields": {"content": [span()]}}
    record = {"record_id": "program:MAT9998", "major": "mathematics_informatics",
              "course_code": "MAT9998", "course_name": "Synthetic course",
              "scope": {"curriculum_version": "QD2023", "cohort_year": 2022}}
    result = audit_candidate(candidate, captured_context(pages(), "raw"), 2,
                             ["alpha", "beta"], record)
    assert result["identity_link_present"] is True
    assert result["academic_verified"] is False and result["default_retrieval_enabled"] is False
    assert result["current_validity"] == "unverified"
    assert "older_source_edition" in result["blocking_reasons"]


def test_pdfium_page_handles_are_closed_explicitly_for_real_pdf():
    path = Path(__file__).resolve().parents[2] / "tests/fixtures/hus/sample_text.pdf"
    texts = pdf_texts(path.read_bytes())
    assert texts and any(text.strip() for text in texts)


@pytest.mark.parametrize("cache_relative", ["data/hus/citation_assets", "data/hus/rag/releases/unsafe-cache", "data/hus/raw"])
def test_cache_cannot_write_into_runtime_or_source_roots(tmp_path, monkeypatch, cache_relative):
    root = Path(__file__).resolve().parents[2]
    out = root / "backups" / ("p13_path_guard_" + tmp_path.parent.name + "_" + tmp_path.name)
    assert not out.exists()
    original_mkdir = Path.mkdir
    def forbid_output_write(path, *args, **kwargs):
        if path == out:
            raise AssertionError("Path guard must reject before any audit directory write")
        return original_mkdir(path, *args, **kwargs)
    monkeypatch.setattr(Path, "mkdir", forbid_output_write)
    with pytest.raises(SourceReviewError, match="cache"):
        run_audit(out, root / cache_relative)
    assert not out.exists()
