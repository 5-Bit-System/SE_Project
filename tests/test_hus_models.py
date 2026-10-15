import pytest
from pydantic import ValidationError

from app.hus.models import (
    AllowlistSourceConfig,
    CrawlRecord,
    DocumentStatus,
    DocumentType,
    HUSAttachment,
    HUSDocument,
    Publisher,
)


def test_models_serialization():
    doc = HUSDocument(
        url="https://mim.hus.vnu.edu.vn/vi/dao-tao",
        title="Đào tạo Khoa Toán",
        content="Nội dung đào tạo",
        content_hash="abc123hash",
        fetched_at="2026-10-15T22:00:00Z",
        published_at="2026-10-14",
        document_type=DocumentType.CURRICULUM,
        publisher=Publisher.MIM,
        status=DocumentStatus.ACTIVE,
    )
    assert doc.url == "https://mim.hus.vnu.edu.vn/vi/dao-tao"
    assert doc.document_type == DocumentType.CURRICULUM
    assert doc.publisher == Publisher.MIM
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


def test_models_validation_error():
    with pytest.raises(ValidationError):
        # Missing required content_hash, content, etc.
        HUSDocument(url="https://example.com", title="Test")


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
