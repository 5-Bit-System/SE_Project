"""Read-only introspection of the AI-07 HUS database schema.

Everything here only reads metadata (tables, columns, keys, indexes, view
definitions, row counts). It never mutates the database, which makes it safe to
point at the shared Neon instance.

The metadata is fetched with a handful of bulk ``pg_catalog`` /
``information_schema`` queries rather than SQLAlchemy's per-table reflection.
That matters on a remote pooled endpoint such as Neon, where dozens of round
trips make introspection impractically slow.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

# The 11 base tables created by ``sql/00_ai07_schema.sql``.
CORE_TABLES: tuple[str, ...] = (
    "faculties",
    "majors",
    "curricula",
    "courses",
    "curriculum_courses",
    "course_prerequisites",
    "academic_terms",
    "accounts",
    "students",
    "course_attempts",
    "student_preferences",
)

# The 2 extra tables created by ``sql/10_official_curricula_2023.sql``.
OFFICIAL_TABLES: tuple[str, ...] = (
    "official_curriculum_groups",
    "official_curriculum_entries",
)

VIEW_NAMES: tuple[str, ...] = ("v_students_profile", "v_student_transcript")


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    type: str
    nullable: bool
    default: str | None


@dataclass(frozen=True)
class TableInfo:
    name: str
    columns: tuple[ColumnInfo, ...]
    primary_key: tuple[str, ...]
    unique: tuple[tuple[str, ...], ...]
    foreign_keys: tuple[str, ...]
    checks: tuple[str, ...]
    indexes: tuple[str, ...]


@dataclass
class SchemaSnapshot:
    """A point-in-time, read-only view of the schema and its row counts."""

    tables: list[TableInfo] = field(default_factory=list)
    views: dict[str, str] = field(default_factory=dict)
    row_counts: dict[str, int] = field(default_factory=dict)

    @property
    def table_names(self) -> set[str]:
        return {table.name for table in self.tables}


_COLUMNS_SQL = """
SELECT c.relname AS table_name,
       a.attname AS column_name,
       format_type(a.atttypid, a.atttypmod) AS column_type,
       NOT a.attnotnull AS nullable,
       pg_get_expr(d.adbin, d.adrelid) AS default_expr
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
WHERE n.nspname = :schema
  AND c.relkind IN ('r', 'p')
  AND a.attnum > 0
  AND NOT a.attisdropped
ORDER BY c.relname, a.attnum
"""

_KEY_CONSTRAINTS_SQL = """
SELECT c.relname AS table_name,
       con.conname AS constraint_name,
       con.contype AS constraint_type,
       array_agg(a.attname ORDER BY k.ord) AS columns
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
CROSS JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS k(attnum, ord)
JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.attnum
WHERE n.nspname = :schema AND con.contype IN ('p', 'u')
GROUP BY c.relname, con.conname, con.contype
ORDER BY c.relname, con.contype, con.conname
"""

_DEF_CONSTRAINTS_SQL = """
SELECT c.relname AS table_name,
       con.conname AS constraint_name,
       pg_get_constraintdef(con.oid) AS definition
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = :schema AND con.contype = :contype
ORDER BY c.relname, con.conname
"""

_INDEXES_SQL = """
SELECT c.relname AS table_name,
       i.relname AS index_name,
       array_agg(a.attname ORDER BY k.ord) AS columns
