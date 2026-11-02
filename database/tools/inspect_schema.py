"""Print or export a read-only snapshot of the AI-07 HUS schema.

Usage::

    python -m database.tools.inspect_schema                    # plain text
    python -m database.tools.inspect_schema --format markdown   # for SCHEMA.md
    python -m database.tools.inspect_schema --out database/SCHEMA.md

Requires ``HUS_DATABASE_URL`` in the environment.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from database.hus_db.config import HusDatabaseConfigError
from database.hus_db.connection import connect
from database.hus_db.introspect import (
    collect_schema,
    render_schema_markdown,
    render_schema_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--format", choices=("text", "markdown"), default="text")
    parser.add_argument("--out", type=Path, default=None, help="write to a file instead of stdout")
    parser.add_argument("--no-counts", action="store_true", help="skip row counts (faster)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        engine = connect()
    except HusDatabaseConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    snapshot = collect_schema(engine, with_row_counts=not args.no_counts)
    if args.format == "markdown":
        rendered = render_schema_markdown(snapshot)
    else:
        rendered = render_schema_text(snapshot)
    if args.out is not None:
        args.out.write_text(rendered + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
