"""Script to decode URL-encoded and mojibake characters in attachment document titles.

Usage:
    python tools/clean_attachment_titles.py
    python tools/clean_attachment_titles.py --dry-run
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.hus.cleaning import slugify  # noqa: E402
from app.hus.models import HUSDocument  # noqa: E402
from app.hus.pipeline import _clean_attachment_filename  # noqa: E402
from app.hus.storage import ProcessedStorage, _normalize_major  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Clean attachment document titles and markdown filenames in HUS storage",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT / "data" / "hus",
        help="Root path containing processed/catalog.json and processed/documents",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Calculate and display changes without writing to disk",
    )
    return parser


def clean_attachment_titles(root: Path, dry_run: bool = False) -> tuple[int, list[str]]:
    """Clean attachment titles in catalog and rename markdown files accordingly."""
    storage = ProcessedStorage(root)
    updated_count = 0
    updated_ids: list[str] = []

    for doc_id, raw_doc in list(storage.documents.items()):
        doc = HUSDocument.model_validate(raw_doc)
        if not (doc.title.startswith("Tài liệu đính kèm:") or "%" in doc.title):
            continue

        cleaned_filename = _clean_attachment_filename(doc.url)
        new_title = f"Tài liệu đính kèm: {cleaned_filename}"

        if new_title == doc.title:
            continue

        updated_count += 1
        updated_ids.append(doc_id)

        major_str = _normalize_major(doc.major)
        new_slug = slugify(new_title) or "document"
        expected_new_file = storage.doc_dir / major_str / f"{new_slug}--{doc_id[:8]}.md"

        old_files = list(storage.doc_dir.glob(f"*/*--{doc_id[:8]}.md"))

        if dry_run:
            print(f"[DRY-RUN] {doc_id[:8]}: {doc.title} -> {new_title}")
            for old_file in old_files:
                if old_file.resolve() != expected_new_file.resolve():
                    print(f"  Old file to delete: {old_file.name}")
            print(f"  New file: {expected_new_file.name}")
            continue

        # Update doc title and save to write new markdown file and update in-memory dict
        doc.title = new_title
        storage.save_document(doc)

        # Remove previous markdown file(s) with different names
        for old_file in old_files:
            if old_file.resolve() != expected_new_file.resolve() and old_file.exists():
                old_file.unlink()

    if not dry_run and updated_count > 0:
        storage.commit()

    return updated_count, updated_ids


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    count, ids = clean_attachment_titles(args.root, dry_run=args.dry_run)
    action = "Would update" if args.dry_run else "Successfully updated"
    print(f"\n{action} {count} attachment documents.")


if __name__ == "__main__":
    main()
