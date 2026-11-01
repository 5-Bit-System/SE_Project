"""Business logic and validation service for academic announcements."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from app.announcements.repository import (
    create_announcement_record,
    delete_announcement_record,
    get_active_announcements_record,
    get_announcement_record,
    list_announcement_records,
    update_announcement_status_record,
)
from app.audit.service import log_admin_action
from app.integrations.daotao.store import engine

_mem_announcements: dict[str, dict[str, Any]] = {}


def _validate_source_url(url: str) -> str:
    cleaned = (url or "").strip()
    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("Invalid source_url: Must be an attributable HTTP or HTTPS URL.")
    return cleaned


def create_announcement(
    title: str,
    content: str,
    source_url: str,
    audience: str = "all",
    effective_date: str | None = None,
    expiry_date: str | None = None,
    created_by: str = "admin",
    conn=None,
) -> dict[str, Any]:
    """Create a new draft academic announcement."""
    title_clean = (title or "").strip()
    if not title_clean or len(title_clean) > 255:
        raise ValueError("Title must be between 1 and 255 characters.")

    content_clean = (content or "").strip()
    if not content_clean:
        raise ValueError("Content cannot be empty.")

    url_clean = _validate_source_url(source_url)

    if audience not in ("all", "students", "faculty"):
        raise ValueError("Audience must be 'all', 'students', or 'faculty'.")

    now = datetime.now(timezone.utc)
    eff = datetime.fromisoformat(effective_date) if effective_date else now
    exp = datetime.fromisoformat(expiry_date) if expiry_date else None

    if exp and exp <= eff:
        raise ValueError("expiry_date must be after effective_date.")

    if conn is not None:
        rec = create_announcement_record(
            conn,
            title=title_clean,
            content=content_clean,
            source_url=url_clean,
            audience=audience,
            effective_date=eff,
            expiry_date=exp,
            created_by=created_by,
        )
        try:
            log_admin_action(
                conn=conn,
                actor_id=created_by,
                actor_email=None,
                action="admin:announcement:create",
                target_type="announcement",
                target_id=rec["id"],
                details={"title": title_clean, "source_url": url_clean, "audience": audience},
            )
        except Exception:
            pass
        return rec

    try:
        with engine().begin() as c:
            rec = create_announcement_record(
                c,
                title=title_clean,
                content=content_clean,
                source_url=url_clean,
                audience=audience,
                effective_date=eff,
                expiry_date=exp,
                created_by=created_by,
            )
            try:
                log_admin_action(
                    conn=c,
                    actor_id=created_by,
                    actor_email=None,
                    action="admin:announcement:create",
                    target_type="announcement",
                    target_id=rec["id"],
                    details={"title": title_clean, "source_url": url_clean, "audience": audience},
                )
            except Exception:
                pass
            return rec
    except Exception:
        # In-memory fallback
        ann_id = str(uuid.uuid4())
        rec = {
            "id": ann_id,
            "title": title_clean,
            "content": content_clean,
            "source_url": url_clean,
            "audience": audience,
            "status": "draft",
            "effective_date": eff.isoformat(),
            "expiry_date": exp.isoformat() if exp else None,
            "created_by": created_by,
            "created_at": now.isoformat(),
            "published_at": None,
        }
        _mem_announcements[ann_id] = rec
        return rec


def get_announcement(announcement_id: str, conn=None) -> dict[str, Any] | None:
    if conn is not None:
        return get_announcement_record(conn, announcement_id)
    try:
        with engine().begin() as c:
            return get_announcement_record(c, announcement_id)
    except Exception:
        return _mem_announcements.get(announcement_id)


def list_announcements(
    status: str | None = None,
    audience: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    conn=None,
) -> tuple[list[dict[str, Any]], int]:
    if conn is not None:
        return list_announcement_records(
            conn, status=status, audience=audience, q=q, limit=limit, offset=offset
        )
    try:
        with engine().begin() as c:
            return list_announcement_records(
                c, status=status, audience=audience, q=q, limit=limit, offset=offset
            )
    except Exception:
        items = list(_mem_announcements.values())
        if status and status != "all":
            items = [i for i in items if i.get("status") == status]
        if audience and audience != "all":
            items = [i for i in items if i.get("audience") == audience]
        if q and q.strip():
            items = [i for i in items if q.lower() in i.get("title", "").lower() or q.lower() in i.get("content", "").lower()]
        total = len(items)
        return items[offset:offset + limit], total


def publish_announcement(announcement_id: str, actor_id: str = "admin", conn=None) -> dict[str, Any]:
    if conn is not None:
        existing = get_announcement_record(conn, announcement_id)
        if not existing:
            raise ValueError(f"Announcement {announcement_id} not found.")
        updated = update_announcement_status_record(conn, announcement_id, "published", actor_id)
        try:
            log_admin_action(
                conn=conn,
                actor_id=actor_id,
                actor_email=None,
                action="admin:announcement:publish",
                target_type="announcement",
                target_id=announcement_id,
                details={"title": existing["title"]},
            )
        except Exception:
            pass
        return updated  # type: ignore

    try:
        with engine().begin() as c:
            existing = get_announcement_record(c, announcement_id)
            if not existing:
                raise ValueError(f"Announcement {announcement_id} not found.")
            updated = update_announcement_status_record(c, announcement_id, "published", actor_id)
            try:
                log_admin_action(
                    conn=c,
                    actor_id=actor_id,
                    actor_email=None,
                    action="admin:announcement:publish",
                    target_type="announcement",
                    target_id=announcement_id,
                    details={"title": existing["title"]},
                )
            except Exception:
                pass
            return updated  # type: ignore
    except Exception:
        if announcement_id not in _mem_announcements:
            raise ValueError(f"Announcement {announcement_id} not found.")
        now = datetime.now(timezone.utc)
        _mem_announcements[announcement_id]["status"] = "published"
        _mem_announcements[announcement_id]["published_at"] = now.isoformat()
        return _mem_announcements[announcement_id]


def expire_announcement(announcement_id: str, actor_id: str = "admin", conn=None) -> dict[str, Any]:
    if conn is not None:
        existing = get_announcement_record(conn, announcement_id)
        if not existing:
            raise ValueError(f"Announcement {announcement_id} not found.")
        updated = update_announcement_status_record(conn, announcement_id, "expired", actor_id)
        try:
            log_admin_action(
                conn=conn,
                actor_id=actor_id,
                actor_email=None,
                action="admin:announcement:expire",
                target_type="announcement",
                target_id=announcement_id,
                details={"title": existing["title"]},
            )
        except Exception:
            pass
        return updated  # type: ignore

    try:
        with engine().begin() as c:
            existing = get_announcement_record(c, announcement_id)
            if not existing:
                raise ValueError(f"Announcement {announcement_id} not found.")
            updated = update_announcement_status_record(c, announcement_id, "expired", actor_id)
            try:
                log_admin_action(
                    conn=c,
                    actor_id=actor_id,
                    actor_email=None,
                    action="admin:announcement:expire",
                    target_type="announcement",
                    target_id=announcement_id,
                    details={"title": existing["title"]},
                )
            except Exception:
                pass
            return updated  # type: ignore
    except Exception:
        if announcement_id not in _mem_announcements:
            raise ValueError(f"Announcement {announcement_id} not found.")
        _mem_announcements[announcement_id]["status"] = "expired"
        return _mem_announcements[announcement_id]


def delete_announcement(announcement_id: str, actor_id: str = "admin", conn=None) -> bool:
    if conn is not None:
        existing = get_announcement_record(conn, announcement_id)
        if not existing:
            return False
        res = delete_announcement_record(conn, announcement_id)
        try:
            log_admin_action(
                conn=conn,
                actor_id=actor_id,
                actor_email=None,
                action="admin:announcement:delete",
                target_type="announcement",
                target_id=announcement_id,
                details={"title": existing["title"]},
            )
        except Exception:
            pass
        return res

    try:
        with engine().begin() as c:
            existing = get_announcement_record(c, announcement_id)
            if not existing:
                return False
            res = delete_announcement_record(c, announcement_id)
            try:
                log_admin_action(
                    conn=c,
                    actor_id=actor_id,
                    actor_email=None,
                    action="admin:announcement:delete",
                    target_type="announcement",
                    target_id=announcement_id,
                    details={"title": existing["title"]},
                )
            except Exception:
                pass
            return res
    except Exception:
        if announcement_id in _mem_announcements:
            del _mem_announcements[announcement_id]
            return True
        return False


def get_public_announcements(audience: str = "all", conn=None) -> list[dict[str, Any]]:
    if conn is not None:
        return get_active_announcements_record(conn, audience=audience)
    try:
        with engine().begin() as c:
            return get_active_announcements_record(c, audience=audience)
    except Exception:
        now = datetime.now(timezone.utc).isoformat()
        res = []
        for a in _mem_announcements.values():
            if a.get("status") == "published" and a.get("effective_date", "") <= now:
                if not a.get("expiry_date") or a.get("expiry_date") > now:
                    if audience == "all" or a.get("audience") in ("all", audience):
                        res.append(a)
        return res


def get_announcements_summary(conn=None) -> dict[str, int]:
    rows, total = list_announcements(limit=1000, conn=conn)
    published = sum(1 for r in rows if r["status"] == "published")
    expired = sum(1 for r in rows if r["status"] == "expired")
    draft = sum(1 for r in rows if r["status"] == "draft")
    return {"total": total, "published": published, "expired": expired, "draft": draft}
