"""Plan existing-document taxonomy corrections; apply only an explicitly approved plan.

Default operation reads an explicit inventory JSON or an explicitly named database
URL environment variable. It never loads .env or app settings. Source Markdown and
published rows are never rewritten. Approved/published corrections use the existing
metadata service to create a pending replacement, with audit in the same transaction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.audit.service import log_admin_action
from app.crawler.document_review_service import (
    compute_content_hash,
    normalize_crawled_url,
    parse_frontmatter,
    resolve_document_major,
    update_document_metadata,
)
from app.curriculum.transactions import publication_lock

DEFAULT_DOCUMENTS = Path("data/hus/processed/documents")
INVENTORY_COLUMNS = (
    "id", "url", "content_hash", "title", "major", "doc_type", "metadata_json",
    "review_status", "is_published",
)


def _sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _inventory(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if not isinstance(row, dict) or any(key not in row for key in INVENTORY_COLUMNS):
            raise ValueError("Inventory rows must contain all document fingerprint fields")
        if not isinstance(row["is_published"], bool):
            raise ValueError("Inventory is_published must be a JSON boolean")
        if row["review_status"] not in {"pending", "approved", "rejected"}:
            raise ValueError("Inventory contains an unsupported review_status")
        if not isinstance(row["metadata_json"], dict):
            raise ValueError("Inventory metadata_json must be an object")
        projected = {key: row[key] for key in INVENTORY_COLUMNS}
        for key in ("id", "url", "content_hash", "title", "major", "doc_type"):
            if not isinstance(projected[key], str) or not projected[key]:
                raise ValueError(f"Inventory {key} must be a nonempty string")
        result.append(projected)
    result.sort(key=lambda row: row["id"])
    if len({row["id"] for row in result}) != len(result):
        raise ValueError("Inventory contains duplicate document IDs")
    return result


def build_plan(docs_dir: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a deterministic plan bound to source bytes and complete DB inventory."""
    if not docs_dir.is_dir():
        raise ValueError("Document directory does not exist")
    inventory = _inventory(rows)
    sources: dict[str, list[dict[str, Any]]] = {}
    manifest = []
    for path in sorted(docs_dir.rglob("*.md")):
        raw_bytes = path.read_bytes()
        metadata, content = parse_frontmatter(raw_bytes.decode("utf-8"))
        relative_path = path.relative_to(docs_dir).as_posix()
        manifest.append({
            "path": relative_path,
            "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        })
        url = normalize_crawled_url(str(metadata.get("url") or ""))
        if urlsplit(url).scheme not in {"http", "https"} or not metadata.get("title"):
            continue
        sources.setdefault(url, []).append({
            "path": relative_path,
            "major": resolve_document_major(metadata, path),
            "content_hash": compute_content_hash(content),
        })

    actions = []
    conflicts = []
    for row in inventory:
        candidates = sources.get(normalize_crawled_url(row["url"]), [])
        if not candidates:
            continue
        targets = {(source["major"], source["content_hash"]) for source in candidates}
        if len(targets) != 1:
            conflicts.append({"id": row["id"], "reason": "ambiguous_source_url"})
            continue
        target_major, source_hash = next(iter(targets))
        if row["major"] == target_major:
            continue
        if row["content_hash"] != source_hash:
            conflicts.append({"id": row["id"], "reason": "source_content_hash_changed"})
            continue
        replacement = row["is_published"] or row["review_status"] == "approved"
        if replacement and any(
            other["metadata_json"].get("previous_document_id") == row["id"]
            and normalize_crawled_url(other["url"]) == normalize_crawled_url(row["url"])
            and other["content_hash"] == source_hash
            and other["major"] == target_major
            and other["review_status"] in {"pending", "approved"}
            for other in inventory
        ):
            # A prior application already prepared this correction for review.
            continue
        actions.append({
            "document_id": row["id"],
            "expected_fingerprint": _sha256(row),
            "current_major": row["major"],
            "target_major": target_major,
            "action": "create_pending_replacement" if replacement else "update_draft_metadata",
            "source_paths": sorted(source["path"] for source in candidates),
        })

    plan = {
        "schema_version": 1,
        "mode": "taxonomy_remediation_plan",
        "source_manifest": manifest,
        "inventory_sha256": _sha256(inventory),
        "inventory_count": len(inventory),
        "actions": actions,
        "conflicts": conflicts,
    }
    return {**plan, "plan_sha256": _sha256(plan)}


def read_inventory(conn: Any, *, lock: bool = False) -> list[dict[str, Any]]:
    suffix = " FOR UPDATE" if lock else ""
    statement = "SELECT " + ", ".join(INVENTORY_COLUMNS)
    statement += " FROM crawled_documents ORDER BY id" + suffix
    return [dict(row) for row in conn.execute(text(statement)).mappings().all()]


def apply_plan(
    conn: Any,
    docs_dir: Path,
    plan: dict[str, Any],
    *,
    expected_plan_sha256: str,
    actor_id: str,
    reason: str,
) -> list[dict[str, str]]:
    """Validate and apply inside the caller's transaction; never commit independently."""
    if not reason or len(reason.strip()) < 3:
        raise ValueError("Apply requires a reason of at least three characters")
    try:
        actor_id = str(uuid.UUID(actor_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Apply requires a valid actor UUID") from exc
    payload = {key: value for key, value in plan.items() if key != "plan_sha256"}
    if (
        not expected_plan_sha256
        or plan.get("plan_sha256") != expected_plan_sha256
        or _sha256(payload) != expected_plan_sha256
    ):
        raise ValueError("Approved plan digest does not match plan contents")

    publication_lock(conn)
    actor = conn.execute(
        text("SELECT role, is_active, email_verified_at FROM accounts WHERE id = :id FOR SHARE"),
        {"id": actor_id},
    ).mappings().one_or_none()
    if (
        not actor or actor["role"] != "admin" or not actor["is_active"]
        or actor["email_verified_at"] is None
    ):
        raise ValueError("Apply requires an active verified administrator account")
    current = build_plan(docs_dir, read_inventory(conn, lock=True))
    if current["plan_sha256"] != expected_plan_sha256:
        raise ValueError("Plan is stale: database or source files changed; regenerate and review")
    if current["conflicts"]:
        raise ValueError("Plan contains source conflicts; resolve before applying")

    results = []
    for action in current["actions"]:
        updated = update_document_metadata(
            conn, action["document_id"], major=action["target_major"]
        )
        log_admin_action(
            conn=conn,
            actor_id=actor_id,
            action="crawler.document.taxonomy_remediation",
            target_type="crawled_document",
            target_id=action["document_id"],
            summary=f"Corrected document taxonomy: {reason.strip()}",
            details={
                "plan_sha256": expected_plan_sha256,
                "previous_major": action["current_major"],
                "target_major": action["target_major"],
                "result_document_id": updated["id"],
                "operation": action["action"],
            },
        )
        results.append({"document_id": action["document_id"], "result_document_id": updated["id"]})
    return results


def _explicit_engine(env_name: str) -> Any:
    raw_url = os.environ.get(env_name, "")
    if not raw_url:
        raise ValueError("The explicitly named database URL environment variable is empty")
    if make_url(raw_url).get_backend_name() != "postgresql":
        raise ValueError("Document remediation requires PostgreSQL")
    return create_engine(raw_url)


def _report_failure(exc: Exception, committed_result: dict[str, Any] | None) -> int:
    if committed_result is not None:
        # A receipt is outside the DB transaction. Never report its failure as rollback.
        print(
            "Database changes were committed (committed=true), but receipt output failed "
            f"({type(exc).__name__}). Do not rerun --apply without inspecting the DB. "
            "Committed result: " + json.dumps(committed_result, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2
    if isinstance(exc, ValueError):
        print(f"Document remediation rejected: {exc}", file=sys.stderr)
    else:
        # Never print an exception containing a connection URL/password or raw DB details.
        print(
            f"Document remediation failed ({type(exc).__name__}); no success is claimed.",
            file=sys.stderr,
        )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCUMENTS)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--inventory-json", type=Path, help="Offline JSON array of DB inventory rows")
    source.add_argument("--database-url-env", help="Explicit environment variable containing a DB URL")
    parser.add_argument("--output", type=Path, help="Write a new plan/result file; never overwrite an existing file")
    parser.add_argument("--apply", type=Path, metavar="PLAN_JSON", help="Explicitly apply a reviewed plan")
    parser.add_argument("--expected-plan-sha256")
    parser.add_argument("--actor-id")
    parser.add_argument("--reason")
    args = parser.parse_args(argv)
    if args.apply and (
        not args.database_url_env or not args.expected_plan_sha256 or not args.actor_id or not args.reason
    ):
        parser.error("--apply requires --database-url-env, --expected-plan-sha256, --actor-id and --reason")
    if not args.apply and any((args.expected_plan_sha256, args.actor_id, args.reason)):
        parser.error("Apply confirmation arguments require --apply")

    engine = None
    committed_result = None
    try:
        if args.output and args.output.resolve().is_relative_to(args.docs_dir.resolve()):
            raise ValueError("Plan output must be outside the source document directory")
        if args.output and args.output.exists():
            raise FileExistsError("Output already exists; choose a new evidence file")
        if args.apply:
            plan = json.loads(args.apply.read_text(encoding="utf-8"))
            engine = _explicit_engine(args.database_url_env)
            with engine.begin() as conn:
                results = apply_plan(
                    conn, args.docs_dir, plan,
                    expected_plan_sha256=args.expected_plan_sha256,
                    actor_id=args.actor_id, reason=args.reason,
                )
            result = {
                "mode": "applied", "committed": True,
                "plan_sha256": args.expected_plan_sha256, "results": results,
            }
            committed_result = result
        elif args.inventory_json:
            rows = json.loads(args.inventory_json.read_text(encoding="utf-8"))
            if not isinstance(rows, list):
                raise ValueError("Inventory JSON must be an array of document rows")
            result = build_plan(args.docs_dir, rows)
        else:
            engine = _explicit_engine(args.database_url_env)
            with engine.begin() as conn:
                conn.execute(text("SET TRANSACTION READ ONLY"))
                result = build_plan(args.docs_dir, read_inventory(conn))
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as output:
                output.write(rendered)
        else:
            print(rendered, end="")
        return 0
    except Exception as exc:
        return _report_failure(exc, committed_result)
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
