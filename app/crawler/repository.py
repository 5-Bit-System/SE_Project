"""Repository for crawler sources and job lifecycle persistence."""

import json
import uuid
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


# ---------------------------------------------------------------------------
# Crawler Sources
# ---------------------------------------------------------------------------


def list_sources(conn, active_only: bool = False) -> list[dict[str, Any]]:
    query = "SELECT * FROM crawler_sources"
    if active_only:
        query += " WHERE is_active = true"
    query += " ORDER BY created_at ASC"
    rows = conn.execute(text(query)).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_source(conn, source_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        text("SELECT * FROM crawler_sources WHERE id = :id"),
        {"id": source_id},
    ).fetchone()
    return _row_to_dict(row)


def create_source(
    conn,
    name: str,
    base_url: str,
    schedule: str = "manual",
    depth_limit: int = 3,
    is_active: bool = True,
    allow_patterns: list[str] | None = None,
    deny_patterns: list[str] | None = None,
    source_id: str | None = None,
) -> dict[str, Any]:
    sid = source_id or f"src_{uuid.uuid4().hex[:10]}"
    conn.execute(
        text("""
            INSERT INTO crawler_sources (
                id, name, base_url, schedule, depth_limit, is_active,
                allow_patterns, deny_patterns, created_at, updated_at
            ) VALUES (
                :id, :name, :base_url, :schedule, :depth_limit, :is_active,
                CAST(:allow_patterns AS jsonb), CAST(:deny_patterns AS jsonb), now(), now()
            )
        """),
        {
            "id": sid,
            "name": name,
            "base_url": base_url,
            "schedule": schedule,
            "depth_limit": depth_limit,
            "is_active": is_active,
            "allow_patterns": json.dumps(allow_patterns or []),
            "deny_patterns": json.dumps(deny_patterns or []),
        },
    )
    return get_source(conn, sid)


def update_source(
    conn,
    source_id: str,
    name: str | None = None,
    base_url: str | None = None,
    schedule: str | None = None,
    depth_limit: int | None = None,
    is_active: bool | None = None,
    allow_patterns: list[str] | None = None,
    deny_patterns: list[str] | None = None,
) -> dict[str, Any] | None:
    src = get_source(conn, source_id)
    if not src:
        return None

    new_name = name if name is not None else src["name"]
    new_url = base_url if base_url is not None else src["base_url"]
    new_schedule = schedule if schedule is not None else src["schedule"]
    new_depth = depth_limit if depth_limit is not None else src["depth_limit"]
    new_active = is_active if is_active is not None else src["is_active"]
    new_allow = (
        json.dumps(allow_patterns)
        if allow_patterns is not None
        else json.dumps(src["allow_patterns"])
    )
    new_deny = (
        json.dumps(deny_patterns) if deny_patterns is not None else json.dumps(src["deny_patterns"])
    )

    conn.execute(
        text("""
            UPDATE crawler_sources
            SET name = :name,
                base_url = :base_url,
                schedule = :schedule,
                depth_limit = :depth_limit,
                is_active = :is_active,
                allow_patterns = CAST(:allow_patterns AS jsonb),
                deny_patterns = CAST(:deny_patterns AS jsonb),
                updated_at = now()
            WHERE id = :id
        """),
        {
            "id": source_id,
            "name": new_name,
            "base_url": new_url,
            "schedule": new_schedule,
            "depth_limit": new_depth,
            "is_active": new_active,
            "allow_patterns": new_allow,
            "deny_patterns": new_deny,
        },
    )
    return get_source(conn, source_id)


def toggle_source(conn, source_id: str, is_active: bool) -> dict[str, Any] | None:
    conn.execute(
        text("""
            UPDATE crawler_sources
            SET is_active = :is_active,
                updated_at = now()
            WHERE id = :id
        """),
        {"id": source_id, "is_active": is_active},
    )
    return get_source(conn, source_id)


def seed_default_sources_if_empty(conn) -> list[dict[str, Any]]:

    defaults = [
        {
            "source_id": "src_hus_main",
            "name": "Cổng thông tin đào tạo Đại học KHTN",
            "base_url": "https://hus.vnu.edu.vn/dao-tao/dai-hoc",
            "schedule": "0 2 * * *",
            "depth_limit": 3,
            "is_active": True,
            "allow_patterns": ["https://hus.vnu.edu.vn/dao-tao/*"],
        },
        {
            "source_id": "src_hus_tuyensinh",
            "name": "Cổng tuyển sinh & Giới thiệu ngành HUS",
            "base_url": "https://tuyensinh.hus.vnu.edu.vn/dai-hoc",
            "schedule": "0 3 * * 1",
            "depth_limit": 2,
            "is_active": True,
            "allow_patterns": ["https://tuyensinh.hus.vnu.edu.vn/*"],
        },
        {
            "source_id": "src_hus_mim",
            "name": "Khoa Toán - Cơ - Tin học HUS",
            "base_url": "https://mim.hus.vnu.edu.vn/vi/cacctrdaotao",
            "schedule": "manual",
            "depth_limit": 2,
            "is_active": True,
            "allow_patterns": ["https://mim.hus.vnu.edu.vn/*"],
        },
    ]

    for d in defaults:
        if not get_source(conn, d["source_id"]):
            create_source(conn, **d)

    return list_sources(conn)


