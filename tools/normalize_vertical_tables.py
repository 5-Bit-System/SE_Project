"""Normalize vertically-rotated text in markdown tables and HUS document catalog.

Usage:
    python tools/normalize_vertical_tables.py
    python tools/normalize_vertical_tables.py --dry-run
    python tools/normalize_vertical_tables.py --check
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.hus.cleaning import _VERTICAL_REVERSED_TERMS, normalize_vertical_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Normalize vertically-rotated table header text in HUS documents",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT / "data" / "hus",
        help="Root path containing processed/documents and processed/catalog.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Display affected files without modifying files on disk",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with code 1 if any unnormalized vertical text is detected, 0 otherwise",
    )
    return parser


def normalize_document_text(content: str) -> tuple[str, int]:
    """Normalize vertically-rotated terms in document content.

    Returns:
        tuple (normalized_text, replaced_count)
    """
    new_content = normalize_vertical_text(content)
    if new_content == content:
        return content, 0

    count = 0
    for pattern, _ in _VERTICAL_REVERSED_TERMS:
        count += len(pattern.findall(content))
    return new_content, count


def normalize_all(
    root: Path, dry_run: bool = False
) -> tuple[int, int, list[str], int]:
    """Scan and normalize all markdown documents and catalog.json under root.

    Returns:
        tuple (normalized_files_count, total_replacements, list_of_file_paths, catalog_docs_updated)
    """
    doc_dir = root / "processed" / "documents"
    pattern = str(doc_dir / "**" / "*.md")
    md_files = sorted(glob.glob(pattern, recursive=True))

    repaired_files: list[str] = []
    total_replacements = 0

    for file_path_str in md_files:
        path = Path(file_path_str)
        content = path.read_text(encoding="utf-8")
        normalized_content, replaced_count = normalize_document_text(content)

        if replaced_count > 0:
            repaired_files.append(file_path_str)
            total_replacements += replaced_count
            if not dry_run:
                path.write_text(normalized_content, encoding="utf-8")

    # Synchronize catalog.json
    catalog_path = root / "processed" / "catalog.json"
    catalog_updated_count = 0
    if catalog_path.exists():
        try:
            catalog_data = json.loads(catalog_path.read_text(encoding="utf-8"))
            catalog_updated = False
            for doc_id, doc in catalog_data.get("documents", {}).items():
                content_md = doc.get("content_markdown", "")
                if content_md:
                    normalized_md, replaced_count = normalize_document_text(content_md)
                    if replaced_count > 0:
                        catalog_updated = True
                        catalog_updated_count += 1
                        total_replacements += replaced_count
                        if not dry_run:
                            doc["content_markdown"] = normalized_md
                            doc["content_hash"] = hashlib.sha256(
                                normalized_md.encode("utf-8")
                            ).hexdigest()

            if catalog_updated and not dry_run:
                tmp_path = catalog_path.with_suffix(".tmp")
                tmp_path.write_text(
                    json.dumps(catalog_data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                tmp_path.replace(catalog_path)
        except Exception as exc:
            print(f"Warning: could not update catalog.json: {exc}", file=sys.stderr)

    return len(repaired_files), total_replacements, repaired_files, catalog_updated_count


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    file_count, replacement_count, files, cat_count = normalize_all(
        args.root, dry_run=args.dry_run or args.check
    )

    if args.check:
        if file_count > 0 or cat_count > 0:
            print(
                f"[CHECK FAILED] Found {file_count} markdown file(s) and {cat_count} catalog entry(ies) "
                f"with {replacement_count} unnormalized vertical term(s):"
            )
            for f in files:
                print(f"  - {f}")
            return 1
        print("[CHECK PASSED] All markdown documents and catalog entries are clean.")
        return 0

    mode = "DRY-RUN: Would normalize" if args.dry_run else "Normalized"
    print(
        f"{mode} {file_count} markdown file(s) and {cat_count} catalog entry(ies) "
        f"({replacement_count} term replacements total)."
    )
    for f in files:
        print(f"  - {f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
