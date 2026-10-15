"""Crawl the allowlisted HUS pages into data/hus/index.json.

python -m tools.build_hus_index --dry-run   # show rules and seeds, no network
python -m tools.build_hus_index             # crawl, then write index.json + raw/ + failed.json
An empty data/hus/allowlist.json crawls nothing.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import httpx  # noqa: E402

from app.hus.crawler import Allowlist, crawl  # noqa: E402
from app.hus.index import HUSIndex  # noqa: E402


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

    headers = {"User-Agent": allowlist.user_agent}
    with httpx.Client(headers=headers, timeout=15, follow_redirects=False) as client:
        documents, failures = crawl(allowlist, client)
    index = HUSIndex(args.out / "index.json", args.out / "raw")
    counts = Counter(index.add(document, raw) for document, raw in documents)
    index.save()
    (args.out / "failed.json").write_text(
        json.dumps(failures, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8"
    )
    print(f"{len(documents)} trang: {dict(counts)}; {len(failures)} lỗi (xem failed.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())