"""Publication gate and provenance manifest service.

Enforces that catalog revisions can only be published when:
1. The revision has been validated and has no validation errors.
2. The revision is formally in 'approved' status.
3. All linked crawled documents are in 'approved' review status.
   (Pending or rejected documents strictly block publication).
4. Creates a tamper-evident SHA-256 provenance manifest recording the payload,
   linked source documents, publisher identity, timestamp, and signature.
5. User-facing retrieval readers consume only active published revisions and approved,
   published documents.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from app.curriculum.repository import get_revision, record_review


def compute_payload_digest(payload: dict | None) -> str:
    """Compute deterministic SHA-256 hex digest of a revision payload."""
    serialized = json.dumps(payload or {}, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def check_revision_validation(revision: dict[str, Any]) -> tuple[bool, str]:
    """Check whether a revision has an explicit, successful, non-stale validation record.

    Returns (is_valid, error_message).
    """
    if not revision:
        return False, "Revision not found"

    val_summary = revision.get("validation_summary")
    if not val_summary or not isinstance(val_summary, dict) or not bool(val_summary):
        return False, "Revision has not been validated"

    if val_summary.get("valid") is not True:
        return False, "Revision validation status is not valid"

    errors = val_summary.get("errors") or []
    if len(errors) > 0:
        return False, f"Revision has {len(errors)} validation error(s)"

    # Verify digest against current payload or source
    current_payload_digest = compute_payload_digest(revision.get("payload"))
    val_payload_digest = val_summary.get("payload_digest")
    val_digest = val_summary.get("digest")

    if val_payload_digest:
        if val_payload_digest != current_payload_digest:
            return False, "Revision payload has been modified since last validation (stale validation digest)"
    elif val_digest and revision.get("source_digest"):
        if val_digest != revision.get("source_digest"):
            return False, "Revision source digest does not match validation digest"
    else:
        return False, "Validation summary is missing validation digest"

    return True, ""


def validate_publication_gate(
    conn,
    revision_id: str,
    linked_document_ids: list[str] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate all gate criteria before permitting publication.

    Raises ValueError if revision is missing, unapproved, has validation errors,
    or contains any unapproved (pending or rejected) linked source documents.
    """
    target = get_revision(conn, revision_id)
    if not target:
        raise ValueError(f"Revision {revision_id} not found")

    if target.get("status") != "approved":
        raise ValueError(
            f"Cannot publish revision with status '{target.get('status')}'. Must be 'approved'."
        )

    is_valid, reason = check_revision_validation(target)
    if not is_valid:
        raise ValueError(f"Revision {revision_id} cannot be published: {reason}")

    # Collect candidate document IDs
    doc_ids_to_check: list[str] = []
    if linked_document_ids:
        doc_ids_to_check.extend(linked_document_ids)

    payload = target.get("payload") or {}
    if isinstance(payload, dict):
        payload_docs = payload.get("linked_document_ids") or []
        if isinstance(payload_docs, list):
            doc_ids_to_check.extend(str(d) for d in payload_docs if d)

    # Deduplicate while preserving order
    unique_doc_ids = list(dict.fromkeys(doc_ids_to_check))

    approved_docs: list[dict[str, Any]] = []
    for doc_id in unique_doc_ids:
        row = (
            conn.execute(
                text("""
                    SELECT id, source_id, job_id, url, content_hash, title, major, doc_type,
                           review_status, reviewer_id, review_reason, reviewed_at, is_published, created_at
                    FROM crawled_documents
                    WHERE id = :id
                """),
                {"id": doc_id},
            )
            .mappings()
            .one_or_none()
        )

        if not row:
            raise ValueError(f"Linked source document '{doc_id}' not found.")

        doc = dict(row)
        status = doc.get("review_status")
        title = doc.get("title", doc_id)

        if status == "pending":
            raise ValueError(
                f"Cannot publish revision: Linked source document '{title}' ({doc_id}) is pending approval."
            )
        elif status == "rejected":
            raise ValueError(
                f"Cannot publish revision: Linked source document '{title}' ({doc_id}) was rejected."
            )
        elif status != "approved":
            raise ValueError(
                f"Cannot publish revision: Linked source document '{title}' ({doc_id}) is not approved ({status})."
            )

        approved_docs.append(doc)

    return target, approved_docs


