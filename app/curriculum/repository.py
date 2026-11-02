"""Repository for versioned curriculum revisions and audit reviews."""

import json
import uuid

from sqlalchemy import text


def _safe_uuid(val):
    if not val:
        return None
    try:
        return str(uuid.UUID(str(val)))
    except (ValueError, AttributeError):
        return None


def _row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    if "id" in d and d["id"] is not None:
        d["id"] = str(d["id"])
    if "created_by" in d and d["created_by"] is not None:
        d["created_by"] = str(d["created_by"])
    if "reviewed_by" in d and d["reviewed_by"] is not None:
        d["reviewed_by"] = str(d["reviewed_by"])
    if "reviewer_id" in d and d["reviewer_id"] is not None:
        d["reviewer_id"] = str(d["reviewer_id"])
    for key in ("created_at", "reviewed_at", "published_at"):
        if key in d and d[key] is not None:
            d[key] = d[key].isoformat()
    return d


def create_revision(
    conn,
    program_id: str,
    version_title: str,
    payload: dict,
    source_digest: str,
    cohort: str | None = None,
    source_filename: str | None = None,
    created_by: str | uuid.UUID | None = None,
) -> dict:
    revision_id = f"rev_{uuid.uuid4().hex[:12]}"
    conn.execute(
        text("""
            INSERT INTO curriculum_revisions (
                revision_id, program_id, cohort, version_title,
                source_filename, source_digest, payload, status,
                created_by
            ) VALUES (
                :rev_id, :program_id, :cohort, :title,
                :filename, :digest, :payload, 'draft',
                :created_by
            )
        """),
        {
            "rev_id": revision_id,
            "program_id": program_id,
            "cohort": cohort,
            "title": version_title,
            "filename": source_filename,
            "digest": source_digest,
            "payload": json.dumps(payload),
            "created_by": _safe_uuid(created_by),
        },
    )

    # Record initial audit event
    record_review(
        conn,
        revision_id=revision_id,
        reviewer_id=created_by,
        action="created",
        reason="Khởi tạo bản thảo chương trình đào tạo",
        details={"version_title": version_title, "source_filename": source_filename},
    )

    return get_revision(conn, revision_id)


def get_revision(conn, revision_id: str) -> dict | None:
    row = (
        conn.execute(
            text("SELECT * FROM curriculum_revisions WHERE revision_id = :rev_id"),
            {"rev_id": revision_id},
        )
        .mappings()
        .one_or_none()
    )
    return _row_to_dict(row)


