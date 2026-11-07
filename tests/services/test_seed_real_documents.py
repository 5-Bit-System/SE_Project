"""Tests for seeding real crawled documents from disk into PostgreSQL."""
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from app.crawler.document_review_service import (
    list_documents,
    parse_frontmatter,
    seed_crawled_documents_from_disk,
)
from tests.support.admin_database import admin_test_engine


@pytest.fixture(scope="module")
def db_engine():
    try:
        eng = admin_test_engine()
        with eng.connect():
            pass
        return eng
    except Exception:
        pytest.skip("PostgreSQL database not reachable")


def test_real_documents_on_disk_validity():
    """Offline unit test: verify all 179 real documents on disk are well-formed."""
    docs_dir = Path("data/hus/processed/documents")
    assert docs_dir.is_dir(), "Processed documents directory must exist"

    md_files = list(docs_dir.rglob("*.md"))
    assert len(md_files) == 179, f"Expected exactly 179 markdown documents, got {len(md_files)}"

    for file_path in md_files:
        content = file_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(content)
        assert meta.get("title"), f"Document {file_path} must have a title"
        assert meta.get("url"), f"Document {file_path} must have a url"
        parsed_url = urlsplit(meta["url"])
        assert parsed_url.netloc in {
            "mim.hus.vnu.edu.vn",
            "hus.vnu.edu.vn",
            "tuyensinh.hus.vnu.edu.vn",
        }, f"Invalid domain in {file_path}: {parsed_url.netloc}"
        assert len(body.strip()) > 0, f"Body in {file_path} cannot be empty"


@pytest.mark.hus_postgres
def test_seed_real_crawled_documents(db_engine):
    with db_engine.begin() as conn:
        docs_dir = Path("data/hus/processed/documents")
        assert docs_dir.is_dir()

        # Seed real documents with clean_old_mock=True
        seeded = seed_crawled_documents_from_disk(conn, docs_dir, clean_old_mock=True)
        assert seeded >= 0

        # Verify documents can be listed
        docs, total = list_documents(conn, limit=10)
        assert total >= 170
        assert len(docs) <= 10

        # Verify URLs are real and normalized (mim uses http)
        for doc in docs:
            if doc["id"] == "doc_xss_test":
                continue
            assert doc["url"].startswith("http://") or doc["url"].startswith("https://")
            assert "approved-doc-test" not in doc["url"]
            assert "cntt-copy" not in doc["url"]
            if "mim.hus.vnu.edu.vn" in doc["url"]:
                assert doc["url"].startswith("http://mim.hus.vnu.edu.vn")