# ---------------------------------------------------------------------------
# Crawler Jobs
# ---------------------------------------------------------------------------


def list_jobs(
    conn, source_id: str | None = None, status: str | None = None, limit: int = 50
) -> list[dict[str, Any]]:
    query = "SELECT * FROM crawler_jobs WHERE 1=1"
    params: dict[str, Any] = {"limit": limit}
    if source_id:
        query += " AND source_id = :source_id"
        params["source_id"] = source_id
    if status:
        query += " AND status = :status"
        params["status"] = status
    query += " ORDER BY created_at DESC LIMIT :limit"

    rows = conn.execute(text(query), params).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_job(conn, job_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        text("SELECT * FROM crawler_jobs WHERE id = :id"),
        {"id": job_id},
    ).fetchone()
    return _row_to_dict(row)


def create_job(
    conn,
    source_id: str,
    created_by: str | uuid.UUID | None = None,
    job_id: str | None = None,
) -> dict[str, Any]:
    jid = job_id or f"job_{uuid.uuid4().hex[:12]}"
    conn.execute(
        text("""
            INSERT INTO crawler_jobs (
                id, source_id, status, pages_discovered, pages_crawled,
                documents_found, started_at, created_by, created_at
            ) VALUES (
                :id, :source_id, 'running', 0, 0, 0, now(), :created_by, now()
            )
        """),
        {"id": jid, "source_id": source_id, "created_by": _safe_uuid(created_by)},
    )
    return get_job(conn, jid)


def update_job_progress(
    conn,
    job_id: str,
    pages_discovered: int | None = None,
    pages_crawled: int | None = None,
    documents_found: int | None = None,
) -> dict[str, Any] | None:
    job = get_job(conn, job_id)
    if not job:
        return None

    disc = pages_discovered if pages_discovered is not None else job["pages_discovered"]
    crawled = pages_crawled if pages_crawled is not None else job["pages_crawled"]
    found = documents_found if documents_found is not None else job["documents_found"]

    conn.execute(
        text("""
            UPDATE crawler_jobs
            SET pages_discovered = :disc,
                pages_crawled = :crawled,
                documents_found = :found
            WHERE id = :id
        """),
        {"id": job_id, "disc": disc, "crawled": crawled, "found": found},
    )
    return get_job(conn, job_id)


def pause_job(conn, job_id: str) -> dict[str, Any] | None:
    job = get_job(conn, job_id)
    if not job or job["status"] != "running":
        return None

    conn.execute(
        text("UPDATE crawler_jobs SET status = 'paused' WHERE id = :id"),
        {"id": job_id},
    )
    return get_job(conn, job_id)


def resume_job(conn, job_id: str) -> dict[str, Any] | None:
    job = get_job(conn, job_id)
    if not job or job["status"] != "paused":
        return None

    conn.execute(
        text("UPDATE crawler_jobs SET status = 'running' WHERE id = :id"),
        {"id": job_id},
    )
    return get_job(conn, job_id)


def complete_job(
    conn,
    job_id: str,
    pages_discovered: int | None = None,
    pages_crawled: int | None = None,
    documents_found: int | None = None,
) -> dict[str, Any] | None:
    job = get_job(conn, job_id)
    if not job or job["status"] not in ("running", "paused"):
        return None

    disc = pages_discovered if pages_discovered is not None else job["pages_discovered"]
    crawled = pages_crawled if pages_crawled is not None else job["pages_crawled"]
    found = documents_found if documents_found is not None else job["documents_found"]

    conn.execute(
        text("""
            UPDATE crawler_jobs
            SET status = 'completed',
                pages_discovered = :disc,
                pages_crawled = :crawled,
                documents_found = :found,
                completed_at = now()
            WHERE id = :id
        """),
        {"id": job_id, "disc": disc, "crawled": crawled, "found": found},
    )
    return get_job(conn, job_id)


def fail_job(conn, job_id: str, error_message: str | None = None) -> dict[str, Any] | None:
    job = get_job(conn, job_id)
    if not job or job["status"] not in ("running", "paused", "queued"):
        return None

    conn.execute(
        text("""
            UPDATE crawler_jobs
            SET status = 'failed',
                error_message = :err,
                completed_at = now()
            WHERE id = :id
        """),
        {"id": job_id, "err": error_message or "Unknown crawler error"},
    )
    return get_job(conn, job_id)


def cancel_job(conn, job_id: str) -> dict[str, Any] | None:
    job = get_job(conn, job_id)
    if not job or job["status"] not in ("running", "paused", "queued"):
        return None

    conn.execute(
        text("""
            UPDATE crawler_jobs
            SET status = 'cancelled',
                completed_at = now()
            WHERE id = :id
        """),
        {"id": job_id},
    )
    return get_job(conn, job_id)
