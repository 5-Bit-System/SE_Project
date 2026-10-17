"""Create or rigorously adopt the original 13-table HUS source schema.

Revision ID: hus_20261017_01
"""

from __future__ import annotations

import re
from pathlib import Path

from alembic import op
from sqlalchemy import text

from database.hus_db.introspect import CORE_TABLES, OFFICIAL_TABLES, VIEW_NAMES

revision = "hus_20261017_01"
down_revision = None
branch_labels = None
depends_on = None

ROOT = Path(__file__).resolve().parents[2]
OBJECTS = (*CORE_TABLES, *OFFICIAL_TABLES)


def _official_ddl() -> str:
    sql = (ROOT / "sql" / "10_official_curricula_2023.sql").read_text(encoding="utf-8")
    beginning = sql.index("CREATE TABLE IF NOT EXISTS public.official_curriculum_groups")
    end = sql.index("-- Remove only synthetic records", beginning)
    return sql[beginning:end].replace("public.", "")


def _signature(conn, schema: str) -> dict:
    """Compare actual PostgreSQL definitions, including defaults, identity, checks and views."""
    rows = conn.execute(text("""
        SELECT c.relname, c.relkind, a.attnum, a.attname,
               format_type(a.atttypid,a.atttypmod), a.attnotnull, a.attidentity,
               pg_get_expr(d.adbin,d.adrelid)
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        LEFT JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped
        LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum
        WHERE n.nspname=:schema AND c.relname=ANY(:names)
        ORDER BY c.relname,a.attnum
    """), {"schema": schema, "names": list((*OBJECTS, *VIEW_NAMES))}).all()
    constraints = conn.execute(text("""
        SELECT c.relname, con.contype, pg_get_constraintdef(con.oid)
        FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid
        JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname=:schema AND c.relname=ANY(:names)
        ORDER BY c.relname,con.contype,pg_get_constraintdef(con.oid)
    """), {"schema": schema, "names": list(OBJECTS)}).all()
    views = conn.execute(text("""
        SELECT c.relname, pg_get_viewdef(c.oid,true)
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname=:schema AND c.relname=ANY(:names) AND c.relkind='v'
    """), {"schema": schema, "names": list(VIEW_NAMES)}).all()
    def norm(value):
        if value is None:
            return None
        value = re.sub(rf'(?i)(?:"?{re.escape(schema)}"?\.)', '', str(value))
        return re.sub(r'\s+', ' ', value).strip()
    return {
        "columns": [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], norm(r[7])) for r in rows],
        "constraints": sorted((r[0], r[1], norm(r[2])) for r in constraints),
        "views": sorted((r[0], norm(r[1])) for r in views),
    }


def upgrade() -> None:
    conn = op.get_bind()
    existing = conn.execute(text("""
        SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname=current_schema() AND relname=ANY(:names)
          AND c.relkind IN ('r','p','v')
    """), {"names": list((*OBJECTS, *VIEW_NAMES))}).scalars().all()
    if not existing:
        conn.exec_driver_sql((ROOT / "sql" / "00_ai07_schema.sql").read_text(encoding="utf-8"))
        conn.exec_driver_sql(_official_ddl())
        return
    if set(existing) != set((*OBJECTS, *VIEW_NAMES)):
        raise RuntimeError(f"Partial HUS baseline; refusing adoption. Objects present: {sorted(existing)}")
    # Build the canonical baseline in a temporary transaction-scoped schema. Every
    # source object is compared before Alembic marks the existing baseline applied.
    scratch = "_hus_baseline_check"
    conn.exec_driver_sql(f'CREATE SCHEMA "{scratch}"')
    try:
        conn.exec_driver_sql(f'SET LOCAL search_path TO "{scratch}"')
        conn.exec_driver_sql((ROOT / "sql" / "00_ai07_schema.sql").read_text(encoding="utf-8"))
        conn.exec_driver_sql(_official_ddl())
        expected = _signature(conn, scratch)
        conn.exec_driver_sql("SET LOCAL search_path TO public")
        actual = _signature(conn, "public")
        if actual != expected:
            for key in expected:
                if actual[key] != expected[key]:
                    raise RuntimeError(f"HUS baseline {key} differ; refusing adoption")
    finally:
        conn.exec_driver_sql("SET LOCAL search_path TO public")
        conn.exec_driver_sql(f'DROP SCHEMA "{scratch}" CASCADE')


def downgrade() -> None:
    raise RuntimeError("HUS source schema downgrade is intentionally unsupported")
