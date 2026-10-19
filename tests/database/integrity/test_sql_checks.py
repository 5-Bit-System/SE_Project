"""Execute portable integrity queries on synthetic SQLite tables.

This tests detection logic only; PostgreSQL DDL and constraints still require
the opt-in hus_postgres integration suite.
"""

import pytest
from sqlalchemy import create_engine

from database.hus_db.verify import (
    check_curricula_have_courses,
    check_no_prerequisite_cycles,
    check_official_entries_covered,
)


@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    with engine.begin() as conn:
        conn.exec_driver_sql("ATTACH DATABASE ':memory:' AS public")
        conn.exec_driver_sql("CREATE TABLE public.curricula (curriculum_id INTEGER)")
        conn.exec_driver_sql(
            "CREATE TABLE public.curriculum_courses (curriculum_id INTEGER, course_code TEXT)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE public.official_curriculum_entries "
            "(curriculum_id INTEGER, course_code TEXT)"
        )
        conn.exec_driver_sql(
            "CREATE TABLE public.course_prerequisites "
            "(curriculum_id INTEGER, course_code TEXT, prerequisite_course_code TEXT)"
        )
    yield engine
    engine.dispose()


@pytest.mark.parametrize("edges,passed", [
    ([], True),
    ([(1, "A", "B"), (1, "B", "C")], True),
    ([(1, "A", "A")], False),
    ([(1, "A", "B"), (1, "B", "A")], False),
    ([(1, "A", "B"), (1, "B", "C"), (1, "C", "A")], False),
    ([(1, "A", "B"), (2, "B", "A")], True),
], ids=["empty", "chain", "self", "two-node-cycle", "three-node-cycle", "separate-majors"])
def test_cycle_detection_is_scoped_to_curriculum(engine, edges, passed):
    with engine.begin() as conn:
        for edge in edges:
            conn.exec_driver_sql("INSERT INTO public.course_prerequisites VALUES (?, ?, ?)", edge)
    assert check_no_prerequisite_cycles(engine).passed is passed


def test_empty_curriculum_is_detected_and_resolved(engine):
    with engine.begin() as conn:
        conn.exec_driver_sql("INSERT INTO public.curricula VALUES (1), (2)")
        conn.exec_driver_sql("INSERT INTO public.curriculum_courses VALUES (1, 'A')")
    assert not check_curricula_have_courses(engine).passed
    with engine.begin() as conn:
        conn.exec_driver_sql("INSERT INTO public.curriculum_courses VALUES (2, 'A')")
    assert check_curricula_have_courses(engine).passed


def test_official_entry_requires_membership_in_its_own_major(engine):
    with engine.begin() as conn:
        conn.exec_driver_sql("INSERT INTO public.curriculum_courses VALUES (1, 'A')")
        conn.exec_driver_sql("INSERT INTO public.official_curriculum_entries VALUES (2, 'A')")
    assert not check_official_entries_covered(engine).passed
    with engine.begin() as conn:
        conn.exec_driver_sql("INSERT INTO public.curriculum_courses VALUES (2, 'A')")
    assert check_official_entries_covered(engine).passed
