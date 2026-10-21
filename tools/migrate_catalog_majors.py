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

from app.hus.cleaning import infer_major  # noqa: E402
from app.hus.models import MajorCategory  # noqa: E402


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


def migrate_catalog(catalog_path: Path, dry_run: bool = False) -> tuple[int, dict[str, int]]:
    """Load catalog, reclassify each document using infer_major, and update catalog."""
    if not catalog_path.is_file():
        raise FileNotFoundError(f"Catalog file not found: {catalog_path}")

    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    documents = data.get("documents", {})

    counts: Counter[str] = Counter()
    for doc in documents.values():
        title = doc.get("title", "")
        url = doc.get("source_url", "")
        content = doc.get("content_markdown", "")
        major = infer_major(title, url, content)
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
