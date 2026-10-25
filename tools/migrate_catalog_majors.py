"""Script to backfill/migrate the 'major' field for all documents in catalog.json.

Usage:
    python tools/migrate_catalog_majors.py
    python tools/migrate_catalog_majors.py --catalog data/hus/processed/catalog.json
    python tools/migrate_catalog_majors.py --dry-run
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.hus.cleaning import infer_attachment_major, infer_major  # noqa: E402
from app.hus.models import MajorCategory  # noqa: E402
from app.hus.urls import CrawlError, canonicalize_url  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Migrate/backfill 'major' classification in HUS catalog.json",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=REPO_ROOT / "data" / "hus" / "processed" / "catalog.json",
        help="Path to catalog.json to migrate",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate and display statistics without overwriting catalog.json",
    )
    return parser


def _url_identity(url: str) -> str:
    """Match parent references using the same identity as crawler storage."""
    try:
        return canonicalize_url(url)
    except CrawlError:
        return url


def migrate_catalog(catalog_path: Path, dry_run: bool = False) -> tuple[int, dict[str, int]]:
    """Reclassify documents, then apply the crawler's attachment inheritance rule."""
    if not catalog_path.is_file():
        raise FileNotFoundError(f"Catalog file not found: {catalog_path}")

    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    documents = data.get("documents", {})

    # Infer all parents before resolving attachments, regardless of catalog order.
    inferred: dict[str, MajorCategory] = {}
    for doc_id, doc in documents.items():
        title = doc.get("title", "")
        url = doc.get("source_url", "")
        content = doc.get("content_markdown", "")
        inferred[doc_id] = (
            infer_attachment_major(url, content)
            if doc.get("parent_url") else infer_major(title, url, content)
        )
    majors_by_url = {
        _url_identity(doc["source_url"]): inferred[doc_id]
        for doc_id, doc in documents.items() if doc.get("source_url")
    }

    counts: Counter[str] = Counter()
    for doc_id, doc in documents.items():
        major = inferred[doc_id]
        if parent_url := doc.get("parent_url"):
            parent_major = majors_by_url.get(_url_identity(parent_url))
            if parent_major is None:
                # A partial catalog cannot reconstruct the inherited label.
                # Retain a valid existing label rather than silently losing it.
                try:
                    parent_major = MajorCategory(doc.get("major"))
                    if parent_major == MajorCategory.GENERAL:
                        parent_major = MajorCategory.UNKNOWN
                except ValueError:
                    parent_major = MajorCategory.UNKNOWN
            major = infer_attachment_major(
                doc.get("source_url", ""), doc.get("content_markdown", ""),
                parent_major=parent_major,
            )
        doc["major"] = major.value
        counts[major.value] += 1

    if not dry_run:
        temp_path = catalog_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(catalog_path)

    return len(documents), dict(counts)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        total, stats = migrate_catalog(args.catalog, dry_run=args.dry_run)
    except Exception as exc:
        print(f"[ERROR] Migration failed: {exc}", file=sys.stderr)
        return 1

    mode_label = "[DRY-RUN] " if args.dry_run else ""
    print(f"\n{mode_label}HUS Catalog Major Migration Summary:")
    print("=" * 45)
    print(f"Total documents processed: {total}")
    print("-" * 45)
    for cat in MajorCategory:
        count = stats.get(cat.value, 0)
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {cat.value:<25} : {count:>3} ({pct:>5.1f}%)")
    print("=" * 45)

    if not args.dry_run:
        print(f"[SUCCESS] Updated {args.catalog}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