def list_revisions(
    conn,
    program_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    query = "SELECT * FROM curriculum_revisions WHERE 1=1"
    params = {"limit": limit}
    if program_id:
        query += " AND program_id = :program_id"
        params["program_id"] = program_id
    if status:
        query += " AND status = :status"
        params["status"] = status
    query += " ORDER BY created_at DESC LIMIT :limit"

    rows = conn.execute(text(query), params).mappings().all()
    return [_row_to_dict(r) for r in rows]


def update_validation(
    conn,
    revision_id: str,
    status: str,
    validation_summary: dict,
) -> dict:
    conn.execute(
        text("""
            UPDATE curriculum_revisions
            SET status = :status,
                validation_summary = :summary
            WHERE revision_id = :rev_id
        """),
        {
            "rev_id": revision_id,
            "status": status,
            "summary": json.dumps(validation_summary),
        },
    )
    record_review(
        conn,
        revision_id=revision_id,
        reviewer_id=None,
        action="validated",
        reason=f"Kiểm thử dữ liệu: {status}",
        details=validation_summary,
    )
    return get_revision(conn, revision_id)


def update_revision_payload(
    conn,
    revision_id: str,
    payload: dict,
    updated_by: str | uuid.UUID | None = None,
    reason: str = "Cập nhật nội dung bản thảo",
) -> dict:
    conn.execute(
        text("""
            UPDATE curriculum_revisions
            SET payload = :payload
            WHERE revision_id = :rev_id
        """),
        {
            "rev_id": revision_id,
            "payload": json.dumps(payload),
        },
    )
    record_review(
        conn,
        revision_id=revision_id,
        reviewer_id=updated_by,
        action="validated",
        reason=reason,
        details={"event": "payload_updated"},
    )
    return get_revision(conn, revision_id)


def review_revision(
    conn,
    revision_id: str,
    reviewer_id: str | uuid.UUID | None,
    decision: str,
    reason: str,
    notes: str | None = None,
) -> dict:
    if decision not in ("approved", "rejected"):
        raise ValueError(f"Invalid review decision: {decision}")

    target = get_revision(conn, revision_id)
    if not target:
        raise ValueError(f"Revision {revision_id} not found")

    if decision == "approved":
        from app.curriculum.publication_gate import check_revision_validation

        is_valid, reason_invalid = check_revision_validation(target)
        if not is_valid:
            raise ValueError(f"Cannot approve revision: {reason_invalid}")

    new_status = "approved" if decision == "approved" else "rejected"
    conn.execute(
        text("""
            UPDATE curriculum_revisions
            SET status = :status,
                reviewed_by = :reviewer,
                reviewed_at = now(),
                review_decision = :decision,
                review_notes = :notes
            WHERE revision_id = :rev_id
        """),
        {
            "rev_id": revision_id,
            "status": new_status,
            "reviewer": _safe_uuid(reviewer_id),
            "decision": decision,
            "notes": notes,
        },
    )
    record_review(
        conn,
        revision_id=revision_id,
        reviewer_id=reviewer_id,
        action=new_status,
        reason=reason,
        details={"notes": notes},
    )
    return get_revision(conn, revision_id)


def publish_revision(
    conn,
    revision_id: str,
    publisher_id: str | uuid.UUID | None,
    reason: str,
    linked_document_ids: list[str] | None = None,
) -> dict:
    from app.curriculum.publication_gate import publish_revision_with_gate

    return publish_revision_with_gate(
        conn,
        revision_id=revision_id,
        publisher_id=publisher_id,
        reason=reason,
        linked_document_ids=linked_document_ids,
    )


def rollback_revision(
    conn,
    program_id: str,
    target_revision_id: str,
    user_id: str | uuid.UUID | None,
    reason: str,
) -> dict:
    target = get_revision(conn, target_revision_id)
    if not target:
        raise ValueError(f"Target revision {target_revision_id} not found")
    if target["program_id"] != program_id:
        raise ValueError(f"Revision belongs to {target['program_id']}, not {program_id}")

    # Deactivate current active
    conn.execute(
        text("""
            UPDATE curriculum_revisions
            SET is_active = false
            WHERE program_id = :program_id AND is_active = true
        """),
        {"program_id": program_id},
    )

    # Activate target
    conn.execute(
        text("""
            UPDATE curriculum_revisions
            SET is_active = true,
                status = 'published'
            WHERE revision_id = :rev_id
        """),
        {"rev_id": target_revision_id},
    )

    record_review(
        conn,
        revision_id=target_revision_id,
        reviewer_id=user_id,
        action="rolled_back",
        reason=reason,
        details={"program_id": program_id},
    )
    return get_revision(conn, target_revision_id)


def get_active_revision(conn, program_id: str) -> dict | None:
    row = (
        conn.execute(
            text(
                "SELECT * FROM curriculum_revisions WHERE program_id = :program_id AND is_active = true"
            ),
            {"program_id": program_id},
        )
        .mappings()
        .one_or_none()
    )
    return _row_to_dict(row)


def record_review(
    conn,
    revision_id: str,
    reviewer_id: str | uuid.UUID | None,
    action: str,
    reason: str,
    details: dict | None = None,
):
    review_id = uuid.uuid4()
    conn.execute(
        text("""
            INSERT INTO curriculum_reviews (
                id, revision_id, reviewer_id, action, reason, details
            ) VALUES (
                :id, :rev_id, :reviewer, :action, :reason, :details
            )
        """),
        {
            "id": review_id,
            "rev_id": revision_id,
            "reviewer": _safe_uuid(reviewer_id),
            "action": action,
            "reason": reason,
            "details": json.dumps(details or {}),
        },
    )


def list_reviews(conn, revision_id: str) -> list[dict]:
    rows = (
        conn.execute(
            text(
                "SELECT * FROM curriculum_reviews WHERE revision_id = :rev_id ORDER BY created_at ASC"
            ),
            {"rev_id": revision_id},
        )
        .mappings()
        .all()
    )
    return [_row_to_dict(r) for r in rows]
