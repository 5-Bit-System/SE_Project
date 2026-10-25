"""Proposals do not grant scope; verified applicability must be tied to real source spans."""

from datetime import date
import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.hus.cleaning import infer_major
from app.hus.corpus import BuildConfig, ReviewFile, SourceManifest, build_artifacts, read_json
from app.hus.index import HUSIndex, chunk_document
from app.hus.metadata import (
    ApplicabilityFile, assign_proposal, locator, metadata_for, propose_metadata, validate_metadata,
)
from app.hus.models import HUSDocument, MajorCategory, MetadataField
from tests.hus_review_fixtures import approved_review
from tools.propose_hus_metadata import main as propose_main


def source(title="Ngành Khoa học dữ liệu", url="https://mim.hus.vnu.edu.vn/vi/news", content="Nội dung nguồn giả lập."):
    return HUSDocument(url=url, title=title, content=content,
                       content_hash=hashlib.sha256(content.encode()).hexdigest(),
                       fetched_at="2026-10-26T00:00:00Z")


def reviewed_major(doc):
    metadata = propose_metadata(doc)
    metadata.major = metadata.major.model_copy(update={
        "verified": "data_science", "evidence": [locator("title", doc.title)],
        "reviewer": "synthetic-reviewer", "reviewed_at": "2026-10-26T00:00:00Z",
    })
    return metadata


@pytest.mark.parametrize("path,title", [
    ("dia-chat", "Quản lý, Công nghệ Tài nguyên môi trường và Địa chất"),
    ("dia-ly", "Địa lý, Quản lý đất đai và GISc"),
])
def test_outside_program_pages_override_menu_and_incidental_math(path, title, tmp_path):
    url = f"https://hus.vnu.edu.vn/dao-tao/bac-dai-hoc/{path}"
    content = "[Toán học](/toan-hoc)\nSinh viên ngành Toán học. Áp dụng cho tất cả sinh viên toàn trường."
    doc = source(title, url, content)
    assert infer_major(title, url, content) == MajorCategory.OUT_OF_SCOPE
    assert metadata_for(doc).major.proposed == "out_of_scope"
    raw = b"synthetic source"
    review = approved_review(doc, raw)
    with pytest.raises(ValueError, match="outside"):
        chunk_document(doc, raw=raw, review=review)
    index = HUSIndex(tmp_path / "index.json", tmp_path / "raw")
    with pytest.raises(ValueError, match="outside"):
        index.add(doc, raw, review=review)
    index.save()
    assert index.documents == {}


def test_unknown_is_not_general_and_query_menu_cannot_supply_major():
    url = "https://mim.hus.vnu.edu.vn/vi/unclassified?next=/toan-hoc"
    assert infer_major("Thông tin", url, "[Ngành Toán học](/vi/toan-hoc)") == MajorCategory.UNKNOWN
    assert infer_major("Thông tin", url, "Quy chế áp dụng cho tất cả sinh viên toàn trường.") == MajorCategory.GENERAL
    assert source("Thông tin", url, "Chưa rõ.").major == MajorCategory.UNKNOWN


def test_verified_metadata_is_not_created_from_classification_or_fetch_date():
    doc = source("Chương trình thạc sĩ, khóa K68, năm học 2025–2026")
    metadata = propose_metadata(doc)
    assert metadata.education_level.proposed == "master"
    assert metadata.admission_cohort.proposed == "K68"
    assert metadata.academic_year.proposed == "2025–2026"
    assert metadata.education_level.verified == metadata.academic_year.verified == "unknown"
    assert metadata.program.verified == metadata.effective_from.verified == "unknown"
    assert propose_metadata(source("Thông tin 2026")).academic_year.proposed == "unknown"


@pytest.mark.parametrize("missing", ["reviewer", "reviewed_at", "evidence"])
def test_every_verified_value_needs_reviewer_time_and_evidence(missing):
    values = dict(verified="master", reviewer="synthetic-reviewer", reviewed_at="2026-10-26T00:00:00Z",
                  evidence=[dict(field="title", start=0, end=3, quote="ABC")])
    values.pop(missing)
    with pytest.raises(ValidationError, match="Verified metadata"):
        MetadataField(**values)


@pytest.mark.parametrize("tamper", ["quote", "offset", "end_outside_source", "hash", "url", "naive_time", "vocabulary"])
def test_verified_metadata_cannot_outlive_its_source_or_use_fake_locators(tamper):
    doc = source()
    metadata = reviewed_major(doc).model_dump()
    if tamper == "quote":
        metadata["major"]["evidence"][0]["quote"] = "Not in the source"
    elif tamper == "offset":
        metadata["major"]["evidence"][0]["start"] = 1
    elif tamper == "end_outside_source":
        metadata["major"]["evidence"][0]["end"] += 100
    elif tamper == "hash":
        metadata["content_hash"] = "0" * 64
    elif tamper == "url":
        metadata["source_url"] = "https://mim.hus.vnu.edu.vn/vi/other"
    elif tamper == "naive_time":
        metadata["major"]["reviewed_at"] = "2026-10-26T00:00:00"
    else:
        metadata["major"]["verified"] = "made_up_major"
    with pytest.raises(ValueError):
        HUSDocument.model_validate({**doc.model_dump(), "applicability": metadata})


