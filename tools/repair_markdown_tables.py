"""Script to repair broken markdown tables caused by embedded newlines in table cells.

Usage:
    python tools/repair_markdown_tables.py
    python tools/repair_markdown_tables.py --dry-run
    python tools/repair_markdown_tables.py --check
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
from pathlib import Path
import re
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.hus.cleaning import normalize_vertical_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Repair broken markdown tables with embedded cell newlines in HUS documents",
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
        help="Display broken files and rows without modifying files on disk",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with code 1 if any broken markdown tables are detected, 0 otherwise",
    )
    parser.add_argument(
        "--normalize-vertical",
        action="store_true",
        help="Also normalize vertically-rotated table headers (e.g. ỉhc nít ốS -> Số tín chỉ)",
    )
    return parser


def repair_markdown_text(
    content: str, normalize_vertical: bool = False
) -> tuple[str, int]:
    """Repair broken table rows in markdown content where cells contained newlines.

    Detects rows starting with '|' but not ending with '|', collecting subsequent lines
    until the line ending with '|', and joins them with '<br>', cleaning pipe boundaries.
    If normalize_vertical is True, also normalizes reversed vertical table header terms.

    Returns:
        tuple (repaired_text, broken_rows_count)
    """
    lines = content.splitlines()
    repaired_lines: list[str] = []
    broken_rows = 0
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("|"):
            if not stripped.endswith("|"):
                block = [stripped]
                i += 1
                while i < n:
                    cur_stripped = lines[i].strip()
                    block.append(cur_stripped)
                    if cur_stripped.endswith("|"):
                        break
                    i += 1
                broken_rows += 1
                line = "<br>".join(block)

            # Clean <br>| and |<br> to avoid malformed cell dividers
            line = re.sub(r"\s*<br\s*/?>\s*\|\s*", " | ", line)
            line = re.sub(r"\s*\|\s*<br\s*/?>\s*", " | ", line)
            # Collapse multiple consecutive <br>
            line = re.sub(r"(?:<br>)+", "<br>", line)
            if normalize_vertical:
                normalized_line = normalize_vertical_text(line)
                if normalized_line != line:
                    broken_rows += 1
                    line = normalized_line
            repaired_lines.append(line.strip())
        else:
            if normalize_vertical:
                line = normalize_vertical_text(line)
            repaired_lines.append(line)
        i += 1

    result = "\n".join(repaired_lines)
    if content.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result, broken_rows


def repair_all(
    root: Path, dry_run: bool = False, normalize_vertical: bool = False
) -> tuple[int, int, list[str]]:
    """Scan and repair all markdown documents under root/processed/documents.

    Returns:
        tuple (repaired_files_count, total_broken_rows, list_of_repaired_file_paths)
    """
    doc_dir = root / "processed" / "documents"
    pattern = str(doc_dir / "**" / "*.md")
    md_files = sorted(glob.glob(pattern, recursive=True))

    repaired_files: list[str] = []
    total_broken_rows = 0

    for file_path_str in md_files:
        path = Path(file_path_str)
        content = path.read_text(encoding="utf-8")
        repaired_content, broken_count = repair_markdown_text(
            content, normalize_vertical=normalize_vertical
        )

        if broken_count > 0:
            repaired_files.append(file_path_str)
            total_broken_rows += broken_count
            if not dry_run:
                path.write_text(repaired_content, encoding="utf-8")

    # Also synchronize catalog.json if it exists
    catalog_path = root / "processed" / "catalog.json"
    if catalog_path.exists():
        try:
            catalog_data = json.loads(catalog_path.read_text(encoding="utf-8"))
            catalog_updated = False
            for doc_id, doc in catalog_data.get("documents", {}).items():
                content_md = doc.get("content_markdown", "")
                if content_md:
                    repaired_md, broken_count = repair_markdown_text(
                        content_md, normalize_vertical=normalize_vertical
                    )
                    if broken_count > 0:
                        catalog_updated = True
                        if not dry_run:
                            doc["content_markdown"] = repaired_md
                            doc["content_hash"] = hashlib.sha256(
                                repaired_md.encode("utf-8")
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

    return len(repaired_files), total_broken_rows, repaired_files


def verify_no_broken_tables(root: Path) -> int:
    """Verify that 0 markdown files contain broken table rows.

    Returns:
        int: number of files with broken tables
    """
    doc_dir = root / "processed" / "documents"
    pattern = str(doc_dir / "**" / "*.md")
    md_files = sorted(glob.glob(pattern, recursive=True))

    broken_files = 0
    for file_path_str in md_files:
        path = Path(file_path_str)
        content = path.read_text(encoding="utf-8")
        for line in content.splitlines():
            s = line.strip()
            if s.startswith("|") and not s.endswith("|"):
                broken_files += 1
                break
    return broken_files


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.check:
        broken_files = verify_no_broken_tables(args.root)
        if broken_files > 0:
            print(f"Check FAILED: {broken_files} files contain broken markdown tables.")
            return 1
        print("Check PASSED: 0 files contain broken markdown tables.")
        return 0

    repaired_count, broken_rows, repaired_files = repair_all(
        args.root,
        dry_run=args.dry_run,
        normalize_vertical=args.normalize_vertical,
    )

    action = "Detected (dry-run)" if args.dry_run else "Repaired"
    print(f"{action} {repaired_count} files ({broken_rows} broken table rows).")
    for f in repaired_files[:10]:
        print(f"  - {f}")
    if len(repaired_files) > 10:
        print(f"  ... and {len(repaired_files) - 10} more files.")

    if not args.dry_run:
        remaining_broken = verify_no_broken_tables(args.root)
        print(f"Post-repair verification: {remaining_broken} files with broken tables.")
        if remaining_broken > 0:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
