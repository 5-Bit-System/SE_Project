"""CLI Runner for HUS Crawler & Data Cleaning Pipeline.

Usage:
    python tools/run_hus_crawler.py --dry-run
    python tools/run_hus_crawler.py --config data/hus/config/sources.json --max-pages 50
    python tools/run_hus_crawler.py --no-incremental
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.hus.allowlist import Allowlist  # noqa: E402
from app.hus.pipeline import HUSPipeline  # noqa: E402
from app.hus.state import CrawlStateManager  # noqa: E402
from app.hus.storage import ProcessedStorage, RawStorage  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="HUS Crawler & Cleaning Pipeline Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "data" / "hus" / "config" / "sources.json",
        help="Path to sources configuration JSON",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "data" / "hus",
        help="Root output directory for raw, processed, and state data",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and show scope rules without sending HTTP requests",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of HTML pages to process (overrides config if set)",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum link traversal depth (overrides config if set)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help="Delay in seconds between requests (overrides config if set)",
    )
    parser.add_argument(
        "--incremental",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable incremental change detection via ETag and content hash",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path = args.config.resolve()
    if not config_path.exists():
        sys.stderr.write(f"Error: Configuration file not found at {config_path}\n")
        return 1

    try:
        allowlist = Allowlist.load(config_path)
    except Exception as exc:
        sys.stderr.write(f"Error loading configuration: {exc}\n")
        return 1

    if args.dry_run:
        print("=" * 60)
        print("=== HUS CRAWLER DRY-RUN MODE ===")
        print("=" * 60)
        print(f"Config path      : {config_path}")
        print(f"Output directory : {args.out.resolve()}")
        print(f"User Agent       : {allowlist.user_agent}")
        print(f"Max Pages        : {args.max_pages or allowlist.max_pages}")
        print(f"Max Depth        : {args.max_depth or allowlist.max_depth}")
        print(f"Delay (seconds)  : {args.delay if args.delay is not None else allowlist.delay_seconds}")
        print(f"Incremental Mode : {args.incremental}")
        print("\n[Approved Host Rules & Path Prefixes]")
        for host, prefixes in allowlist.rules.items():
            print(f"  * {host}: {', '.join(prefixes)}")

        print("\n[Excluded Hosts (Other Faculties Blocked)]")
        for exc_host in sorted(allowlist.excluded_hosts):
            print(f"  [X] {exc_host}")

        print("\n[Seed URLs]")
        for seed in allowlist.seeds:
            print(f"  -> {seed}")
        print("=" * 60)
        print("Configuration valid. No network requests sent.")
        return 0

    out_root = args.out.resolve()
    raw_storage = RawStorage(out_root)
    processed_storage = ProcessedStorage(out_root)
    state_manager = CrawlStateManager(out_root / "state" / "crawl_state.json")

    pipeline = HUSPipeline(
        allowlist=allowlist,
        raw_storage=raw_storage,
        processed_storage=processed_storage,
        state_manager=state_manager,
    )

    print(f"Starting crawl with config: {config_path.name} (out: {out_root})...")
    summary = pipeline.run(
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        delay_seconds=args.delay,
        incremental=args.incremental,
    )

    print("\n" + "=" * 50)
    print("=== CRAWL SUMMARY ===")
    print("=" * 50)
    print(f"New documents        : {summary.new_count}")
    print(f"Updated documents    : {summary.updated_count}")
    print(f"Unchanged documents  : {summary.unchanged_count}")
    print(f"Attachments processed: {summary.attachment_count}")
    print(f"Attachments skipped  : {summary.skipped_attachment_count}")
    print(f"Errors encountered   : {summary.error_count}")

    if summary.skipped_attachments:
        print("\n[Skipped Attachments Detail]")
        for skipped_url, reason in summary.skipped_attachments.items():
            print(f"  - {skipped_url} -> {reason}")

    if summary.failures:
        print("\n[Failures Detail]")
        for fail_url, reason in summary.failures.items():
            print(f"  ! {fail_url} -> {reason}")
    print("=" * 50)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