FROM pg_index ix
JOIN pg_class c ON c.oid = ix.indrelid
JOIN pg_class i ON i.oid = ix.indexrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
CROSS JOIN LATERAL unnest(ix.indkey) WITH ORDINALITY AS k(attnum, ord)
JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum
WHERE n.nspname = :schema AND c.relkind = 'r'
GROUP BY c.relname, i.relname
ORDER BY c.relname, i.relname
"""

_TABLES_SQL = """
SELECT c.relname AS table_name
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = :schema AND c.relkind IN ('r', 'p')
ORDER BY c.relname
"""

_VIEWS_SQL = """
SELECT table_name, view_definition
FROM information_schema.views
WHERE table_schema = :schema
ORDER BY table_name
"""


def _fetch(engine: Engine, sql: str, schema: str, **params: object) -> list[tuple]:
    with engine.connect() as conn:
        return list(conn.execute(text(sql), {"schema": schema, **params}).fetchall())


def read_row_counts(
    engine: Engine,
    names: tuple[str, ...],
    *,
    schema: str = "public",
) -> dict[str, int]:
    """Count rows per relation in a single round trip.

    Returns an empty mapping when no relation exists; never raises on a missing
    relation so a partial database can still be inspected.
    """
    existing = tuple(name for name in names if name)
    if not existing:
        return {}
    union = " UNION ALL ".join(
        f"SELECT '{name}' AS relation, count(*) AS n FROM {schema}.{name}" for name in existing
    )
    try:
        with engine.connect() as conn:
            rows = conn.exec_driver_sql(union).fetchall()
    except SQLAlchemyError:
        return {}
    return {row[0]: int(row[1]) for row in rows}


def collect_schema(
    engine: Engine,
    *,
    schema: str = "public",
    with_row_counts: bool = True,
) -> SchemaSnapshot:
    """Collect a full read-only snapshot of the AI-07 schema."""
    table_names = [row[0] for row in _fetch(engine, _TABLES_SQL, schema)]
    ordered = [name for name in (*CORE_TABLES, *OFFICIAL_TABLES) if name in table_names]
    ordered += [name for name in table_names if name not in ordered]

    columns: dict[str, list[ColumnInfo]] = {}
    for table_name, column_name, column_type, nullable, default in _fetch(
        engine, _COLUMNS_SQL, schema
    ):
        columns.setdefault(table_name, []).append(
            ColumnInfo(
                name=column_name,
                type=column_type,
                nullable=bool(nullable),
                default=default,
            )
        )

    primary_keys: dict[str, tuple[str, ...]] = {}
    unique: dict[str, list[tuple[str, ...]]] = {}
    for table_name, _name, constraint_type, cols in _fetch(engine, _KEY_CONSTRAINTS_SQL, schema):
        if constraint_type == "p":
            primary_keys[table_name] = tuple(cols)
        else:
            unique.setdefault(table_name, []).append(tuple(cols))

    foreign_keys: dict[str, list[str]] = {}
    for table_name, name, definition in _fetch(engine, _DEF_CONSTRAINTS_SQL, schema, contype="f"):
        foreign_keys.setdefault(table_name, []).append(definition)

    checks: dict[str, list[str]] = {}
    for table_name, name, definition in _fetch(engine, _DEF_CONSTRAINTS_SQL, schema, contype="c"):
        checks.setdefault(table_name, []).append(f"{name}: {definition}")

    indexes: dict[str, list[str]] = {}
    for table_name, index_name, cols in _fetch(engine, _INDEXES_SQL, schema):
        indexes.setdefault(table_name, []).append(f"{index_name}({', '.join(cols)})")

    tables = [
        TableInfo(
            name=name,
            columns=tuple(columns.get(name, [])),
            primary_key=primary_keys.get(name, ()),
            unique=tuple(unique.get(name, [])),
            foreign_keys=tuple(foreign_keys.get(name, [])),
            checks=tuple(checks.get(name, [])),
            indexes=tuple(indexes.get(name, [])),
        )
        for name in ordered
    ]

    views = {
        name: definition or ""
        for name, definition in _fetch(engine, _VIEWS_SQL, schema)
    }

    row_counts: dict[str, int] = {}
    if with_row_counts:
        row_counts = read_row_counts(engine, tuple(ordered) + tuple(views), schema=schema)
    return SchemaSnapshot(tables=tables, views=views, row_counts=row_counts)


def _column_line(column: ColumnInfo) -> str:
    flags = ["NULL" if column.nullable else "NOT NULL"]
    if column.default is not None:
        flags.append(f"default {column.default}")
    return f"{column.name} {column.type} ({', '.join(flags)})"


def render_schema_text(snapshot: SchemaSnapshot) -> str:
    """Render the snapshot as plain text, handy for a quick terminal review."""
    lines: list[str] = []
    for table in snapshot.tables:
        count = snapshot.row_counts.get(table.name)
        suffix = f" [{count} rows]" if count is not None else ""
        lines.append(f"{table.name}{suffix}")
        for column in table.columns:
            lines.append(f"  - {_column_line(column)}")
        if table.primary_key:
            lines.append(f"  PK: {', '.join(table.primary_key)}")
        for item in table.unique:
            lines.append(f"  UNIQUE: {', '.join(item)}")
        for fk in table.foreign_keys:
            lines.append(f"  FK: {fk}")
        if table.indexes:
            lines.append(f"  INDEX: {', '.join(table.indexes)}")
    for name in snapshot.views:
        count = snapshot.row_counts.get(name)
        suffix = f" [{count} rows]" if count is not None else ""
        lines.append(f"VIEW {name}{suffix}")
    return "\n".join(lines)


def render_schema_markdown(snapshot: SchemaSnapshot, *, title: str = "AI-07 schema snapshot") -> str:
    """Render the snapshot as Markdown for ``database/SCHEMA.md``."""
    lines: list[str] = [f"# {title}", ""]
    lines.append(
        "Read-only snapshot generated by `python -m database.tools.inspect_schema "
        "--format markdown`. Do not edit by hand."
    )
    lines.append("")
    for table in snapshot.tables:
        count = snapshot.row_counts.get(table.name)
        heading = f"## `{table.name}`"
        if count is not None:
            heading += f" — {count} rows"
        lines.append(heading)
        lines.append("")
        lines.append("| Column | Type | Nullable | Default |")
        lines.append("|---|---|---|---|")
        for column in table.columns:
            nullable = "yes" if column.nullable else "no"
            default = column.default or ""
            lines.append(f"| `{column.name}` | {column.type} | {nullable} | {default} |")
        lines.append("")
        if table.primary_key:
            lines.append(f"- **Primary key:** {', '.join(f'`{c}`' for c in table.primary_key)}")
        for item in table.unique:
            lines.append(f"- **Unique:** {', '.join(f'`{c}`' for c in item)}")
        for fk in table.foreign_keys:
            lines.append(f"- **Foreign key:** {fk}")
        if table.indexes:
            lines.append(f"- **Indexes:** {', '.join(table.indexes)}")
        if table.checks:
            lines.append("- **Checks:**")
            for check in table.checks:
                lines.append(f"  - {check}")
        lines.append("")
    if snapshot.views:
        lines.append("## Views")
        lines.append("")
        for name, definition in snapshot.views.items():
            count = snapshot.row_counts.get(name)
            header = f"### `{name}`"
            if count is not None:
                header += f" — {count} rows"
            lines.append(header)
            lines.append("")
            lines.append("```sql")
            lines.append(definition.strip())
            lines.append("```")
            lines.append("")
    return "\n".join(lines)
