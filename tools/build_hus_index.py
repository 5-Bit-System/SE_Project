"""Inspect the legacy allowlist; unreviewed legacy index export is disabled.

python -m tools.build_hus_index --dry-run   # show rules and seeds, no network
Use python -m tools.prepare_hus_corpus build for reviewed candidate corpus export.
An empty data/hus/allowlist.json crawls nothing.
"""

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.hus.crawler import Allowlist  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--allowlist", type=Path, default=REPO_ROOT / "data/hus/allowlist.json")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "data/hus")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    allowlist = Allowlist.load(args.allowlist)
    if not allowlist.sources:
        print("Allowlist trống: không có gì để crawl.")
        return 0
    if args.dry_run:
        for host, prefixes in allowlist.rules.items():
            print(f"{host}: {', '.join(prefixes)}")
        print(f"{len(allowlist.seeds)} seed, max_pages={allowlist.max_pages}, "
              f"max_depth={allowlist.max_depth}, delay={allowlist.delay_seconds}s")
        return 0

    print("Legacy index export is disabled: use python -m tools.prepare_hus_corpus build "
          "with a pinned source manifest and explicit review decisions.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
