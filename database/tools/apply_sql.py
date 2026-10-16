"""Apply a versioned SQL file to the AI-07 HUS database.

Usage::

    python -m database.tools.apply_sql database/sql/00_ai07_schema.sql --dry-run
    python -m database.tools.apply_sql database/sql/00_ai07_schema.sql
    python -m database.tools.apply_sql database/sql/10_official_curricula_2023.sql

The SQL file is sent to PostgreSQL as one batch so that its own ``BEGIN`` /
``COMMIT`` block controls atomicity (the import script wraps everything in a
single transaction). Requires ``HUS_DATABASE_URL`` in the environment.

Safety: the tool refuses to run files that contain obviously destructive
statements (``DROP DATABASE``, ``DROP SCHEMA``, ``ALTER DATABASE``) unless
``--allow-dangerous`` is given. The project never drops the shared database.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import Engine

from database.hus_db.config import HusDatabaseConfigError
from database.hus_db.connection import connect

DANGEROUS_TOKENS: tuple[str, ...] = ("drop database", "drop schema", "alter database")


def scan_dangerous_statements(sql_text: str) -> list[str]:
    """Return the destructive tokens present in ``sql_text`` (case-insensitive)."""
    lowered = sql_text.lower()
    return [token for token in DANGEROUS_TOKENS if token in lowered]


def apply_sql(engine: Engine, sql_text: str) -> None:
    """Send ``sql_text`` to PostgreSQL as a single batch."""
    with engine.connect() as conn:
        driver = conn.connection.driver_connection
        cursor = driver.cursor()
        try:
            cursor.execute(sql_text)
            driver.commit()
        finally:
            cursor.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", type=Path, help="path to the SQL file to apply")
    parser.add_argument("--dry-run", action="store_true", help="validate and report without executing")
    parser.add_argument(
        "--allow-dangerous",
        action="store_true",
        help="permit DROP DATABASE / DROP SCHEMA / ALTER DATABASE statements",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.file.is_file():
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2
    sql_text = args.file.read_text(encoding="utf-8")
    dangerous = scan_dangerous_statements(sql_text)
    if dangerous and not args.allow_dangerous:
        print(
            "error: refusing to run; file contains destructive statements: "
            + ", ".join(dangerous)
            + " (pass --allow-dangerous to override)",
            file=sys.stderr,
        )
        return 3
    if args.dry_run:
        print(f"dry-run: {args.file} ({len(sql_text)} bytes) is readable")
        if dangerous:
            print(f"dry-run: destructive tokens present: {', '.join(dangerous)}")
        return 0
    try:
        engine = connect()
    except HusDatabaseConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"applying {args.file} ...")
    apply_sql(engine, sql_text)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
