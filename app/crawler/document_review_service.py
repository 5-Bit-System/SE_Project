"""Service and repository for crawled document review, deduplication, and metadata editing."""

import hashlib
import json
import re
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import text


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
            d[k] = d[k].isoformat()
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
            "source_id": source_id,
            "job_id": job_id,
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
    """Edit metadata on a draft crawled document before approval."""
    doc = get_document(conn, doc_id)
    if not doc:
        raise ValueError(f"Tài liệu '{doc_id}' không tồn tại.")

    new_title = title if title is not None else doc["title"]
    new_major = major if major is not None else doc["major"]
    new_type = doc_type if doc_type is not None else doc["doc_type"]
    new_meta = json.dumps(metadata) if metadata is not None else json.dumps(doc["metadata_json"])

    conn.execute(
        text("""
            UPDATE crawled_documents
            SET title = :title,
                major = :major,
                doc_type = :doc_type,
                metadata_json = CAST(:meta AS jsonb)
            WHERE id = :id
        """),
        {
            "id": doc_id,
            "title": new_title,
            "major": new_major,
            "doc_type": new_type,
            "meta": new_meta,
        },
    )
    return get_document(conn, doc_id)


def review_document(
    conn,
    doc_id: str,
    decision: str,
    reason: str,
    reviewer_id: str | None = None,
) -> dict[str, Any]:
    """Approve or reject a document with required reason and reviewer audit."""
    if decision not in ("approved", "rejected"):
        raise ValueError("Quyết định kiểm duyệt phải là 'approved' hoặc 'rejected'.")
    if not reason or len(reason.strip()) < 3:
        raise ValueError("Lý do kiểm duyệt bắt buộc phải có ít nhất 3 ký tự.")

    doc = get_document(conn, doc_id)
    if not doc:
        raise ValueError(f"Tài liệu '{doc_id}' không tồn tại.")

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
            "reviewer_id": _safe_uuid(reviewer_id),
        },
    )
    return get_document(conn, doc_id)


def seed_crawled_documents_from_disk(conn, base_dir: Path | None = None) -> int:
    """Scan processed markdown files on disk and index into crawled_documents if empty."""
    existing_count = conn.execute(text("SELECT count(*) FROM crawled_documents")).scalar() or 0
    if existing_count > 0:
        return existing_count

    root = base_dir or (
        Path(__file__).resolve().parents[2] / "data" / "hus" / "processed" / "documents"
    )
    if not root.exists():
        if existing_count == 0:
            create_document(
                conn,
                url="https://hus.vnu.edu.vn/dao-tao/kctdt-chuan-toan-hoc",
                title="Khung chương trình đào tạo chuẩn ngành Toán học K67",
                markdown_content="# Khung chương trình đào tạo chuẩn ngành Toán học\n\nNội dung chương trình đào tạo.",
                major="toan_hoc",
                doc_type="curriculum",
                source_id="src_hus_main",
                metadata_json={"title": "Khung chương trình đào tạo chuẩn ngành Toán học", "cohort": "K67"},
                doc_id="doc_default_sample",
            )
            return 1
        return 0

    inserted = 0
    for md_file in root.glob("**/*.md"):
        try:
            raw_text = md_file.read_text(encoding="utf-8")
        except Exception:
            continue

        frontmatter, content_body = parse_frontmatter(raw_text)

        title = frontmatter.get("title") or md_file.stem
        url = frontmatter.get("url") or f"https://hus.vnu.edu.vn/processed/{md_file.name}"
        major = frontmatter.get("major") or md_file.parent.name
        doc_type = frontmatter.get("type") or "curriculum"

        create_document(
            conn,
            url=str(url),
            title=str(title),
            markdown_content=content_body,
            major=str(major),
            doc_type=str(doc_type),
            source_id="src_hus_main",
            metadata_json=frontmatter,
            doc_id=f"doc_{md_file.stem[-8:]}" if len(md_file.stem) >= 8 else None,
        )
        inserted += 1

    if inserted == 0 and existing_count == 0:
        create_document(
            conn,
            url="https://hus.vnu.edu.vn/dao-tao/kctdt-chuan-toan-hoc",
            title="Khung chương trình đào tạo chuẩn ngành Toán học K67",
            markdown_content="# Khung chương trình đào tạo chuẩn ngành Toán học\n\nNội dung chương trình đào tạo.",
            major="toan_hoc",
            doc_type="curriculum",
            source_id="src_hus_main",
            metadata_json={"title": "Khung chương trình đào tạo chuẩn ngành Toán học", "cohort": "K67"},
            doc_id="doc_default_sample",
        )
        inserted = 1

    return inserted
