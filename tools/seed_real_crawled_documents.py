"""Tool script to seed 179 real HUS crawled documents and sync review state from Git."""

import hashlib
import json
import logging
import sys
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import create_engine, text

from app.config import get_settings
from app.crawler.document_review_service import (
    DEFAULT_REVIEWS_FILE,
    get_document_review_summary,
    normalize_crawled_url,
    parse_frontmatter,
    sync_crawled_documents_and_reviews,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def create_initial_git_reviews_if_empty(
    docs_dir: Path, reviews_file: Path = DEFAULT_REVIEWS_FILE
) -> None:
    """If reviews JSON does not exist or has < 10 reviews, generate an initial curated set."""
    if reviews_file.is_file() and len(json.loads(reviews_file.read_text("utf-8"))) >= 30:
        logger.info("Found existing document_reviews.json with reviews, keeping existing.")
        return

    reviews: dict[str, dict] = {}
    md_files = sorted(docs_dir.rglob("*.md"))

    content_hashes_seen: dict[str, str] = {}

    for path in md_files:
        raw = path.read_text(encoding="utf-8")
        metadata, content = parse_frontmatter(raw)
        raw_url = str(metadata.get("url") or "")
        url = normalize_crawled_url(raw_url)
        if urlsplit(url).scheme not in {"http", "https"} or not metadata.get("title"):
            continue

        doc_id = f"doc_{hashlib.sha256(url.encode('utf-8')).hexdigest()[:12]}"
        title = metadata["title"]
        c_hash = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()

        # Business rules for initial review states:
        # 1. Duplicates: if duplicate content hash already seen in another document, mark rejected
        if c_hash in content_hashes_seen:
            reviews[doc_id] = {
                "doc_id": doc_id,
                "url": url,
                "content_hash": c_hash,
                "title": title,
                "review_status": "rejected",
                "review_reason": f"Nội dung trùng khớp với tài liệu {content_hashes_seen[c_hash]}",
                "reviewer_id": None,
                "reviewed_at": None,
            }
            continue

        content_hashes_seen[c_hash] = doc_id

        # 2. All newly seeded non-duplicate documents default to 'pending' awaiting administrator review
        reviews[doc_id] = {
            "doc_id": doc_id,
            "url": url,
            "content_hash": c_hash,
            "title": title,
            "review_status": "pending",
            "review_reason": "Chờ kiểm định thực tế bởi quản trị viên",
            "reviewer_id": None,
            "reviewed_at": None,
        }

    reviews_file.parent.mkdir(parents=True, exist_ok=True)
    reviews_file.write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Saved %d initial reviews to %s", len(reviews), reviews_file)


def main() -> None:
    settings = get_settings()
    docs_dir = Path("data/hus/processed/documents")
    if not docs_dir.is_dir():
        logger.error("Documents directory not found at %s", docs_dir)
        sys.exit(1)

    logger.info("Connecting to database: %s", settings.database_url)
    engine = create_engine(settings.database_url)

    # 1. Pre-populate initial Git reviews file if needed
    create_initial_git_reviews_if_empty(docs_dir, DEFAULT_REVIEWS_FILE)

    with engine.begin() as conn:
        # 2. Ensure doc_xss_test exists
        exists_xss = conn.execute(
            text("SELECT 1 FROM crawled_documents WHERE id = 'doc_xss_test'")
        ).scalar()
        if not exists_xss:
            conn.execute(
                text("""
                    INSERT INTO crawled_documents (
                        id, url, content_hash, title, major, doc_type,
                        markdown_content, metadata_json, review_status, created_at
                    ) VALUES (
                        'doc_xss_test', 'javascript:alert(\\'xss\\')', 'xss_hash',
                        'Tài liệu bảo mật <img src=x onerror=window.__doc_xss=true>',
                        'toan_hoc', 'curriculum', '# Nội dung an toàn', '{}'::jsonb,
                        'pending', now()
                    )
                """)
            )
            logger.info("Created security audit document 'doc_xss_test'")

        # 3. Synchronize all 179 real documents and reviews
        res = sync_crawled_documents_and_reviews(
            conn, docs_dir=docs_dir, reviews_file=DEFAULT_REVIEWS_FILE
        )
        logger.info(
            "Sync result: newly_seeded=%d, total=%d, reviews_applied=%d",
            res["seeded"],
            res["total"],
            res["reviews_applied"],
        )

        # 4. Print summary
        summary = get_document_review_summary(conn)
        logger.info("=== BÁO CÁO TRẠNG THÁI KIỂM DUYỆT TÀI LIỆU ===")
        logger.info("Tổng số tài liệu: %d", summary["total"])
        logger.info("  - Đã phê duyệt (Approved): %d (Xanh lá)", summary["approved"])
        logger.info("  - Chờ phê duyệt (Pending) : %d (Vàng)", summary["pending"])
        logger.info("  - Từ chối (Rejected)      : %d (Đỏ)", summary["rejected"])
        logger.info("===============================================")


if __name__ == "__main__":
    main()
