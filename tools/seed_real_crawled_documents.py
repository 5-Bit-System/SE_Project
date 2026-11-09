"""Tool script to seed 179 real HUS crawled documents and sync review state from Git."""

import hashlib
import json
import logging
import sys
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy import create_engine

from app.config import get_settings
from app.crawler.document_review_service import (
    DEFAULT_REVIEWS_FILE,
    NON_MATH_DISCIPLINE_KEYWORDS,
    get_document_review_summary,
    normalize_crawled_url,
    parse_frontmatter,
    resolve_document_major,
    sync_crawled_documents_and_reviews,
)

__all__ = [
    "DEFAULT_REVIEWS_FILE",
    "NON_MATH_DISCIPLINE_KEYWORDS",
    "create_initial_git_reviews_if_empty",
    "main",
    "resolve_document_major",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def create_initial_git_reviews_if_empty(
    docs_dir: Path, reviews_file: Path = DEFAULT_REVIEWS_FILE
) -> None:
    """Initialize only a missing snapshot or an explicit empty JSON object.

    Preserve every nonempty review mapping byte-for-byte, including small exports.
    A blank, malformed or non-object JSON file is an error, never permission to
    overwrite an existing snapshot. This initializer does not repair snapshots.
    """
    if reviews_file.exists():
        try:
            existing_reviews = json.loads(reviews_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError(f"Invalid review snapshot JSON: {reviews_file}") from exc
        if not isinstance(existing_reviews, dict) or any(
            not isinstance(review, dict) for review in existing_reviews.values()
        ):
            raise ValueError(f"Invalid review snapshot mapping: {reviews_file}")
        if existing_reviews:
            logger.info("Found existing review snapshot, keeping all decisions.")
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

    # 1. Pre-populate initial Git reviews file if needed
    create_initial_git_reviews_if_empty(docs_dir, DEFAULT_REVIEWS_FILE)

    logger.info("Connecting to configured database")
    engine = create_engine(settings.database_url)

    with engine.begin() as conn:
        # 2. Synchronize source documents and reviews; test fixtures belong in tests.
        res = sync_crawled_documents_and_reviews(
            conn, docs_dir=docs_dir, reviews_file=DEFAULT_REVIEWS_FILE
        )
        logger.info(
            "Sync result: newly_seeded=%d, total=%d, reviews_applied=%d",
            res["seeded"],
            res["total"],
            res["reviews_applied"],
        )

        # 3. Print summary
        summary = get_document_review_summary(conn)
        logger.info("=== BÁO CÁO TRẠNG THÁI KIỂM DUYỆT TÀI LIỆU ===")
        logger.info("Tổng số tài liệu: %d", summary["total"])
        logger.info("  - Đã phê duyệt (Approved): %d (Xanh lá)", summary["approved"])
        logger.info("  - Chờ phê duyệt (Pending) : %d (Vàng)", summary["pending"])
        logger.info("  - Từ chối (Rejected)      : %d (Đỏ)", summary["rejected"])
        logger.info("===============================================")


if __name__ == "__main__":
    main()