def test_reproposal_preserves_review_but_not_after_source_changes():
    doc = source()
    doc.applicability = validate_metadata(doc, reviewed_major(doc))
    assign_proposal(doc)
    assert doc.applicability.major.verified == "data_science"
    assert doc.applicability.major.reviewer == "synthetic-reviewer"
    doc.content_markdown = "Changed source"
    doc.content_hash = hashlib.sha256(doc.content.encode()).hexdigest()
    with pytest.raises(ValueError, match="different source"):
        assign_proposal(doc)


def test_index_exports_only_verified_applicability_without_promoting_proposals(tmp_path):
    raw = b"synthetic raw"
    doc = source()
    index = HUSIndex(tmp_path / "index.json", tmp_path / "raw")
    index.add(doc, raw, review=approved_review(doc, raw))
    chunk = index.documents[doc.url]["chunks"][0]
    assert index.documents[doc.url]["major"] == "unknown"
    assert chunk["applicability"]["major"]["proposed"] == "data_science"
    assert chunk["applicability"]["major"]["verified"] == "unknown"
    doc.applicability = reviewed_major(doc)
    index.add(doc, raw, review=approved_review(doc, raw))
    index.save()
    chunk = index.documents[doc.url]["chunks"][0]
    assert index.documents[doc.url]["major"] == "data_science"
    assert chunk["applicability"]["major"]["verified"] == "data_science"
    doc.applicability.major.reviewed_at = "2026-10-27T00:00:00Z"
    with pytest.raises(ValueError, match="later than as_of"):
        chunk_document(doc, raw=raw, review=approved_review(doc, raw), as_of=date(2026, 10, 26))


def test_checked_in_metadata_repairs_effective_scope_without_rewriting_snapshot(tmp_path):
    root = Path(__file__).resolve().parents[2] / "data/hus"
    config_dir = root / "corpus"
    original = (root / "processed/catalog.json").read_bytes()
    out = tmp_path / "proposed.json"
    assert propose_main(["--source-root", str(root), "--manifest", str(config_dir / "source_manifest.json"),
                         "--out", str(out)]) == 0
    with pytest.raises(SystemExit) as error:
        propose_main(["--source-root", str(root), "--manifest", str(config_dir / "source_manifest.json"),
                      "--out", str(out)])
    assert error.value.code == 1
    assert (root / "processed/catalog.json").read_bytes() == original
    metadata = ApplicabilityFile.model_validate(read_json(config_dir / "applicability.json"))
    for key in ("d73edbb5ad3fc8e5", "741abe805f966790"):
        assert metadata.documents[key].major.proposed == "out_of_scope"
        assert metadata.documents[key].major.verified == "unknown"
    artifacts = build_artifacts(root, SourceManifest.model_validate(read_json(config_dir / "source_manifest.json")),
                                ReviewFile.model_validate(read_json(config_dir / "review_decisions.json")),
                                BuildConfig.model_validate(read_json(config_dir / "build_config.json")), metadata)
    rows = {row["document_id"]: row for row in map(json.loads, artifacts["inventory.jsonl"].splitlines())}
    for key in ("d73edbb5ad3fc8e5", "741abe805f966790"):
        assert rows[key]["major"] == "unknown"
        assert rows[key]["proposed_major"] == "out_of_scope"
        assert rows[key]["legacy_crawler_major"] == "mathematics"
        assert "outside_supported_majors" in rows[key]["flags"]


def test_multiple_education_levels_are_not_collapsed_to_one():
    metadata = propose_metadata(source("Thông tin đào tạo thạc sĩ và tiến sĩ"))
    assert metadata.education_level.proposed == "unknown"
    assert metadata.education_level.verified == "unknown"
    assert len(metadata.education_level.proposal_evidence) == 2


def test_discovery_preserves_review_for_same_source_but_rebuilds_on_title_change(tmp_path):
    from app.hus.storage import ProcessedStorage

    doc = source()
    doc.applicability = reviewed_major(doc)
    storage = ProcessedStorage(tmp_path)
    key = storage.save_document(doc)
    same_source = source()
    assert storage.refresh_discovery(key, same_source) is True
    assert storage.documents[key]["applicability"]["major"]["verified"] == "data_science"
    changed_title = source("Địa lý, Quản lý đất đai và GISc")
    assert storage.refresh_discovery(key, changed_title) is False


def test_parent_inheritance_is_a_proposal_not_proof_of_applicability():
    doc = source("Attachment", "https://mim.hus.vnu.edu.vn/files/guide.pdf", "Unknown scope.")
    doc.parent_url = "https://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu"
    metadata = propose_metadata(doc, MajorCategory.DATA_SCIENCE)
    assert metadata.major.proposed == "data_science"
    assert metadata.major.verified == "unknown"
    assert metadata.major.proposal_method == "parent_inheritance"
    assert metadata.major.proposal_evidence[0].field == "parent_url"
    with pytest.raises(ValueError, match="document itself"):
        MetadataField(verified="data_science", reviewer="synthetic-reviewer",
                      reviewed_at="2026-10-26T00:00:00Z", evidence=metadata.major.proposal_evidence)


def test_configured_metadata_cannot_be_silently_skipped_by_build_api():
    root = Path(__file__).resolve().parents[2] / "data/hus"
    p = root / "corpus"
    with pytest.raises(ValueError, match="Configured applicability"):
        build_artifacts(root, SourceManifest.model_validate(read_json(p / "source_manifest.json")),
                        ReviewFile.model_validate(read_json(p / "review_decisions.json")),
                        BuildConfig.model_validate(read_json(p / "build_config.json")))
