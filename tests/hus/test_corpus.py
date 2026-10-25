"""Source integrity, deterministic builds, and explicit corpus review boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.hus.corpus import (
    BuildConfig, CorpusError, build_artifacts, create_source_manifest,
    initial_reviews, json_bytes, normalize, sha256, source_path, split_chunks,
    verify_artifacts,
)
from tools.prepare_hus_corpus import main


@pytest.fixture
def snapshot(tmp_path):
    root = tmp_path / "source"
    (root / "processed/documents/general").mkdir(parents=True)
    (root / "raw/html/general").mkdir(parents=True)
    documents = {}
    for i, status in enumerate(("active", "pending_ocr")):
        key = str(i + 1) + "0" * 15
        url = f"https://mim.hus.vnu.edu.vn/vi/synthetic-{i}"
        text = ("# Synthetic fixture\n\n" + "Nội dung giả lập, không phải nguồn học vụ.\n" * 15).strip()
        documents[key] = {
            "document_id": key, "source_url": url, "title": "Synthetic fixture",
            "content_markdown": text, "content_hash": sha256(text.encode()),
            "fetched_at": "2026-10-25T00:00:00Z", "status": status,
        }
        (root / f"processed/documents/general/fixture--{key[:8]}.md").write_bytes(
            f"---\ntitle: Synthetic fixture\n---\n\n{text}".encode()
        )
        raw_name = hashlib.sha1(url.encode()).hexdigest()[:12]
        (root / f"raw/html/general/fixture--{raw_name}.html").write_bytes(
            b"<article>Synthetic source, not academic evidence.</article>\n"
        )
    (root / "processed/catalog.json").write_bytes(json_bytes({
        "document_count": len(documents), "documents": documents,
    }))
    manifest = create_source_manifest(root, "synthetic-v1", "fixture://synthetic-v1")
    reviews = initial_reviews(root, manifest)
    config = BuildConfig(
        schema_version="1.0", pipeline_version="1.1", source_manifest="source_manifest.json",
        review_decisions="review_decisions.json", normalization="nfc-lf-trim-trailing-v1",
        chunking="utf8-lines-v1", max_chunk_bytes=128, overlap_bytes=0,
    )
    return root, manifest, reviews, config


def approve_first(manifest, reviews):
    key = "1000000000000000"
    decision = reviews.decisions[key]
    source = manifest.documents[key]
    decision.status = "include"
    decision.source_url = source.source_url
    decision.reason = "Synthetic source reviewed for test only"
    decision.reviewer = "synthetic-reviewer"
    decision.reviewed_at = "2026-10-26T00:00:00Z"
    decision.source_checksum_encoding = "utf8-lf"
    decision.evidence_locator = "article, synthetic fixture"
    decision.reviewed_source_sha256 = next(
        f.sha256 for f in manifest.files if f.path == source.raw_path
    )


def test_reproduction_after_relocation_and_windows_line_endings(snapshot, tmp_path):
    root, manifest, reviews, config = snapshot
    approve_first(manifest, reviews)
    first = build_artifacts(root, manifest, reviews, config)
    import shutil

    relocated = tmp_path / "other-machine"
    shutil.copytree(root, relocated)
    for source in manifest.files:
        path = relocated / source.path
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert build_artifacts(relocated, manifest, reviews, config) == first
    out = tmp_path / "build"
    for name, data in first.items():
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_bytes(data)
    verify_artifacts(out, first)
    (out / "chunks.jsonl").write_bytes(b"tampered\n")
    with pytest.raises(CorpusError, match="differs"):
        verify_artifacts(out, first)


def test_review_queue_does_not_promote_crawler_active(snapshot):
    root, manifest, reviews, config = snapshot
    artifacts = build_artifacts(root, manifest, reviews, config)
    report = json.loads(artifacts["validation_report.json"])
    assert report["review_counts"] == {
        "include": 0, "needs_review": 1, "pending_ocr": 1, "exclude": 0,
    }
    assert artifacts["documents.jsonl"] == artifacts["chunks.jsonl"] == b""


def test_approved_chunks_keep_unicode_and_source_mapping(snapshot):
    root, manifest, reviews, config = snapshot
    approve_first(manifest, reviews)
    artifacts = build_artifacts(root, manifest, reviews, config)
    chunks = [json.loads(line) for line in artifacts["chunks.jsonl"].splitlines()]
    maps = [json.loads(line) for line in artifacts["source_map.jsonl"].splitlines()]
    text = artifacts["normalized/1000000000000000.md"].decode()
    assert len(chunks) > 1
    assert "".join(c["text"] for c in chunks) == text
    assert {c["document_id"] for c in chunks} == {"1000000000000000"}
    assert {c["chunk_id"] for c in chunks} == {m["chunk_id"] for m in maps}
    for chunk in chunks:
        assert len(chunk["text"].encode()) <= 128
        locator = chunk["locator"]
        assert text[locator["start_char"]:locator["end_char"]] == chunk["text"]


@pytest.mark.parametrize("change", ["missing", "changed", "stale_review", "missing_decision",
                                     "wrong_snapshot", "ocr_include", "no_evidence", "wrong_raw_hash"])
def test_reject_invalid_inputs_and_review(snapshot, change):
    root, manifest, reviews, config = snapshot
    if change == "missing":
        (root / manifest.files[0].path).unlink()
    elif change == "changed":
        (root / manifest.files[0].path).write_bytes(b"changed source")
    elif change == "stale_review":
        reviews.decisions["1000000000000000"].content_hash = "0" * 64
    elif change == "missing_decision":
        reviews.decisions.pop("1000000000000000")
    elif change == "wrong_snapshot":
        reviews.source_snapshot_id = "different-snapshot"
    elif change == "ocr_include":
        reviews.decisions["2000000000000000"].status = "include"
    elif change == "wrong_raw_hash":
        approve_first(manifest, reviews)
        reviews.decisions["1000000000000000"].reviewed_source_sha256 = "0" * 64
    else:
        reviews.decisions["1000000000000000"].status = "include"
    with pytest.raises(CorpusError):
        build_artifacts(root, manifest, reviews, config)


def test_missing_attachment_is_an_explicit_blocker(snapshot):
    root, manifest, reviews, config = snapshot
    source = manifest.documents["1000000000000000"]
    missing_path = source.raw_path
    source.raw_path = None
    source.source_kind = "attachment"
    manifest.files = [f for f in manifest.files if f.path != missing_path]
    artifacts = build_artifacts(root, manifest, reviews, config)
    first = json.loads(artifacts["inventory.jsonl"].splitlines()[0])
    assert "original_attachment_missing" in first["flags"]
    assert first["raw_path"] is None
    reviews.decisions["1000000000000000"].status = "include"
    with pytest.raises(CorpusError, match="Include lacks"):
        build_artifacts(root, manifest, reviews, config)


@pytest.mark.parametrize("name", ["../secret", "C:/secret", "raw/../../secret", "/secret",
                                  "raw\\secret", "raw//file"])
def test_manifest_paths_cannot_escape_root(tmp_path, name):
    with pytest.raises(CorpusError):
        source_path(tmp_path, name)


def test_binary_checksums_are_not_line_ending_normalized(tmp_path):
    from app.hus.corpus import file_bytes

    path = tmp_path / "source.pdf"
    path.write_bytes(b"%PDF\r\n")
    assert file_bytes(path, "binary") == b"%PDF\r\n"


def test_long_unicode_line_chunks_have_lossless_byte_limits():
    text = normalize("\n" + "điều kiện 🎓 " * 80 + "  \r\n")
    spans = split_chunks(text, 128)
    assert "".join(text[a:b] for a, b in spans) == text
    assert all(len(text[a:b].encode()) <= 128 for a, b in spans)


def test_cli_build_verify_refuse_overwrite_and_source_output(snapshot, tmp_path, capsys):
    root, manifest, reviews, config = snapshot
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    for name, value in [("source_manifest.json", manifest), ("review_decisions.json", reviews),
                        ("build_config.json", config)]:
        (config_dir / name).write_bytes(json_bytes(value.model_dump()))
    args = ["--source-root", str(root), "--config", str(config_dir / "build_config.json"),
            "--out", str(tmp_path / "build")]
    assert main(["build", *args]) == 0
    assert main(["verify", *args]) == 0
    assert main(["build", *args]) == 1
    assert "already exists" in capsys.readouterr().err
    args[-1] = str(root / "build")
    assert main(["build", *args]) == 1
    assert not (root / "build").exists()


def test_production_snapshot_reproduces_without_local_backups():
    """Acceptance uses the checked-in snapshot contract, not build07 or a local database."""
    from app.hus.corpus import ReviewFile, SourceManifest, read_json

    root = Path(__file__).resolve().parents[2] / "data/hus"
    config_dir = root / "corpus"
    config = BuildConfig.model_validate(read_json(config_dir / "build_config.json"))
    manifest = SourceManifest.model_validate(read_json(config_dir / config.source_manifest))
    reviews = ReviewFile.model_validate(read_json(config_dir / config.review_decisions))
    artifacts = build_artifacts(root, manifest, reviews, config)
    report = json.loads(artifacts["validation_report.json"])
    assert report["document_count"] == 106
    assert report["review_counts"] == {
        "include": 0, "needs_review": 100, "pending_ocr": 6, "exclude": 0,
    }
    assert report["flag_counts"]["original_attachment_missing"] == 51
    assert report["source_files_verified"] == 162
    assert report["active_release"] is False
    assert json.loads((config_dir / "baseline_validation_report.json").read_text(encoding="utf-8")) == report
    assert json.loads(artifacts["manifest.json"]) == read_json(config_dir / "baseline_build_manifest.json")


def test_repinning_does_not_hide_markdown_catalog_divergence(snapshot):
    root, manifest, reviews, config = snapshot
    path = root / manifest.documents["1000000000000000"].markdown_path
    path.write_bytes(path.read_bytes() + b"changed meaning")
    manifest = create_source_manifest(root, "synthetic-v1", "fixture://synthetic-v1")
    with pytest.raises(CorpusError, match="Markdown body"):
        build_artifacts(root, manifest, reviews, config)


@pytest.mark.parametrize("update", [
    {"reviewed_at": None}, {"reviewed_at": "2026-10-26T00:00:00"},
    {"source_checksum_encoding": "binary"}, {"usage_scope": "current"},
])
def test_corpus_uses_the_same_review_gate(snapshot, update):
    root, manifest, reviews, config = snapshot
    approve_first(manifest, reviews)
    decision = reviews.decisions["1000000000000000"]
    reviews.decisions["1000000000000000"] = decision.model_copy(update=update)
    with pytest.raises(CorpusError, match="Include lacks"):
        build_artifacts(root, manifest, reviews, config)


def test_corpus_checks_current_validity_at_build_date(snapshot):
    root, manifest, reviews, config = snapshot
    approve_first(manifest, reviews)
    decision = reviews.decisions["1000000000000000"]
    decision.usage_scope = "current"
    decision.validity_status = "current_verified"
    decision.validity_evidence_locator = "Synthetic section on effective dates"
    decision.effective_from = "2026-10-26"
    decision.effective_to = "2026-10-27"
    with pytest.raises(CorpusError):
        build_artifacts(root, manifest, reviews, config)
    config.as_of = "2026-10-26"
    artifacts = build_artifacts(root, manifest, reviews, config)
    assert json.loads(artifacts["validation_report.json"])["included_documents"] == 1
    config.as_of = "2026-10-28"
    with pytest.raises(CorpusError):
        build_artifacts(root, manifest, reviews, config)
