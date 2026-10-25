"""Transactional persistence. Every read/write is scoped by the authenticated owner."""

import json
import uuid
from contextlib import nullcontext
from functools import lru_cache

from sqlalchemy import create_engine, text

from app.config import get_settings
from app.integrations.daotao.snapshot import PortalFailure


@lru_cache
def engine():
    settings = get_settings()
    if settings.storage_backend != "postgres" or settings.database_model != "hus":
        raise PortalFailure("storage_unavailable")
    return create_engine(settings.database_url, pool_pre_ping=True, hide_parameters=True,
                         connect_args={"connect_timeout": 10})


def owner(subject):
    with engine().begin() as conn:
        row = conn.execute(text("""
            INSERT INTO portal_users(id, subject) VALUES (:id, :subject)
            ON CONFLICT(provider, subject) DO UPDATE SET subject=EXCLUDED.subject
            RETURNING id, generation
        """), {"id": str(uuid.uuid4()), "subject": subject}).mappings().one()
        return str(row["id"]), row["generation"]


def profile(owner_id):
    with engine().connect() as conn:
        row = conn.execute(text("""
            SELECT u.subject, u.profile, s.payload, s.fetched_at
            FROM portal_users u LEFT JOIN portal_transcript_snapshots s
              ON s.owner=u.id AND s.id=u.current_snapshot_id WHERE u.id=:owner
        """), {"owner": owner_id}).mappings().one_or_none()
        if row is None:
            raise PortalFailure("session_expired")
        details = dict(row["profile"])
        last_synced_at = details.pop("_last_synced_at", None)
        return {"subject": row["subject"], "profile": details,
                "last_synced_at": last_synced_at,
                "snapshot": row["payload"],
                "fetched_at": row["fetched_at"].isoformat() if row["fetched_at"] else None}


def save(owner_id, generation, payload, source_profile=None, *, connection=None):
    with (engine().begin() if connection is None else nullcontext(connection)) as conn:
        user = conn.execute(text("SELECT * FROM portal_users WHERE id=:id FOR UPDATE"),
                            {"id": owner_id}).mappings().one_or_none()
        if user is None or user["generation"] != generation:
            raise PortalFailure("cancelled")
        if source_profile is not None:
            # Source display labels only. Never an academic program/policy binding.
            details = {key: value if isinstance(value, str) and 0 < len(value) <= 200 else None
                       for key in ("name", "program", "cohort")
                       for value in [source_profile.get(key)]}
            if "_last_synced_at" in user["profile"]:
                details["_last_synced_at"] = user["profile"]["_last_synced_at"]
            previous = user["profile"] or {}
            if (all(previous.get(key) == details.get(key) for key in ("program", "cohort"))
                    and isinstance(previous.get("academic_binding"), dict)):
                details["academic_binding"] = previous["academic_binding"]
            conn.execute(text("UPDATE portal_users SET profile=CAST(:profile AS JSONB) WHERE id=:id"),
                         {"profile": json.dumps(details), "id": owner_id})
        existing = conn.execute(text("""
            SELECT id FROM portal_transcript_snapshots WHERE owner=:owner AND digest=:digest
        """), {"owner": owner_id, "digest": payload["digest"]}).scalar()
        if existing:
            if str(existing) == str(user["current_snapshot_id"]):
                mark_synced(conn, owner_id)
            return "unchanged"
        # Until pagination/filter completion is proven, never replace prior data.
        if user["current_snapshot_id"] and payload["completeness"] != "complete":
            raise PortalFailure("incomplete_snapshot")
        snapshot_id = str(uuid.uuid4())
        conn.execute(text("""
            INSERT INTO portal_transcript_snapshots(id,owner,digest,completeness,payload)
            VALUES (:id,:owner,:digest,:completeness,CAST(:payload AS JSONB))
        """), {"id": snapshot_id, "owner": owner_id, "digest": payload["digest"],
                "completeness": payload["completeness"], "payload": json.dumps(payload)})
        for attempt in payload["attempts"]:
            conn.execute(text("""
                INSERT INTO portal_transcript_attempts(snapshot,row_key,source)
                VALUES (:id,:key,CAST(:source AS JSONB))
            """), {"id": snapshot_id, "key": attempt["row_key"],
                    "source": json.dumps(attempt)})
        conn.execute(text("UPDATE portal_users SET current_snapshot_id=:snapshot WHERE id=:id"),
                     {"snapshot": snapshot_id, "id": owner_id})
        conn.execute(text("""
            DELETE FROM portal_transcript_snapshots WHERE owner=:owner AND id NOT IN
              (SELECT id FROM portal_transcript_snapshots WHERE owner=:owner
               ORDER BY fetched_at DESC LIMIT 2)
        """), {"owner": owner_id})
        mark_synced(conn, owner_id)
        return "saved"


def save_academic_binding(owner_id, generation, binding, expected_snapshot_digest,
                          expected_source_scope, *, connection=None):
    """Write a validated confirmation under the owner's current source lock."""
    from app.program_bindings import binding_current, source_scope

    with (engine().begin() if connection is None else nullcontext(connection)) as conn:
        user = conn.execute(text("SELECT * FROM portal_users WHERE id=:id FOR UPDATE"),
                            {"id": owner_id}).mappings().one_or_none()
        if user is None or user["generation"] != generation:
            raise PortalFailure("cancelled")
        profile = user["profile"] or {}
        current = conn.execute(text("""
            SELECT digest FROM portal_transcript_snapshots WHERE id=:snapshot AND owner=:owner
        """), {"snapshot": user["current_snapshot_id"], "owner": owner_id}).scalar_one_or_none()
        if (current != expected_snapshot_digest or source_scope(profile) != expected_source_scope
                or not binding_current({**profile, "academic_binding": binding})):
            raise PortalFailure("context_changed")
        conn.execute(text("UPDATE portal_users SET profile=CAST(:profile AS JSONB) WHERE id=:id"),
                     {"id": owner_id, "profile": json.dumps({**profile, "academic_binding": binding})})
    return "confirmed"


def mark_synced(conn, owner_id):
    # Server-owned metadata, separate from the immutable transcript payload/time.
    conn.execute(text("""
        UPDATE portal_users
        SET profile=jsonb_set(profile, '{_last_synced_at}', to_jsonb(CURRENT_TIMESTAMP))
        WHERE id=:owner
    """), {"owner": owner_id})


def clear(owner_id, *, connection=None):
    with (engine().begin() if connection is None else nullcontext(connection)) as conn:
        conn.execute(text("""
            UPDATE portal_users SET current_snapshot_id=NULL, profile='{}', generation=generation+1
            WHERE id=:owner
        """), {"owner": owner_id})
        conn.execute(text("DELETE FROM portal_transcript_snapshots WHERE owner=:owner"),
                     {"owner": owner_id})
        conn.execute(text("DELETE FROM portal_users WHERE id=:owner"), {"owner": owner_id})
