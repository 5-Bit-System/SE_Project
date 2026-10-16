"""Deterministic integrity checks for the AI-07 HUS database.

Two layers live here:

* pure predicates that operate on a :class:`SchemaSnapshot` or a count mapping,
  so they can be unit-tested without any database connection;
* SQL checks that read the live database through a SQLAlchemy ``Engine`` to catch
  the invariants the schema *cannot* enforce itself (for example, prerequisite
  cycles and official-import coverage — see DESIGN.md section 11.3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from sqlalchemy import Engine

from database.hus_db.introspect import (
    CORE_TABLES,
    OFFICIAL_TABLES,
    VIEW_NAMES,
    SchemaSnapshot,
    collect_schema,
)


@dataclass(frozen=True)
class CheckResult:
    """Outcome of a single verification check."""

    name: str
    passed: bool
    detail: str


# Minimum row counts expected after applying ``00_ai07_schema.sql`` and
# ``10_official_curricula_2023.sql``. Numbers are deliberately conservative so
# the check flags an empty or truncated import without pinning exact values.
DEFAULT_MIN_ROWS: dict[str, int] = {
    "faculties": 1,
    "majors": 4,
    "curricula": 4,
    "courses": 100,
    "curriculum_courses": 100,
    "course_prerequisites": 1,
    "official_curriculum_groups": 1,
    "official_curriculum_entries": 100,
}

# The database does not check prerequisite cycles, so we do it here.
PREREQUISITE_CYCLE_SQL = """
WITH RECURSIVE reach AS (
    SELECT curriculum_id, course_code, prerequisite_course_code AS reachable
    FROM public.course_prerequisites
  UNION
    SELECT r.curriculum_id, r.course_code, p.prerequisite_course_code
    FROM reach r
    JOIN public.course_prerequisites p
      ON p.curriculum_id = r.curriculum_id
     AND p.course_code = r.reachable
)
SELECT count(*) FROM reach WHERE course_code = reachable
"""

CURRICULA_WITHOUT_COURSES_SQL = """
SELECT count(*)
FROM public.curricula cu
WHERE NOT EXISTS (
    SELECT 1 FROM public.curriculum_courses cc
    WHERE cc.curriculum_id = cu.curriculum_id
)
"""

# Every official curriculum entry must also appear in curriculum_courses; the FK
# only guarantees that the course exists, not that it belongs to this curriculum.
OFFICIAL_ENTRIES_NOT_IN_CURRICULUM_SQL = """
SELECT count(*)
FROM public.official_curriculum_entries e
WHERE NOT EXISTS (
    SELECT 1 FROM public.curriculum_courses cc
    WHERE cc.curriculum_id = e.curriculum_id
      AND cc.course_code = e.course_code
)
"""


def check_required_objects(
    snapshot: SchemaSnapshot,
    *,
    include_official: bool = True,
) -> list[CheckResult]:
    """Verify the expected tables and views exist in the snapshot."""
    present_tables = snapshot.table_names
    present_views = set(snapshot.views)
    required_tables = list(CORE_TABLES)
    if include_official:
        required_tables += list(OFFICIAL_TABLES)
    results: list[CheckResult] = []
    for name in required_tables:
        ok = name in present_tables
        results.append(CheckResult(f"table:{name}", ok, "present" if ok else "MISSING"))
    for name in VIEW_NAMES:
        ok = name in present_views
        results.append(CheckResult(f"view:{name}", ok, "present" if ok else "MISSING"))
    return results


def check_min_rows(
    counts: Mapping[str, int],
    minimums: Mapping[str, int] | None = None,
) -> list[CheckResult]:
    """Verify each relation has at least the expected number of rows."""
    expected = DEFAULT_MIN_ROWS if minimums is None else minimums
    results: list[CheckResult] = []
    for name, minimum in expected.items():
        actual = counts.get(name)
        ok = actual is not None and actual >= minimum
        results.append(CheckResult(f"rows:{name}", ok, f"{actual} (min {minimum})"))
    return results


def _scalar(engine: Engine, sql: str) -> int:
    with engine.connect() as conn:
        return int(conn.exec_driver_sql(sql).scalar() or 0)


def check_no_prerequisite_cycles(engine: Engine) -> CheckResult:
    """Fail when a curriculum's prerequisite graph contains a cycle."""
    count = _scalar(engine, PREREQUISITE_CYCLE_SQL)
    return CheckResult(
        "sql:prerequisite_cycles",
        count == 0,
        f"{count} cyclic course(s)",
    )


def check_curricula_have_courses(engine: Engine) -> CheckResult:
    """Fail when a curriculum has no courses at all."""
    count = _scalar(engine, CURRICULA_WITHOUT_COURSES_SQL)
    return CheckResult(
        "sql:curricula_without_courses",
        count == 0,
        f"{count} curriculum(s) without courses",
    )


def check_official_entries_covered(engine: Engine) -> CheckResult:
    """Fail when an official entry's course is missing from curriculum_courses."""
    count = _scalar(engine, OFFICIAL_ENTRIES_NOT_IN_CURRICULUM_SQL)
    return CheckResult(
        "sql:official_entries_not_in_curriculum",
        count == 0,
        f"{count} official entry(ies) missing from curriculum_courses",
    )


def run_checks(
    engine: Engine,
    *,
    include_official: bool = True,
    snapshot: SchemaSnapshot | None = None,
) -> list[CheckResult]:
    """Run every structural, row-count and SQL check and return the results."""
    snap = snapshot or collect_schema(engine)
    results = check_required_objects(snap, include_official=include_official)
    results += check_min_rows(snap.row_counts)
    results.append(check_no_prerequisite_cycles(engine))
    results.append(check_curricula_have_courses(engine))
    if include_official and OFFICIAL_TABLES[-1] in snap.table_names:
        results.append(check_official_entries_covered(engine))
    return results


def summarize(results: list[CheckResult]) -> tuple[int, int]:
    """Return ``(passed, total)`` for a list of results."""
    passed = sum(1 for r in results if r.passed)
    return passed, len(results)
