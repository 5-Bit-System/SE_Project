"""Read-only introspection of the AI-07 HUS database schema.

Everything here only reads metadata (tables, columns, keys, indexes, view
definitions, row counts). It never mutates the database, which makes it safe to
point at the shared Neon instance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import Engine, inspect
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


def _fk_repr(foreign_key: dict[str, Any]) -> str:
    local = ", ".join(foreign_key.get("constrained_columns") or [])
    referred_table = foreign_key.get("referred_table")
    referred = ", ".join(foreign_key.get("referred_columns") or [])
    return f"({local}) -> {referred_table}({referred})"


def _column_info(column: dict[str, Any]) -> ColumnInfo:
    return ColumnInfo(
        name=column["name"],
        type=str(column["type"]),
        nullable=bool(column.get("nullable", True)),
        default=column.get("default"),
    )


def read_table(engine: Engine, name: str, *, schema: str = "public") -> TableInfo:
    """Read a single table's structural metadata."""
    inspector = inspect(engine)
    columns = tuple(_column_info(c) for c in inspector.get_columns(name, schema=schema))
    pk = inspector.get_pk_constraint(name, schema=schema)
    unique = tuple(
        tuple(u["column_names"])
        for u in inspector.get_unique_constraints(name, schema=schema)
        if u.get("column_names")
    )
    foreign_keys = tuple(
        _fk_repr(fk) for fk in inspector.get_foreign_keys(name, schema=schema)
    )
    checks = tuple(
        f"{c.get('name', 'check')}: {c.get('sqltext', '')}"
        for c in inspector.get_check_constraints(name, schema=schema)
    )
    indexes = tuple(
        f"{i['name']}({', '.join(i.get('column_names') or [])})"
        for i in inspector.get_indexes(name, schema=schema)
    )
    return TableInfo(
        name=name,
        columns=columns,
        primary_key=tuple(pk.get("constrained_columns") or []),
        unique=unique,
        foreign_keys=foreign_keys,
        checks=checks,
        indexes=indexes,
    )


def read_row_counts(
    engine: Engine,
    names: tuple[str, ...],
    *,
    schema: str = "public",
) -> dict[str, int]:
    """Count rows per relation, skipping any relation that cannot be counted."""
    counts: dict[str, int] = {}
    with engine.connect() as conn:
        for name in names:
            try:
                value = conn.exec_driver_sql(
                    f"SELECT count(*) FROM {schema}.{name}"
                ).scalar()
            except SQLAlchemyError:
                continue
            counts[name] = int(value or 0)
    return counts


def collect_schema(
    engine: Engine,
    *,
    schema: str = "public",
    with_row_counts: bool = True,
) -> SchemaSnapshot:
    """Collect a full read-only snapshot of the AI-07 schema."""
    inspector = inspect(engine)
    available_tables = inspector.get_table_names(schema=schema)
    ordered = [name for name in (*CORE_TABLES, *OFFICIAL_TABLES) if name in available_tables]
    # Keep any unexpected table as well, so drift is visible in the report.
    ordered += [name for name in available_tables if name not in ordered]

    tables = [read_table(engine, name, schema=schema) for name in ordered]
    views = {
        name: inspector.get_view_definition(name, schema=schema) or ""
        for name in inspector.get_view_names(schema=schema)
    }
    row_counts: dict[str, int] = {}
    if with_row_counts:
        row_counts = read_row_counts(engine, tuple(ordered), schema=schema)
        row_counts.update(read_row_counts(engine, tuple(views), schema=schema))
    return SchemaSnapshot(tables=tables, views=views, row_counts=row_counts)


def _column_line(column: ColumnInfo) -> str:
    flags = []
    flags.append("NULL" if column.nullable else "NOT NULL")
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
        for unique in table.unique:
            lines.append(f"  UNIQUE: {', '.join(unique)}")
        for fk in table.foreign_keys:
            lines.append(f"  FK: {fk}")
        if table.indexes:
            lines.append(f"  INDEX: {', '.join(table.indexes)}")
    for name, definition in snapshot.views.items():
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
            lines.append(
                f"| `{column.name}` | {column.type} | {nullable} | {default} |"
            )
        lines.append("")
        if table.primary_key:
            lines.append(f"- **Primary key:** {', '.join(f'`{c}`' for c in table.primary_key)}")
        for unique in table.unique:
            lines.append(f"- **Unique:** {', '.join(f'`{c}`' for c in unique)}")
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
