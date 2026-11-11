"""Service and repository for crawled document review, deduplication, and metadata editing."""

import hashlib
import json
import logging
import os
import re
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from sqlalchemy import text

from app.curriculum.transactions import publication_lock

logger = logging.getLogger(__name__)

DEFAULT_REVIEWS_FILE = Path("data/hus/document_reviews.json")
_EXPORT_LOCK = threading.Lock()


class DocumentConflictError(ValueError):
    """Raised when review_document encounters an expected status mismatch (compare-and-set)."""


def document_review_fingerprint(document: dict[str, Any]) -> str:
    """Bind a repository decision to one source version and its reviewed metadata.

    This is an identity check for trusted review snapshots, not a signature or
    proof that an administrator actually performed a review.
    """
    metadata = document.get("metadata_json") or {}
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    payload = {
        "format": "document-review-v1",
        "id": document.get("id") or document.get("doc_id"),
        "url": document.get("url"),
        "content_hash": document.get("content_hash"),
        "title": document.get("title"),
        "major": document.get("major"),
        "doc_type": document.get("doc_type"),
        "metadata_json": metadata,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def normalize_crawled_url(url: str) -> str:
    """Normalize crawler URLs. Specifically ensures mim.hus.vnu.edu.vn uses http:// to avoid port 443 timeout."""
    if not url:
        return ""
    url = url.strip()
    if url.startswith("https://mim.hus.vnu.edu.vn"):
        url = "http://mim.hus.vnu.edu.vn" + url[len("https://mim.hus.vnu.edu.vn"):]
    return url


def load_git_reviews(file_path: Path | None = None) -> dict[str, dict[str, Any]]:
    path = file_path or DEFAULT_REVIEWS_FILE
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("Could not read reviews file %s: %s", path, e)
        return {}


def save_git_review(
    doc_id: str,
    url: str,
    content_hash: str,
    title: str,
    review_status: str,
    review_reason: str,
    reviewer_id: str | None = None,
    reviewed_at: str | None = None,
    file_path: Path | None = None,
) -> None:
    path = file_path or DEFAULT_REVIEWS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    reviews = load_git_reviews(path)
    reviews[doc_id] = {
        "doc_id": doc_id,
        "url": url,
        "content_hash": content_hash,
        "title": title,
        "review_status": review_status,
        "review_reason": review_reason,
        "reviewer_id": reviewer_id,
        "reviewed_at": reviewed_at or "",
    }
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(reviews, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def export_git_reviews_from_db(
    engine_or_conn: Any,
    file_path: Path | None = None,
) -> int:
    """Export committed review decisions from PostgreSQL (SSOT) to Git-tracked JSON with atomic write.

    Queries all crawled documents with review_status IN ('approved', 'rejected'),
    writes to a unique .tmp file in the destination directory, and atomically replaces
    the target file using os.replace with up to 3 retries on transient file locks.
    """
    with _EXPORT_LOCK:
        path = Path(file_path) if file_path is not None else DEFAULT_REVIEWS_FILE
        path.parent.mkdir(parents=True, exist_ok=True)

        if hasattr(engine_or_conn, "connect") and not hasattr(engine_or_conn, "execute"):
            with engine_or_conn.connect() as conn:
                return _do_export_git_reviews(conn, path)
        else:
            return _do_export_git_reviews(engine_or_conn, path)


def _do_export_git_reviews(conn: Any, path: Path) -> int:
    reviews: dict[str, dict[str, Any]] = {}

    rows = conn.execute(
        text("""
            SELECT id, url, content_hash, title, major, doc_type, metadata_json,
                   review_status, review_reason, reviewer_id, reviewed_at
            FROM crawled_documents
            WHERE (review_status = 'rejected' OR (review_status = 'approved' AND reviewer_id IS NOT NULL))
              AND url NOT LIKE 'javascript:%'
              AND id != 'doc_xss_test'
            ORDER BY id
        """)
    ).fetchall()

    for r in rows:
        d = _row_to_dict(r)
        if not d:
            continue
        # Safeguard: never export orphan approved reviews or test fixtures to git JSON
        if d["review_status"] == "approved" and not d.get("reviewer_id"):
            logger.warning("Skipping export of unverified approved document %s", d["id"])
            continue
        if "javascript:" in d["url"].lower() or d["id"] == "doc_xss_test":
            continue
        reviews[d["id"]] = {
            "doc_id": d["id"],
            "url": d["url"],
            "content_hash": d["content_hash"],
            "title": d["title"],
            "review_status": d["review_status"],
            "review_reason": d.get("review_reason") or "",
            "reviewer_id": d.get("reviewer_id"),
            "reviewed_at": d.get("reviewed_at") or "",
            "review_fingerprint": document_review_fingerprint(d),
        }

    tmp_path = path.with_name(f"{path.stem}_{uuid.uuid4().hex[:8]}.tmp")
    payload = json.dumps(reviews, ensure_ascii=False, indent=2)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            tmp_path.write_text(payload, encoding="utf-8")
            os.replace(tmp_path, path)
            break
        except OSError as exc:
            if attempt < max_retries - 1:
                time.sleep(0.05 * (2**attempt))
            else:
                logger.error(
                    "Failed to export git reviews to %s after %d attempts: %s",
                    path,
                    max_retries,
                    exc,
                )
                raise
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

    return len(reviews)



def _safe_uuid(val: Any) -> str | None:
    if not val:
        return None
    try:
        return str(uuid.UUID(str(val)))
    except (ValueError, AttributeError):
        return None


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    d = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
    for k in ("created_by", "reviewer_id"):
        if k in d and d[k] is not None:
            d[k] = str(d[k])
    for k in ("created_at", "updated_at", "started_at", "completed_at", "reviewed_at"):
        if k in d and d[k] is not None:
            if hasattr(d[k], "isoformat"):
                d[k] = d[k].isoformat()
            else:
                d[k] = str(d[k])
    return d


def parse_frontmatter(text_content: str) -> tuple[dict[str, Any], str]:
    """Parse key-value YAML frontmatter without external pyyaml dependency."""
    if not text_content.startswith("---"):
        return {}, text_content
    parts = text_content.split("---", 2)
    if len(parts) < 3:
        return {}, text_content
    meta = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            meta[k] = v
    return meta, parts[2].strip()


def is_meaningful_content(content: str, min_length: int = 50) -> tuple[bool, str]:
    """Validate whether document content contains sufficient non-marker text.

    Strips YAML frontmatter and HTML comment page markers (e.g. <!-- page 1 -->).
    Returns (True, "") if cleaned text has at least min_length characters,
    otherwise returns (False, "Nội dung tài liệu rỗng hoặc chỉ chứa marker trang, không đủ điều kiện phê duyệt (cần OCR)").
    """
    if not content:
        return (
            False,
            "Nội dung tài liệu rỗng hoặc chỉ chứa marker trang, không đủ điều kiện phê duyệt (cần OCR)",
        )

    # Strip frontmatter if present
    if content.startswith("---"):
        _, body = parse_frontmatter(content)
    else:
        body = content

    # Strip HTML comment markers (e.g., <!-- page 1 -->)
    cleaned = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL).strip()

    if len(cleaned) < min_length:
        return (
            False,
            "Nội dung tài liệu rỗng hoặc chỉ chứa marker trang, không đủ điều kiện phê duyệt (cần OCR)",
        )

    return (True, "")


def compute_content_hash(content: str) -> str:
    """Return SHA-256 hex digest of normalized content."""
    norm = content.strip().encode("utf-8")
    return hashlib.sha256(norm).hexdigest()


def sanitize_markdown_for_preview(raw_text: str) -> str:
    """Strip dangerous tags (<script>, <iframe>, event handlers) for secure admin preview."""
    if not raw_text:
        return ""
    # Strip script and iframe tags
    clean = re.sub(
        r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", raw_text, flags=re.DOTALL | re.IGNORECASE
    )
    clean = re.sub(
        r"<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>", "", clean, flags=re.DOTALL | re.IGNORECASE
    )
    # Strip javascript: URIs
    clean = re.sub(r"javascript\s*:", "blocked-uri:", clean, flags=re.IGNORECASE)
    # Strip onerror/onload/onclick inline attributes
    clean = re.sub(r"\bon\w+\s*=", "data-blocked-handler=", clean, flags=re.IGNORECASE)
    return clean


def find_duplicates(conn, content_hash: str, exclude_id: str | None = None) -> list[dict[str, Any]]:
    """Find other documents sharing the exact same content hash."""
    query = "SELECT id, url, title, major, review_status, created_at FROM crawled_documents WHERE content_hash = :hash"
    params: dict[str, Any] = {"hash": content_hash}
    if exclude_id:
        query += " AND id != :exclude_id"
        params["exclude_id"] = exclude_id
    rows = conn.execute(text(query), params).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_document_review_summary(conn) -> dict[str, int]:
    """Return count of crawled documents grouped by review status."""
    rows = conn.execute(
        text("SELECT review_status, count(*) FROM crawled_documents GROUP BY review_status")
    ).fetchall()
    counts = {r[0]: int(r[1]) for r in rows}
    total = sum(counts.values())
    return {
        "total": total,
        "approved": counts.get("approved", 0),
        "pending": counts.get("pending", 0),
        "rejected": counts.get("rejected", 0),
    }


def list_documents(
    conn,
    status: str | None = None,
    major: str | None = None,
    source_id: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Return paginated list of crawled documents with filtering."""
    base_where = "WHERE 1=1"
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if status and status != "all":
        base_where += " AND review_status = :status"
        params["status"] = status
    if major and major != "all":
        base_where += " AND major = :major"
        params["major"] = major
    if source_id and source_id != "all":
        base_where += " AND source_id = :source_id"
        params["source_id"] = source_id
    if search:
        base_where += " AND (title ILIKE :search OR url ILIKE :search)"
        params["search"] = f"%{search.strip()}%"

    count_query = f"SELECT count(*) FROM crawled_documents {base_where}"
    total = conn.execute(text(count_query), params).scalar() or 0

    query = f"""
        SELECT id, source_id, job_id, url, content_hash, title, major, doc_type,
               review_status, reviewer_id, review_reason, reviewed_at, is_published, created_at,
               length(markdown_content) as content_length
        FROM crawled_documents
        {base_where}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """
    rows = conn.execute(text(query), params).fetchall()
    return [_row_to_dict(r) for r in rows], total


def get_document(conn, doc_id: str) -> dict[str, Any] | None:
    """Get single document detail with duplicates analysis."""
    row = conn.execute(
        text("SELECT * FROM crawled_documents WHERE id = :id"),
        {"id": doc_id},
    ).fetchone()
    if not row:
        return None
    doc = _row_to_dict(row)
    doc["safe_markdown"] = sanitize_markdown_for_preview(doc["markdown_content"])
    doc["duplicates"] = find_duplicates(conn, doc["content_hash"], exclude_id=doc_id)
    doc["duplicate_count"] = len(doc["duplicates"])
    is_meaningful, _ = is_meaningful_content(doc.get("markdown_content") or "")
    doc["needs_ocr"] = not is_meaningful
    return doc


def create_document(
    conn,
    url: str,
    title: str,
    markdown_content: str,
    major: str = "general",
    doc_type: str = "general_info",
    source_id: str | None = None,
    job_id: str | None = None,
    metadata_json: dict[str, Any] | None = None,
    doc_id: str | None = None,
) -> dict[str, Any]:
    did = doc_id or f"doc_{uuid.uuid4().hex[:12]}"
    h = compute_content_hash(markdown_content)

    valid_source_id = None
    if source_id:
        exists_src = conn.execute(
            text("SELECT 1 FROM crawler_sources WHERE id = :sid"),
            {"sid": source_id},
        ).scalar()
        if exists_src:
            valid_source_id = source_id

    valid_job_id = None
    if job_id:
        exists_job = conn.execute(
            text("SELECT 1 FROM crawler_jobs WHERE id = :jid"),
            {"jid": job_id},
        ).scalar()
        if exists_job:
            valid_job_id = job_id

    conn.execute(
        text("""
            INSERT INTO crawled_documents (
                id, source_id, job_id, url, content_hash, title, major,
                doc_type, markdown_content, metadata_json, review_status, created_at
            ) VALUES (
                :id, :source_id, :job_id, :url, :hash, :title, :major,
                :doc_type, :content, CAST(:metadata AS jsonb), 'pending', now()
            )
        """),
        {
            "id": did,
            "source_id": valid_source_id,
            "job_id": valid_job_id,
            "url": url,
            "hash": h,
            "title": title,
            "major": major,
            "doc_type": doc_type,
            "content": markdown_content,
            "metadata": json.dumps(metadata_json or {}),
        },
    )
    return get_document(conn, did)


def update_document_metadata(
    conn,
    doc_id: str,
    title: str | None = None,
    major: str | None = None,
    doc_type: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Edit metadata on a draft crawled document. If document was approved or published,
    its review status is invalidated (reset to pending, unpublished, clearing reviewer attribution)
    so it requires re-review before publication.
    """
    publication_lock(conn)
    conn.execute(text('SELECT id FROM crawled_documents WHERE id=:id FOR UPDATE'), {'id': doc_id})
    doc = get_document(conn, doc_id)
    if not doc:
        raise ValueError(f"Tài liệu '{doc_id}' không tồn tại.")

    new_title = title if title is not None else doc["title"]
    new_major = major if major is not None else doc["major"]
    new_type = doc_type if doc_type is not None else doc["doc_type"]
    new_meta = json.dumps(metadata) if metadata is not None else json.dumps(doc["metadata_json"])

    was_approved_or_published = doc.get("review_status") == "approved" or bool(doc.get("is_published"))
    if was_approved_or_published:
        meta = json.loads(new_meta)
        meta['previous_document_id'] = doc_id
        previous_version = (doc.get('metadata_json') or {}).get('version', 1)
        meta['version'] = (previous_version if type(previous_version) is int else 1) + 1
        replacement = create_document(conn, url=doc['url'], title=new_title,
            markdown_content=doc['markdown_content'], major=new_major, doc_type=new_type,
            source_id=doc.get('source_id'), job_id=doc.get('job_id'), metadata_json=meta)
        replacement['branched_from'] = doc_id
        return replacement

    conn.execute(
        text("""
            UPDATE crawled_documents
            SET title = :title,
                major = :major,
                doc_type = :doc_type,
                metadata_json = CAST(:meta AS jsonb),
                review_status = CASE WHEN :was_revoked THEN 'pending' ELSE review_status END,
                is_published = CASE WHEN :was_revoked THEN false ELSE is_published END,
                reviewer_id = CASE WHEN :was_revoked THEN NULL ELSE reviewer_id END,
                review_reason = CASE WHEN :was_revoked THEN NULL ELSE review_reason END,
                reviewed_at = CASE WHEN :was_revoked THEN NULL ELSE reviewed_at END
            WHERE id = :id
        """),
        {
            "id": doc_id,
            "title": new_title,
            "major": new_major,
            "doc_type": new_type,
            "meta": new_meta,
            "was_revoked": was_approved_or_published,
        },
    )
    return get_document(conn, doc_id)


def review_document(
    conn,
    doc_id: str,
    decision: str,
    reason: str,
    reviewer_id: str | None = None,
    expected_status: Literal["pending", "approved", "rejected"] | None = None,
) -> dict[str, Any]:
    """Approve or reject a document with required reason and reviewer audit."""
    if decision not in ("approved", "rejected"):
        raise ValueError("Quyết định kiểm duyệt phải là 'approved' hoặc 'rejected'.")
    if not reason or len(reason.strip()) < 3:
        raise ValueError("Lý do kiểm duyệt bắt buộc phải có ít nhất 3 ký tự.")

    publication_lock(conn)
    conn.execute(text('SELECT id FROM crawled_documents WHERE id=:id FOR UPDATE'), {'id': doc_id})
    doc = get_document(conn, doc_id)
    if not doc:
        raise ValueError(f"Tài liệu '{doc_id}' không tồn tại.")
    if doc.get('is_published'):
        raise ValueError('Published source versions are immutable; create a draft replacement')

    if expected_status is not None and doc.get("review_status") != expected_status:
        raise DocumentConflictError(
            f"Trạng thái tài liệu '{doc_id}' hiện tại là '{doc.get('review_status')}', "
            f"không khớp với trạng thái kỳ vọng '{expected_status}'."
        )

    if decision == "approved":
        is_meaningful, error_msg = is_meaningful_content(doc.get("markdown_content") or "")
        if not is_meaningful:
            raise ValueError(
                error_msg
                or "Nội dung tài liệu rỗng hoặc chỉ chứa marker trang, không đủ điều kiện phê duyệt (cần OCR)"
            )

    valid_reviewer_id = None
    safe_uid = _safe_uuid(reviewer_id)
    if safe_uid:
        try:
            exists = conn.execute(
                text("SELECT 1 FROM accounts WHERE id = :aid"),
                {"aid": safe_uid},
            ).scalar()
            if exists:
                valid_reviewer_id = safe_uid
            else:
                logger.warning("Reviewer account %s does not exist in accounts table; using null", safe_uid)
        except Exception as exc:
            logger.warning("Failed to verify reviewer account %s: %s", safe_uid, exc)

    if decision == "approved":
        if not valid_reviewer_id:
            raise ValueError(
                "Phê duyệt tài liệu bắt buộc phải có tài khoản người duyệt (reviewer) hợp lệ trong hệ thống."
            )

    conn.execute(
        text("""
            UPDATE crawled_documents
            SET review_status = :status,
                review_reason = :reason,
                reviewer_id = :reviewer_id,
                reviewed_at = now()
            WHERE id = :id
        """),
        {
            "id": doc_id,
            "status": decision,
            "reason": reason.strip(),
            "reviewer_id": valid_reviewer_id,
        },
    )
    return get_document(conn, doc_id)


NON_MATH_DISCIPLINE_KEYWORDS: tuple[str, ...] = (
    "hóa dược",
    "hóa học",
    "địa chất",
    "địa lý",
    "sinh học",
    "vật lí",
    "vật lý",
    "môi trường",
    "hải dương",
    "khí tượng",
    "hạt nhân",
    "vật liệu",
)


def resolve_document_major(metadata: dict[str, Any], path: Path | None = None) -> str:
    """Resolve document major respecting frontmatter and multi-discipline keywords.

    Ensures that any document containing keywords from other natural science faculties
    (Chemistry, Biology, Geology, Geography, Materials Science, Physics, Environmental Science, etc.)
    is automatically categorized as 'general' even if located in mathematics directory.
    Uses frontmatter major directly if valid and not conflicting with non-math disciplines.
    """
    raw_major = str(metadata.get("major") or "").strip().lower()
    title = str(metadata.get("title") or "").lower()
    fname = path.name.lower() if path else ""

    if any(kw in title or kw in fname for kw in NON_MATH_DISCIPLINE_KEYWORDS):
        return "general"

    if raw_major:
        return raw_major

    if path and "mathematics" in path.parts:
        return "mathematics"

    return "general"


def seed_crawled_documents_from_disk(
    conn, base_dir: Path | None = None, clean_old_mock: bool = False
) -> int:
    """Import 179 real crawled documents from disk into PostgreSQL.

    If clean_old_mock is True, purges legacy mock test records while preserving
    security audit anchors such as 'doc_xss_test'.
    """
    if clean_old_mock:
        conn.execute(
            text("""
                DELETE FROM crawled_documents
                WHERE id != 'doc_xss_test'
                  AND is_published = false
                  AND review_status = 'pending'
                  AND reviewer_id IS NULL AND reviewed_at IS NULL
                  AND (
                    url LIKE '%approved-doc-test%'
                    OR url LIKE '%cntt-copy%'
                    OR url LIKE '%ctdt-khdl-gate%'
                    OR url LIKE '%cntt-2022%'
                    OR url LIKE '%doc_audit_%'
                    OR url LIKE '%test-review-doc%'
                    OR url LIKE '%dummy%'
                    OR url LIKE 'javascript:%'
                  )
            """)
        )

    if base_dir is None:
        base_dir = Path("data/hus/processed/documents")
    if not base_dir.is_dir():
        return 0

    from urllib.parse import urlsplit

    count = 0
    for path in sorted(base_dir.rglob("*.md")):
        raw = path.read_text(encoding="utf-8")
        metadata, content = parse_frontmatter(raw)
        raw_url = str(metadata.get("url") or "")
        url = normalize_crawled_url(raw_url)
        if urlsplit(url).scheme not in {"http", "https"} or not metadata.get("title"):
            continue

        existing_id = conn.execute(
            text("SELECT id FROM crawled_documents WHERE url = :url"),
            {"url": url},
        ).scalar()
        if existing_id:
            continue

        doc_id = f"doc_{hashlib.sha256(url.encode('utf-8')).hexdigest()[:12]}"
        metadata["original_file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        create_document(
            conn,
            url=url,
            title=metadata["title"],
            markdown_content=content,
            major=resolve_document_major(metadata, path),
            doc_type=metadata.get("type", "general_info"),
            metadata_json=metadata,
            doc_id=doc_id,
        )
        count += 1
    return count


def sync_crawled_documents_and_reviews(
    conn, docs_dir: Path | None = None, reviews_file: Path | None = None
) -> dict[str, int]:
    """Seed sources and restore trusted decisions only into untouched drafts.

    Existing database decisions always win, including after an export failure.
    Legacy snapshots lacking a version fingerprint remain readable for inspection
    but cannot authorize a decision. Never match a decision by URL alone.
    """
    publication_lock(conn)
    # Fixture cleanup is never a side effect of normal startup or review restore.
    seeded = seed_crawled_documents_from_disk(conn, base_dir=docs_dir)
    reviews = load_git_reviews(reviews_file)
    if not isinstance(reviews, dict):
        raise ValueError("Review snapshot must be a JSON object keyed by document ID")
    applied = 0
    hash_mismatches = 0
    protected_published = 0
    skipped_marker_only = 0
    skipped_unverified_approvals = 0
    skipped_existing_decisions = 0
    version_mismatches = 0
    invalid_review_evidence = 0
    for doc_id, r in reviews.items():
        if not isinstance(r, dict):
            invalid_review_evidence += 1
            continue
        url = r.get("url")
        status = r.get("review_status")
        content_hash = r.get("content_hash")
        target = conn.execute(
            text("SELECT * FROM crawled_documents WHERE id = :id"), {"id": doc_id}
        ).mappings().first()
        if not target or target["url"] != url or r.get("doc_id", doc_id) != doc_id:
            version_mismatches += 1
            continue
        if target["is_published"]:
            protected_published += 1
            continue
        if not content_hash or target["content_hash"] != content_hash:
            hash_mismatches += 1
            continue
        # A pending snapshot is not a decision and cannot revoke a database review.
        if status not in ("approved", "rejected"):
            continue
        if (
            target["review_status"] != "pending"
            or target["reviewer_id"] is not None
            or target["reviewed_at"] is not None
            or target["review_reason"]
        ):
            skipped_existing_decisions += 1
            continue

        reviewer_id = _safe_uuid(r.get("reviewer_id"))
        valid_reviewer_id = None
        if reviewer_id:
            if conn.execute(text("SELECT 1 FROM accounts WHERE id = :aid"), {"aid": reviewer_id}).scalar():
                valid_reviewer_id = reviewer_id
        if not valid_reviewer_id:
            if status == "approved":
                skipped_unverified_approvals += 1
            else:
                invalid_review_evidence += 1
            continue

        if status == "approved":
            is_meaningful, _ = is_meaningful_content(target["markdown_content"] or "")
            if not is_meaningful:
                skipped_marker_only += 1
                continue
        fingerprint = r.get("review_fingerprint")
        if not fingerprint or fingerprint != document_review_fingerprint(dict(target)):
            version_mismatches += 1
            continue
        reason = r.get("review_reason")
        try:
            reviewed_at = datetime.fromisoformat(r.get("reviewed_at") or "")
        except (TypeError, ValueError):
            invalid_review_evidence += 1
            continue
        if not isinstance(reason, str) or len(reason.strip()) < 3 or reviewed_at.utcoffset() is None:
            invalid_review_evidence += 1
            continue

        res = conn.execute(
            text("""
                UPDATE crawled_documents
                SET review_status = :status,
                    review_reason = :reason,
                    reviewer_id = :reviewer_id,
                    reviewed_at = :reviewed_at
                WHERE id = :id AND url = :url
                  AND content_hash = :content_hash
                  AND is_published = false
                  AND review_status = 'pending'
                  AND reviewer_id IS NULL AND reviewed_at IS NULL
                  AND (review_reason IS NULL OR review_reason = '')
            """),
            {
                "id": doc_id,
                "url": url,
                "content_hash": content_hash,
                "status": status,
                "reason": reason.strip(),
                "reviewer_id": valid_reviewer_id,
                "reviewed_at": reviewed_at,
            },
        )
        if res.rowcount > 0:
            applied += res.rowcount

    total_docs = conn.execute(text("SELECT count(*) FROM crawled_documents")).scalar() or 0
    return {
        "seeded": seeded,
        "total": total_docs,
        "reviews_applied": applied,
        "hash_mismatches": hash_mismatches,
        "protected_published": protected_published,
        "skipped_marker_only": skipped_marker_only,
        "skipped_unverified_approvals": skipped_unverified_approvals,
        "skipped_existing_decisions": skipped_existing_decisions,
        "version_mismatches": version_mismatches,
        "invalid_review_evidence": invalid_review_evidence,
    }
