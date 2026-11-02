import pytest
from pydantic import ValidationError

from app.hus.models import (
    AllowlistSourceConfig,
    CrawlRecord,
    DocumentStatus,
    DocumentType,
    HUSAttachment,
    HUSDocument,
    MajorCategory,
    Publisher,
)


def test_models_serialization():
    doc = HUSDocument(
        source_url="https://mim.hus.vnu.edu.vn/vi/dao-tao",
        title="Đào tạo Khoa Toán",
        content_markdown="Nội dung đào tạo",
        content_hash="abc123hash",
        fetched_at="2026-10-15T22:00:00Z",
        published_at="2026-10-14",
        document_type=DocumentType.CURRICULUM,
        publisher=Publisher.MIM,
        major=MajorCategory.MATHEMATICS,
        status=DocumentStatus.ACTIVE,
    )
    assert doc.url == "https://mim.hus.vnu.edu.vn/vi/dao-tao"
    assert doc.document_type == DocumentType.CURRICULUM
    assert doc.publisher == Publisher.MIM
    assert doc.major == MajorCategory.MATHEMATICS
    assert doc.attachments == []

    att = HUSAttachment(
        attachment_id="att-1",
        source_url="https://mim.hus.vnu.edu.vn/file.pdf",
        file_type="pdf",
        file_size=1024,
    )
    doc.attachments.append(att)
    assert len(doc.attachments) == 1
    assert doc.attachments[0].file_type == "pdf"
    payload = doc.model_dump(mode="json")
    assert payload["source_url"] == doc.url
    assert payload["content_markdown"] == doc.content
    assert payload["major"] == "mathematics"
    assert "url" not in payload
    assert "content" not in payload


def test_major_category_defaults_and_validation():
    # Missing applicability is unknown, never silently shared.
    doc_default = HUSDocument(
        source_url="https://mim.hus.vnu.edu.vn/vi/thong-tin-chung",
        title="Quy chế đào tạo",
        content_markdown="Nội dung quy chế",
        content_hash="hash123",
        fetched_at="2026-10-15T22:00:00Z",
    )
    assert doc_default.major == MajorCategory.UNKNOWN

    # Valid string coercion
    doc_ds = HUSDocument(
        source_url="https://mim.hus.vnu.edu.vn/category/khoa-hoc-du-lieu/feed",
        title="Khoa học dữ liệu",
        content_markdown="Nội dung KHDL",
        content_hash="hash456",
        fetched_at="2026-10-15T22:00:00Z",
        major="data_science",  # type: ignore[arg-type]
    )
    assert doc_ds.major == MajorCategory.DATA_SCIENCE

    # Round trip JSON deserialization
    raw_json = doc_ds.model_dump(mode="json")
    deserialized = HUSDocument.model_validate(raw_json)
    assert deserialized.major == MajorCategory.DATA_SCIENCE

    # Invalid major category raises ValidationError
    with pytest.raises(ValidationError):
        HUSDocument(
            source_url="https://mim.hus.vnu.edu.vn/vi/test",
            title="Invalid major test",
            content_markdown="Nội dung",
            content_hash="hash789",
            fetched_at="2026-10-15T22:00:00Z",
            major="invalid_major",  # type: ignore[arg-type]
        )


def test_models_validation_error():
    with pytest.raises(ValidationError):
        # Missing required content_hash, content, etc.
        HUSDocument(url="https://example.com", title="Test")

    valid = {
        "source_url": "https://mim.hus.vnu.edu.vn/vi/dao-tao",
        "title": "Test",
        "content_markdown": "Nội dung",
        "content_hash": "hash",
        "fetched_at": "2026-10-15T22:00:00Z",
    }
    for field, value in (
        ("source_url", "not-a-url"),
        ("source_url", "https://exa mple.com/path"),
        ("source_url", "https://example.com:99999/path"),
        ("content_hash", ""),
        ("fetched_at", "yesterday"),
        ("fetched_at", "2026-10-15"),
        ("published_at", "15/10/2026"),
        ("parent_url", "javascript:alert(1)"),
        ("links", ["not-a-url"]),
    ):
        with pytest.raises(ValidationError):
            HUSDocument(**(valid | {field: value}))

    with pytest.raises(ValidationError):
        CrawlRecord(url="https://mim.hus.vnu.edu.vn/vi", content_hash="", last_crawled="bad")


def test_crawl_record_and_config():
    record = CrawlRecord(
        url="https://mim.hus.vnu.edu.vn/vi",
        content_hash="hash1",
        last_crawled="2026-10-15T22:00:00Z",
    )
    assert record.status_code == 200
    assert record.etag is None

    cfg = AllowlistSourceConfig(
        host="mim.hus.vnu.edu.vn",
        path_prefixes=["/vi/"],
        exclude_prefixes=["/vi/album"],
        seeds=["https://mim.hus.vnu.edu.vn/vi"],
    )
    assert cfg.host == "mim.hus.vnu.edu.vn"
    assert len(cfg.exclude_prefixes) == 1
