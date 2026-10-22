import json
from pathlib import Path

from app.hus.models import DocumentType, HUSDocument, MajorCategory, Publisher
from app.hus.storage import ProcessedStorage, RawStorage


def test_raw_storage_idempotent(tmp_path: Path):
    storage = RawStorage(tmp_path)
    url = "https://mim.hus.vnu.edu.vn/vi/test"
    raw_html = b"<html><body>Hello</body></html>"

    p1 = storage.save_raw_html(url, raw_html)
    assert p1.exists()
    assert p1.read_bytes() == raw_html
    assert p1.parent.name == "general"
    assert "--" in p1.name
    assert p1.suffix == ".html"

    # Same content does not create another file
    p2 = storage.save_raw_html(url, raw_html)
    assert p1 == p2

    # Save with specific major and title
    p3 = storage.save_raw_html(
        "https://mim.hus.vnu.edu.vn/vi/ds",
        raw_html,
        major=MajorCategory.DATA_SCIENCE,
        title="Khoa học dữ liệu",
    )
    assert p3.exists()
    assert p3.parent.name == "data_science"
    assert p3.name.startswith("khoa-hoc-du-lieu--")

    # Save document (pdf)
    p_pdf = storage.save_raw_document("https://mim.hus.vnu.edu.vn/file.pdf", b"%PDF-1.4", "pdf")
    assert p_pdf.exists()
    assert p_pdf.parent.name == "general"
    assert "--" in p_pdf.name
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
    md_files = list((tmp_path / "processed" / "documents").rglob("*.md"))
    assert len(md_files) == 1
    md_file = md_files[0]
    assert md_file.parent.name == "general"
    assert md_file.name.startswith("quy-che-dao-tao--")
    assert md_file.name.endswith(f"{doc_id[:8]}.md")
    assert md_file.exists()
    content = md_file.read_text(encoding="utf-8")
    assert "# Điều 1: Tín chỉ" in content
    assert "major: general" in content

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


def test_hierarchical_storage_and_metadata_header(tmp_path: Path):
    raw_storage = RawStorage(tmp_path)
    processed_storage = ProcessedStorage(tmp_path)

    # 1. Raw HTML with major and title
    html_path = raw_storage.save_raw_html(
        "https://mim.hus.vnu.edu.vn/vi/khdl",
        b"<html>KHDL</html>",
        major=MajorCategory.DATA_SCIENCE,
        title="Khoa học dữ liệu 2026",
    )
    assert html_path == tmp_path / "raw" / "html" / "data_science" / html_path.name
    assert html_path.name.startswith("khoa-hoc-du-lieu-2026--")
    assert html_path.suffix == ".html"

    # 2. Raw document with major and title
    doc_path = raw_storage.save_raw_document(
        "https://mim.hus.vnu.edu.vn/files/khmt.pdf",
        b"%PDF-1.4...",
        ext="pdf",
        major=MajorCategory.COMPUTER_SCIENCE,
        title="khmt.pdf",
    )
    assert doc_path == tmp_path / "raw" / "documents" / "computer_science" / doc_path.name
    assert doc_path.name.startswith("khmt--")
    assert doc_path.suffix == ".pdf"

    # 3. Processed document with major and metadata header
    doc = HUSDocument(
        url="https://mim.hus.vnu.edu.vn/vi/toan-tin",
        title="Chương trình Toán - Tin",
        content="Nội dung chương trình đào tạo",
        content_hash="hash_tt",
        fetched_at="2026-10-22T00:00:00Z",
        major=MajorCategory.MATHEMATICS_INFORMATICS,
        document_type=DocumentType.CURRICULUM,
        publisher=Publisher.MIM,
    )
    doc_id = processed_storage.save_document(doc)
    md_path = (
        tmp_path
        / "processed"
        / "documents"
        / "mathematics_informatics"
        / f"chuong-trinh-toan-tin--{doc_id[:8]}.md"
    )
    assert md_path.exists()

    content = md_path.read_text(encoding="utf-8")
    expected_header = (
        "---\n"
        "title: Chương trình Toán - Tin\n"
        "url: https://mim.hus.vnu.edu.vn/vi/toan-tin\n"
        "publisher: MIM\n"
        "type: curriculum\n"
        "major: mathematics_informatics\n"
        "---\n\n"
    )
    assert content.startswith(expected_header)
    assert "Nội dung chương trình đào tạo" in content
