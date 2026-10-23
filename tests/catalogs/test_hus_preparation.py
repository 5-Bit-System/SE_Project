"""Checks evidence isolation and lossless preprocessing using invented documents."""

import csv
import json
from pathlib import Path

import pytest

from tools.prepare_hus_corpus import chunk_spans, digest, prepare


def fixture_files(root: Path) -> tuple[Path, Path]:
    snapshot = root / "snapshot"
    (snapshot / "processed/documents").mkdir(parents=True)
    (snapshot / "raw").mkdir()
    docs = {}
    for key, state in [("12345678abcdef00", "active"), ("87654321abcdef00", "pending_ocr")]:
        text = "Synthetic introduction.\nA condition and its exception belong together."
        url = f"https://example.invalid/{key}"
        docs[key] = dict(document_id=key, source_url=url, title=key, content_markdown=text,
                         status=state, document_type="general_info", major="general",
                         parent_url=None, publisher="SYNTHETIC", published_at=None, fetched_at=None)
        (snapshot / f"processed/documents/{key}--{key[:8]}.md").write_text(
            f"---\ntitle: {key}\nurl: {url}\ntype: general_info\nmajor: general\npublisher: SYNTHETIC\n---\n\n{text}\n", encoding="utf-8")
        (snapshot / f"raw/{key}.html").write_text(
            f'<link rel="canonical" href="/{key}"><p>{text}</p>', encoding="utf-8")
    catalog = json.dumps(dict(document_count=2, documents=docs)).encode()
    (snapshot / "processed/catalog.json").write_bytes(catalog)
    (snapshot / "manifest.json").write_text(json.dumps(dict(catalog_sha256=digest(catalog))))
    review = root / "review.json"
    key = "12345678abcdef00"
    review.write_text(json.dumps({key: dict(decision="include", content_sha256=digest(docs[key]["content_markdown"].encode()),
        reviewer="synthetic_test", reviewed_at="2026-01-01", reason="invented",
        evidence="Synthetic introduction.", source_quotes=["Synthetic introduction."],
        document_type="description", scope="general")}), encoding="utf-8")
    return snapshot, review


def test_reproducible_build_isolates_pending_and_preserves_sources(tmp_path):
    snapshot, review = fixture_files(tmp_path)
    first = tmp_path / "build1"
    second = tmp_path / "build2"
    stats = prepare(snapshot, first, review)
    prepare(snapshot, second, review)
    assert stats["documents"] == 1
    assert stats["decisions"]["pending_ocr"] == 1
    assert stats["source_unchanged"]
    assert (first / "manifest.json").read_bytes() == (second / "manifest.json").read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        prepare(snapshot, first, review)


def test_changed_review_content_fails_closed(tmp_path):
    snapshot, review = fixture_files(tmp_path)
    data = json.loads(review.read_text())
    data["12345678abcdef00"]["content_sha256"] = "stale"
    review.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Stale review"):
        prepare(snapshot, tmp_path / "failed", review)


def test_markdown_disagreement_blocks_inclusion(tmp_path):
    snapshot, review = fixture_files(tmp_path)
    md = snapshot / "processed/documents/12345678abcdef00--12345678.md"
    md.write_text(md.read_text() + " changed")
    with pytest.raises(ValueError, match="unresolved checks"):
        prepare(snapshot, tmp_path / "failed", review)


def test_chunking_preserves_whole_oversized_condition():
    text = "Heading\n" + "condition with exception " * 300 + "\nNext paragraph."
    spans = chunk_spans(text, byte_budget=100)
    assert "".join(text[a:b] for a, b in spans) == text
    assert any("condition with exception " * 300 in text[a:b] for a, b in spans)


def test_output_inside_source_snapshot_is_rejected(tmp_path):
    snapshot, review = fixture_files(tmp_path)
    with pytest.raises(ValueError, match="outside the immutable snapshot"):
        prepare(snapshot, snapshot / "build", review)
    assert not (snapshot / "build").exists()


def test_postgraduate_candidate_stays_out_of_answer_corpus(tmp_path):
    snapshot, review = fixture_files(tmp_path)
    data = json.loads(review.read_text(encoding="utf-8"))
    key = "87654321abcdef00"
    data[key] = dict(decision="needs_review", content_sha256=digest(
        "Synthetic introduction.\nA condition and its exception belong together.".encode()),
        reviewer="synthetic_test", reviewed_at="2026-01-01", reason="check source",
        candidate_topic="postgraduate_study", proposed_education_level="master")
    review.write_text(json.dumps(data), encoding="utf-8")
    output = tmp_path / "build"
    stats = prepare(snapshot, output, review)
    with (output / "document_review.csv").open(encoding="utf-8-sig", newline="") as file:
        rows = {row["document_id"]: row for row in csv.DictReader(file)}
    assert stats["decisions"]["needs_review"] == 1
    assert rows[key]["candidate_topic"] == "postgraduate_study"
    assert rows[key]["proposed_education_level"] == "master"
    assert key not in (output / "documents.jsonl").read_text(encoding="utf-8")
    assert key not in (output / "chunks.jsonl").read_text(encoding="utf-8")
