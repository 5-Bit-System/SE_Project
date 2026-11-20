"""Audit logging service with strict data minimization and redaction."""

from __future__ import annotations

import copy
import uuid
from typing import Any

from app.audit.repository import (
    get_audit_summary_metrics,
    insert_audit_log,
    query_audit_logs,
)

SENSITIVE_KEY_PATTERNS = {
    "password",
    "secret",
    "token",
    "cookie",
    "session",
    "key",
    "authorization",
    "raw_content",
    "markdown_content",
    "vnu_password",
    "access_token",
    "refresh_token",
    "credential",
    "hash_secret",
}


def redact_sensitive_payload(data: Any, depth: int = 0) -> Any:
    """Recursively redact sensitive credentials, tokens, and unrestricted bodies."""
    if depth > 8:
        return "[MAX_DEPTH]"

    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(pattern in k_lower for pattern in SENSITIVE_KEY_PATTERNS):
                cleaned[k] = "[REDACTED]"
            elif isinstance(v, (dict, list)):
                cleaned[k] = redact_sensitive_payload(v, depth + 1)
            elif isinstance(v, str) and len(v) > 500:
                cleaned[k] = v[:200] + f"… [TRUNCATED {len(v)} chars]"
            else:
                cleaned[k] = v
        return cleaned

    if isinstance(data, list):
        if len(data) > 50:
            return [redact_sensitive_payload(item, depth + 1) for item in data[:50]] + [
                f"… [TRUNCATED {len(data) - 50} items]"
            ]
        return [redact_sensitive_payload(item, depth + 1) for item in data]

    if isinstance(data, str) and len(data) > 500:
        return data[:200] + f"… [TRUNCATED {len(data)} chars]"

    return data


def log_admin_action(
    conn=None,
    actor_id: str | uuid.UUID | None = None,
    actor_email: str | None = None,
    action: str = "",
    target_type: str = "",
    target_id: str = "",
    result: str = "ok",
    summary: str = "",
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> dict[str, Any]:
    """Sanitize details, enforce append-only audit invariant, and record action."""
    safe_details = redact_sensitive_payload(copy.deepcopy(details or {}))
    if conn is None:
        return {
            "id": str(uuid.uuid4()),
            "actor_id": str(actor_id) if actor_id else None,
            "actor_email": actor_email,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "result": result,
            "summary": summary,
            "details": safe_details,
            "ip_address": ip_address,
        }
    return insert_audit_log(
        conn=conn,
        actor_id=actor_id,
        actor_email=actor_email,
        action=action,
        target_type=target_type,
        target_id=target_id,
        result=result,
        summary=summary,
        details=safe_details,
        ip_address=ip_address,
    )


def get_audit_trail(
    conn,
    action_group: str | None = None,
    target_type: str | None = None,
    actor_id: str | None = None,
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Retrieve filtered, paginated audit records."""
    bounded_limit = max(1, min(limit, 200))
    bounded_offset = max(0, offset)
    return query_audit_logs(
        conn=conn,
        action_group=action_group,
        target_type=target_type,
        actor_id=actor_id,
        query=query,
        limit=bounded_limit,
        offset=bounded_offset,
    )


def get_audit_metrics(conn) -> dict[str, Any]:
    """Retrieve operational KPIs for admin audit view."""
    return get_audit_summary_metrics(conn)
