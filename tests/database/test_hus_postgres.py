"""Opt-in checks against local Docker ai07; synthetic rows always roll back."""

from __future__ import annotations

import json
import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database.hus_db.config import HusDatabaseConfig
from database.hus_db.connection import create_engine_for
from database.hus_db.introspect import CORE_TABLES, OFFICIAL_TABLES, VIEW_NAMES
from database.hus_db.verify import DEFAULT_MIN_ROWS, run_checks
from database.tools.publish_catalogs import SOURCE

pytestmark = pytest.mark.hus_postgres


@pytest.fixture(scope="module")
def hus_engine():
    url = os.environ.get("HUS_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set HUS_TEST_DATABASE_URL explicitly to test local Docker ai07")
    engine = create_engine_for(HusDatabaseConfig(url))
    if engine.url.host not in {"127.0.0.1", "localhost"} or engine.url.database != "ai07":
        engine.dispose()
        pytest.fail("HUS integration tests require a local ai07 database")
    yield engine
    engine.dispose()


@pytest.fixture
def hus_student(hus_engine):
    with hus_engine.connect() as conn:
        transaction = conn.begin()
        try:
            curriculum_id, course_code = conn.execute(text(
                "SELECT curriculum_id, course_code FROM public.curriculum_courses "
                "ORDER BY curriculum_id, course_code LIMIT 1"
            )).one()
            student_code = f"test_{uuid4().hex}"
            conn.execute(text(
                "INSERT INTO public.accounts(username, password_hash) VALUES (:code, 'test-only')"
            ), {"code": student_code})
            conn.execute(text(
                "INSERT INTO public.students(student_code, full_name, curriculum_id, admitted_year) "
                "VALUES (:code, 'Synthetic integration test', :curriculum, 2022)"
            ), {"code": student_code, "curriculum": curriculum_id})
            term_id = conn.execute(text(
                "INSERT INTO public.academic_terms(academic_year_start, semester) "
                "VALUES (2099, 3) ON CONFLICT (academic_year_start, semester) "
                "DO UPDATE SET semester = EXCLUDED.semester RETURNING term_id"
            )).scalar_one()
            yield conn, {"student": student_code, "course": course_code, "term": term_id}
        finally:
            transaction.rollback()


INSERT_ATTEMPT = text(
    "INSERT INTO public.course_attempts(student_code, course_code, term_id, attempt_no, "
    "grade_10, grade_4, result_status) "
    "VALUES (:student, :course, :term, :attempt, :grade_10, :grade_4, :status)"
)


def test_live_schema_and_import_pass_all_checks(hus_engine):
    results = run_checks(hus_engine)
    expected_names = {
        *(f"table:{name}" for name in (*CORE_TABLES, *OFFICIAL_TABLES)),
        *(f"view:{name}" for name in VIEW_NAMES),
        *(f"rows:{name}" for name in DEFAULT_MIN_ROWS),
        "sql:prerequisite_cycles",
        "sql:curricula_without_courses",
        "sql:official_entries_not_in_curriculum",
    }
    assert {result.name for result in results} == expected_names
    assert all(r.passed for r in results), [(r.name, r.detail) for r in results if not r.passed]


def test_live_prerequisites_exactly_match_source_export(hus_engine):
    tables = json.loads(SOURCE.read_text(encoding="utf-8"))["tables"]
    majors = {c["curriculum_id"]: c["major_code"] for c in tables["curricula"]}
    expected = {
        (majors[r["curriculum_id"]], r["course_code"], r["group_no"],
         r["prerequisite_course_code"])
        for r in tables["course_prerequisites"]
    }
    with hus_engine.connect() as conn:
        actual = set(conn.execute(text(
            "SELECT c.major_code, p.course_code, p.group_no, p.prerequisite_course_code "
            "FROM public.course_prerequisites p "
            "JOIN public.curricula c USING (curriculum_id)"
        )).all())
    assert actual == expected, {"missing": expected - actual, "extra": actual - expected}


def test_live_raw_prerequisite_cells_and_statuses_are_not_lost(hus_engine):
    tables = json.loads(SOURCE.read_text(encoding="utf-8"))["tables"]
    majors = {c["curriculum_id"]: c["major_code"] for c in tables["curricula"]}
    expected = sorted(
        (majors[e["curriculum_id"]], e["course_code"], e["group_key"],
         e["prerequisite_source_text"], e["prerequisite_parse_status"])
        for e in tables["official_curriculum_entries"]
    )
    with hus_engine.connect() as conn:
        actual = sorted(tuple(row) for row in conn.execute(text(
            "SELECT c.major_code, e.course_code, e.group_key, "
            "e.prerequisite_source_text, e.prerequisite_parse_status "
            "FROM public.official_curriculum_entries e "
            "JOIN public.curricula c USING (curriculum_id)"
        )).all())
    assert actual == expected


def test_profile_and_transcript_views_preserve_retakes(hus_student):
    conn, student = hus_student
    conn.execute(INSERT_ATTEMPT, [
        {**student, "attempt": 1, "grade_10": 3, "grade_4": 0, "status": "failed"},
        {**student, "attempt": 2, "grade_10": 8, "grade_4": 3, "status": "passed"},
    ])
    profile = conn.execute(text(
        "SELECT * FROM public.v_students_profile WHERE student_code = :student"
    ), student).mappings().one()
    assert profile["full_name"] == "Synthetic integration test"
    assert profile["major_code"]
    transcript = conn.execute(text(
        "SELECT * FROM public.v_student_transcript WHERE student_code = :student "
        "ORDER BY attempt_no"
    ), student).mappings().all()
    assert [row["result_status"] for row in transcript] == ["failed", "passed"]
    assert [float(row["grade_10"]) for row in transcript] == [3, 8]
    assert all(row["course_code"] == student["course"] for row in transcript)


@pytest.mark.parametrize(("override", "sqlstate"), [
    ({"grade_10": 11}, "23514"),
    ({"grade_4": 5}, "23514"),
    ({"attempt": 0}, "23514"),
    ({"status": "invalid"}, "23514"),
    ({"grade_10": None}, "23514"),
    ({"course": "NONEXISTENT_SYNTHETIC_COURSE"}, "23503"),
    ({"student": "NONEXISTENT_SYNTHETIC_STUDENT"}, "23503"),
])
def test_attempt_constraints_reject_invalid_data(hus_student, override, sqlstate):
    conn, student = hus_student
    values = {**student, "attempt": 1, "grade_10": 8, "grade_4": 3, "status": "passed"}
    with pytest.raises(IntegrityError) as error:
        with conn.begin_nested():
            conn.execute(INSERT_ATTEMPT, {**values, **override})
    assert error.value.orig.pgcode == sqlstate


def test_duplicate_attempt_is_rejected(hus_student):
    conn, student = hus_student
    values = {**student, "attempt": 1, "grade_10": 8, "grade_4": 3, "status": "passed"}
    conn.execute(INSERT_ATTEMPT, values)
    with pytest.raises(IntegrityError) as error:
        with conn.begin_nested():
            conn.execute(INSERT_ATTEMPT, values)
    assert error.value.orig.pgcode == "23505"