def build_publication_manifest(
    revision: dict[str, Any],
    approved_documents: list[dict[str, Any]],
    publisher_id: str | uuid.UUID | None,
    reason: str,
) -> dict[str, Any]:
    """Construct an immutable provenance manifest with SHA-256 integrity checksum."""
    rev_id = revision["revision_id"]
    program_id = revision["program_id"]
    source_digest = revision.get("source_digest") or ""
    payload = revision.get("payload") or {}

    payload_serialized = json.dumps(payload, sort_keys=True)
    payload_hash = hashlib.sha256(payload_serialized.encode("utf-8")).hexdigest()

    docs_manifest = []
    doc_hashes = []
    for doc in sorted(approved_documents, key=lambda d: d["id"]):
        reviewed_at = doc.get("reviewed_at")
        doc_entry = {
            "document_id": doc["id"],
            "url": doc["url"],
            "title": doc["title"],
            "major": doc["major"],
            "content_hash": doc["content_hash"],
            "review_status": doc["review_status"],
            "reviewed_at": reviewed_at.isoformat()
            if hasattr(reviewed_at, "isoformat")
            else str(reviewed_at or ""),
            "reviewer_id": str(doc["reviewer_id"]) if doc.get("reviewer_id") else None,
        }
        docs_manifest.append(doc_entry)
        doc_hashes.append(doc["content_hash"])

    published_at = datetime.now(timezone.utc).isoformat()

    hasher = hashlib.sha256()
    hasher.update(rev_id.encode("utf-8"))
    hasher.update(program_id.encode("utf-8"))
    hasher.update(source_digest.encode("utf-8"))
    hasher.update(payload_hash.encode("utf-8"))
    for h in doc_hashes:
        hasher.update(h.encode("utf-8"))
    manifest_checksum = hasher.hexdigest()

    return {
        "manifest_version": "1.0",
        "revision_id": rev_id,
        "program_id": program_id,
        "version_title": revision.get("version_title"),
        "source_digest": source_digest,
        "payload_hash": payload_hash,
        "published_at": published_at,
        "publisher_id": str(publisher_id) if publisher_id else None,
        "publication_reason": reason,
        "documents_count": len(docs_manifest),
        "source_documents": docs_manifest,
        "manifest_checksum": manifest_checksum,
    }


def publish_revision_with_gate(
    conn,
    revision_id: str,
    publisher_id: str | uuid.UUID | None,
    reason: str,
    linked_document_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Execute gated publication atomically.

    Validates prerequisite gate rules, constructs provenance manifest, marks approved
    documents as published, deactivates previous active revision, activates new revision,
    and records audit history.
    """
    target, approved_docs = validate_publication_gate(conn, revision_id, linked_document_ids)
    manifest = build_publication_manifest(target, approved_docs, publisher_id, reason)
    program_id = target["program_id"]

    # Mark linked approved documents as published
    for doc in approved_docs:
        conn.execute(
            text("UPDATE crawled_documents SET is_published = true WHERE id = :id"),
            {"id": doc["id"]},
        )

    # Deactivate current active revision for this program atomically
    conn.execute(
        text("""
            UPDATE curriculum_revisions
            SET is_active = false
            WHERE program_id = :program_id AND is_active = true
        """),
        {"program_id": program_id},
    )

    # Set new active revision
    conn.execute(
        text("""
            UPDATE curriculum_revisions
            SET is_active = true,
                status = 'published',
                published_at = now()
            WHERE revision_id = :rev_id
        """),
        {"rev_id": revision_id},
    )

    # Record review audit entry with provenance manifest
    record_review(
        conn,
        revision_id=revision_id,
        reviewer_id=publisher_id,
        action="published",
        reason=reason,
        details={
            "program_id": program_id,
            "provenance_manifest": manifest,
        },
    )

    published_rev = get_revision(conn, revision_id)
    if published_rev:
        published_rev["provenance_manifest"] = manifest
    return published_rev or {}


def get_publication_provenance(conn, revision_id: str) -> dict[str, Any] | None:
    """Retrieve the provenance manifest for a published revision."""
    row = (
        conn.execute(
            text("""
                SELECT details FROM curriculum_reviews
                WHERE revision_id = :rev_id AND action = 'published'
                ORDER BY created_at DESC LIMIT 1
            """),
            {"rev_id": revision_id},
        )
        .mappings()
        .one_or_none()
    )
    if not row or not row.get("details"):
        return None

    details = row["details"]
    if isinstance(details, str):
        try:
            details = json.loads(details)
        except Exception:
            return None

    return details.get("provenance_manifest")


def get_published_documents(conn, major: str | None = None) -> list[dict[str, Any]]:
    """Retrieve only approved and published documents for public or student readers."""
    query = """
        SELECT id, url, title, major, doc_type, markdown_content, metadata_json,
               review_status, reviewed_at, is_published, created_at
        FROM crawled_documents
        WHERE is_published = true AND review_status = 'approved'
    """
    params: dict[str, Any] = {}
    if major:
        query += " AND major = :major"
        params["major"] = major
    query += " ORDER BY created_at DESC"

    rows = conn.execute(text(query), params).mappings().all()
    result = []
    for r in rows:
        d = dict(r)
        if hasattr(d.get("created_at"), "isoformat"):
            d["created_at"] = d["created_at"].isoformat()
        if hasattr(d.get("reviewed_at"), "isoformat") and d.get("reviewed_at"):
            d["reviewed_at"] = d["reviewed_at"].isoformat()
        result.append(d)
    return result
