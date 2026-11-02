"""Verify the AI-07 HUS database against the documented invariants.

Usage::

    python -m database.tools.verify_data
    python -m database.tools.verify_data --no-official   # base schema only

Exit code is 0 when every check passes and 1 otherwise, so it can gate CI or a
pre-demo smoke test. Requires ``HUS_DATABASE_URL`` in the environment.
"""

from __future__ import annotations

import argparse
import sys

from database.hus_db.config import HusDatabaseConfigError
from database.hus_db.connection import connect
from database.hus_db.verify import run_checks, summarize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--no-official",
        action="store_true",
        help="only require the 11 base tables + views, not the official import",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        engine = connect()
    except HusDatabaseConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    results = run_checks(engine, include_official=not args.no_official)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {result.name} - {result.detail}")
    passed, total = summarize(results)
    print(f"\n{passed}/{total} checks passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
