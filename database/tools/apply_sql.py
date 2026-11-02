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
import re
import sys
from pathlib import Path

from sqlalchemy import Engine, text

from database.hus_db.config import HusDatabaseConfigError
from database.hus_db.connection import connect

DANGEROUS_TOKENS: tuple[str, ...] = ("drop database", "drop schema", "alter database")


def scan_dangerous_statements(sql_text: str) -> list[str]:
    """Find destructive keyword pairs, ignoring SQL comments and quoted content.

    This is a guard against accidental execution, not a sandbox for untrusted SQL.
    """
    tokens: list[str] = []
    position = 0
    while position < len(sql_text):
        if sql_text.startswith("--", position):
            end = sql_text.find("\n", position + 2)
            position = len(sql_text) if end < 0 else end + 1
        elif sql_text.startswith("/*", position):
            depth = 1
            position += 2
            while position < len(sql_text) and depth:
                if sql_text.startswith("/*", position):
                    depth += 1
                    position += 2
                elif sql_text.startswith("*/", position):
                    depth -= 1
                    position += 2
                else:
                    position += 1
        elif sql_text[position] in ("'", '"'):
            quote = sql_text[position]
            position += 1
            while position < len(sql_text):
                if sql_text[position] == quote:
                    position += 1
                    if position < len(sql_text) and sql_text[position] == quote:
                        position += 1
                    else:
                        break
                else:
                    position += 1
            tokens.append("quoted")
        else:
            dollar = re.match(r"\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$", sql_text[position:])
            word = re.match(r"[A-Za-z_][A-Za-z_0-9]*", sql_text[position:])
            if dollar:
                delimiter = dollar.group()
                end = sql_text.find(delimiter, position + len(delimiter))
                position = len(sql_text) if end < 0 else end + len(delimiter)
                tokens.append("quoted")
            elif word:
                tokens.append(word.group().lower())
                position += len(word.group())
            else:
                if not sql_text[position].isspace():
                    tokens.append(sql_text[position])
                position += 1
    pairs = {f"{left} {right}" for left, right in zip(tokens, tokens[1:])}
    return [token for token in DANGEROUS_TOKENS if token in pairs]


def apply_sql(engine: Engine, sql_text: str) -> None:
    """Send ``sql_text`` to PostgreSQL as a single batch."""
    with engine.connect() as conn:
        if conn.execute(text("SELECT to_regclass('public.hus_catalog_revisions')")).scalar():
            raise RuntimeError("HUS runtime is managed by migrations; use migrate and publish_catalogs")
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
