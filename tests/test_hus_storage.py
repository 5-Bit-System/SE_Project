import json
from pathlib import Path
import pytest

from app.hus.models import DocumentType, HUSDocument, Publisher
from app.hus.storage import ProcessedStorage, RawStorage


def test_raw_storage_idempotent(tmp_path: Path):
    storage = RawStorage(tmp_path)
    url = "https://mim.hus.vnu.edu.vn/vi/test"
    raw_html = b"<html><body>Hello</body></html>"

    p1 = storage.save_raw_html(url, raw_html)
    assert p1.exists()
    assert p1.read_bytes() == raw_html

    # Same content does not create another file
    p2 = storage.save_raw_html(url, raw_html)
    assert p1 == p2

    # Save document (pdf)
    p_pdf = storage.save_raw_document("https://mim.hus.vnu.edu.vn/file.pdf", b"%PDF-1.4", "pdf")
    assert p_pdf.exists()
    assert p_pdf.suffix == ".pdf"


def test_processed_storage_atomic_commit(tmp_path: Path):
    storage = ProcessedStorage(tmp_path)
    doc = HUSDocument(
        url="https://mim.hus.vnu.edu.vn/vi/dao-tao",
        title="Quy chế đào tạo",
        content="# Điều 1: Tín chỉ",
        content_hash="hash123",
        fetched_at="2026-10-16T09:00:00Z",
        document_type=DocumentType.REGULATION,
        publisher=Publisher.MIM,
    )
    doc_id = storage.save_document(doc)
    assert doc_id is not None
    md_file = tmp_path / "processed" / "documents" / f"{doc_id}.md"
    assert md_file.exists()
    assert "# Điều 1: Tín chỉ" in md_file.read_text(encoding="utf-8")

    # Before commit, catalog.json might not exist
    storage.commit()
    catalog_file = tmp_path / "processed" / "catalog.json"
    assert catalog_file.exists()

    data = json.loads(catalog_file.read_text(encoding="utf-8"))
    assert data["document_count"] == 1
    assert doc_id in data["documents"]
    assert data["documents"][doc_id]["title"] == "Quy chế đào tạo"

    # Reload storage from disk
    reloaded = ProcessedStorage(tmp_path)
    assert len(reloaded.documents) == 1
    assert doc_id in reloaded.documents
