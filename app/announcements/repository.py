"""Repository for academic announcements persistence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text


def _row_to_dict(row: Any) -> dict[str, Any] | None:
    if row is None:
        return None
    d = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
    for k in ("effective_date", "expiry_date", "created_at", "published_at"):
        if k in d and isinstance(d[k], datetime):
            d[k] = d[k].isoformat()
    return d


def create_announcement_record(
    conn,
    title: str,
    content: str,
    source_url: str,
    audience: str = "all",
    effective_date: datetime | str | None = None,
    expiry_date: datetime | str | None = None,
    created_by: str = "admin",
) -> dict[str, Any]:
    ann_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    eff = effective_date or now
    if isinstance(eff, str):
        eff = datetime.fromisoformat(eff)
    exp = expiry_date
    if isinstance(exp, str):
        exp = datetime.fromisoformat(exp)

    conn.execute(
        text("""
            INSERT INTO academic_announcements (
                id, title, content, source_url, audience, status,
                effective_date, expiry_date, created_by, created_at
            ) VALUES (
                :id, :title, :content, :source_url, :audience, 'draft',
                :effective_date, :expiry_date, :created_by, :created_at
            )
        """),
        {
            "id": ann_id,
            "title": title,
            "content": content,
            "source_url": source_url,
            "audience": audience,
            "effective_date": eff,
            "expiry_date": exp,
            "created_by": created_by,
            "created_at": now,
        },
    )
    return get_announcement_record(conn, ann_id)  # type: ignore


def get_announcement_record(conn, announcement_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        text("SELECT * FROM academic_announcements WHERE id = :id"),
        {"id": announcement_id},
    ).fetchone()
    return _row_to_dict(row)


def list_announcement_records(
    conn,
    status: str | None = None,
    audience: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    conditions = []
    params: dict[str, Any] = {"limit": max(1, min(limit, 100)), "offset": max(0, offset)}

    if status and status != "all":
        conditions.append("status = :status")
        params["status"] = status
    if audience and audience != "all":
        conditions.append("audience = :audience")
        params["audience"] = audience
    if q and q.strip():
        conditions.append("(title ILIKE :q OR content ILIKE :q)")
        params["q"] = f"%{q.strip()}%"

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    total = conn.execute(
        text(f"SELECT COUNT(*) FROM academic_announcements {where}"),
        params,
    ).scalar() or 0

    rows = conn.execute(
        text(f"""
            SELECT * FROM academic_announcements
            {where}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    ).fetchall()

    return [_row_to_dict(r) for r in rows], int(total)


def update_announcement_status_record(
    conn,
    announcement_id: str,
    new_status: str,
    actor_id: str = "admin",
) -> dict[str, Any] | None:
    now = datetime.now(timezone.utc)
    published_clause = ", published_at = :now" if new_status == "published" else ""

    conn.execute(
        text(f"""
            UPDATE academic_announcements
            SET status = :status {published_clause}
            WHERE id = :id
        """),
        {"id": announcement_id, "status": new_status, "now": now},
    )
    return get_announcement_record(conn, announcement_id)


def delete_announcement_record(conn, announcement_id: str) -> bool:
    res = conn.execute(
        text("DELETE FROM academic_announcements WHERE id = :id"),
        {"id": announcement_id},
    )
    return res.rowcount > 0


def get_active_announcements_record(conn, audience: str = "all") -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    params: dict[str, Any] = {"now": now}
    aud_clause = ""
    if audience != "all":
        aud_clause = "AND (audience = 'all' OR audience = :audience)"
        params["audience"] = audience

    rows = conn.execute(
        text(f"""
            SELECT * FROM academic_announcements
            WHERE status = 'published'
              AND effective_date <= :now
              AND (expiry_date IS NULL OR expiry_date > :now)
              {aud_clause}
            ORDER BY effective_date DESC
        """),
        params,
    ).fetchall()
    return [_row_to_dict(r) for r in rows]
