"""Repository for privileged admin action audit logs."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import text


def _safe_uuid(val: Any) -> uuid.UUID | None:
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except Exception:
        return None


def insert_audit_log(
    conn,
    actor_id: str | uuid.UUID | None,
    actor_email: str | None,
    action: str,
    target_type: str,
    target_id: str,
    result: str = "ok",
    summary: str = "",
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> dict[str, Any]:
    """Insert an append-only privileged audit log entry."""
    details_json = json.dumps(details or {})
    row = (
        conn.execute(
            text("""
                INSERT INTO admin_audit_logs (
                    actor_id, actor_email, action, target_type, target_id,
                    result, summary, details, ip_address, created_at
                ) VALUES (
                    :actor_id, :actor_email, :action, :target_type, :target_id,
                    :result, :summary, CAST(:details AS jsonb), :ip_address, now()
                )
                RETURNING id, actor_id, actor_email, action, target_type, target_id,
                          result, summary, details, ip_address, created_at
            """),
            {
                "actor_id": _safe_uuid(actor_id),
                "actor_email": actor_email,
                "action": action,
                "target_type": target_type,
                "target_id": str(target_id),
                "result": result,
                "summary": summary,
                "details": details_json,
                "ip_address": ip_address,
            },
        )
        .mappings()
        .one()
    )
    result_dict = dict(row)
    if hasattr(result_dict.get("created_at"), "isoformat"):
        result_dict["created_at"] = result_dict["created_at"].isoformat()
    if result_dict.get("actor_id"):
        result_dict["actor_id"] = str(result_dict["actor_id"])
    return result_dict


def query_audit_logs(
    conn,
    action_group: str | None = None,
    target_type: str | None = None,
    actor_id: str | None = None,
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Query paginated audit logs with filtering and text search."""
    where_clauses = ["1=1"]
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    if action_group and action_group != "all":
        where_clauses.append("(action = :action_group OR action LIKE :action_prefix)")
        params["action_group"] = action_group
        params["action_prefix"] = f"{action_group}.%"

    if target_type and target_type != "all":
        where_clauses.append("target_type = :target_type")
        params["target_type"] = target_type

    if actor_id:
        safe_act = _safe_uuid(actor_id)
        if safe_act:
            where_clauses.append("actor_id = :actor_id")
            params["actor_id"] = safe_act

    if query:
        where_clauses.append("(summary ILIKE :q OR target_id ILIKE :q OR actor_email ILIKE :q)")
        params["q"] = f"%{query.strip()}%"

    where_sql = " AND ".join(where_clauses)

    count_sql = f"SELECT count(*) FROM admin_audit_logs WHERE {where_sql}"
    total = conn.execute(text(count_sql), params).scalar_one()

    data_sql = f"""
        SELECT id, actor_id, actor_email, action, target_type, target_id,
               result, summary, details, ip_address, created_at
        FROM admin_audit_logs
        WHERE {where_sql}
        ORDER BY created_at DESC, id DESC
        LIMIT :limit OFFSET :offset
    """
    rows = conn.execute(text(data_sql), params).mappings().all()

    items = []
    for r in rows:
        d = dict(r)
        if hasattr(d.get("created_at"), "isoformat"):
            d["created_at"] = d["created_at"].isoformat()
        if d.get("actor_id"):
            d["actor_id"] = str(d["actor_id"])
        items.append(d)

    return items, total


def get_audit_summary_metrics(conn) -> dict[str, Any]:
    """Compute high-level summary KPIs for audit dashboard."""
    total_count = conn.execute(text("SELECT count(*) FROM admin_audit_logs")).scalar_one()

    last_24h = conn.execute(
        text(
            "SELECT count(*) FROM admin_audit_logs WHERE created_at >= now() - interval '24 hours'"
        )
    ).scalar_one()

    warnings_count = conn.execute(
        text("SELECT count(*) FROM admin_audit_logs WHERE result != 'ok'")
    ).scalar_one()

    return {
        "total_events": total_count,
        "events_last_24h": last_24h,
        "failed_or_warn_count": warnings_count,
    }
