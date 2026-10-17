"""PostgreSQL integration tests create/drop only their own random schemas.

Set TEST_DATABASE_URL explicitly; no test resets the user's public schema.
Default pytest skips these tests when no test database is supplied.
"""

import json
import os
import shutil
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateSchema, DropSchema

from tests.catalog_fixtures import create_catalog_fixture
from app.config import PROJECT_ROOT
from app.db import schema as db
from app.errors import StorageDataError
from app.infrastructure.json_catalog_repository import list_catalogs
from app.infrastructure.postgres_repository import PostgresRepository
from app.main import app
from app.profiles import DemoProfile
from app.rules import evaluate_eligibility
from tools.seed_database import seed_database

pytestmark = pytest.mark.postgres


@pytest.fixture
def postgres_engine():
    url = os.getenv("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration tests")
    engine = create_engine(url, hide_parameters=True, connect_args={"connect_timeout": 5})
    namespace = "se_test_" + uuid4().hex
    with engine.begin() as conn:
        conn.execute(CreateSchema(namespace))
    isolated = engine.execution_options(schema_translate_map={None: namespace})
    try:
        yield isolated, namespace
    finally:
        with engine.begin() as conn:
            conn.execute(DropSchema(namespace, cascade=True))
        engine.dispose()


@pytest.fixture
def source_bundle(tmp_path):
    return create_catalog_fixture(tmp_path / "seed_sources", envelope=True)


@pytest.fixture
def seeded_engine(postgres_engine, source_bundle):
    catalog_root, profiles_path = source_bundle
    engine, _ = postgres_engine
    db.metadata.create_all(engine)
    seed_database(engine, data_root=catalog_root, profiles_path=profiles_path)
    return engine


def counts(engine):
    with engine.connect() as conn:
        return {
            table.name: conn.execute(select(func.count()).select_from(table)).scalar_one()
            for table in db.metadata.sorted_tables
        }


def test_seed_is_idempotent_and_catalog_round_trip_is_lossless(seeded_engine, source_bundle):
    catalog_root, profiles_path = source_bundle
    before = counts(seeded_engine)
    assert (
        seed_database(seeded_engine, data_root=catalog_root, profiles_path=profiles_path)[
            "new_revisions"
        ]
        == 0
    )
    assert counts(seeded_engine) == before
    assert before["programs"] == 4
    assert before["courses"] == sum(len(c.courses) for c in list_catalogs(catalog_root))
    assert before["demo_profiles"] == 12
    assert before["prerequisite_options"] == sum(
        len(clause)
        for c in list_catalogs(catalog_root)
        for course in c.courses
        for clause in course.prerequisites
    )
    repository = PostgresRepository(seeded_engine)
    for source in list_catalogs(catalog_root):
        actual = repository.load_catalog(source.program.program_id)
        assert actual.model_dump() == source.model_dump()
    # Check typed metadata preserved on KHDL
    khdl_actual = repository.load_catalog("khdl")
    assert khdl_actual.metadata_schema_version == "1.0"
    assert khdl_actual.courses[0].field_evidence != {}
    actual_profiles = {
        item["profile_id"]: DemoProfile.model_validate(item) for item in repository.read_profiles()
    }
    for item in json.loads(profiles_path.read_text(encoding="utf-8")):
        source_profile = DemoProfile.model_validate(item)
        assert actual_profiles[source_profile.profile_id] == source_profile
        catalog = repository.load_catalog(source_profile.program_id)
        source = next(
            cat
            for cat in list_catalogs(catalog_root)
            if cat.program.program_id == source_profile.program_id
        )
        passed = source_profile.to_transcript().passed_course_codes
        assert (
            evaluate_eligibility(catalog, passed).model_dump()
            == evaluate_eligibility(source, passed).model_dump()
        )


def test_transcript_fk_rejects_a_course_from_another_major(seeded_engine):
    with seeded_engine.connect() as conn:
        revision = conn.execute(
            select(db.catalog_revisions.c.revision_id).where(
                db.catalog_revisions.c.program_id == "khdl_7460108_2022"
            )
        ).scalar_one()
        assert (
            conn.execute(
                select(db.courses.c.code).where(
                    db.courses.c.revision_id == revision, db.courses.c.code == "TOAN_HOC101"
                )
            ).first()
            is None
        )
    with pytest.raises(IntegrityError), seeded_engine.begin() as conn:
        conn.execute(
            db.transcript_records.insert().values(
                revision_id=revision,
                profile_id="khdl_01",
                course_code="TOAN_HOC101",
                position=999,
                grade=8,
                passed=True,
                term=1,
                payload={},
            )
        )


@pytest.mark.parametrize("grade,passed", [(11, True), (-1, False), (3, True), (8, False)])
def test_transcript_grade_and_pass_constraints(seeded_engine, grade, passed):
    with seeded_engine.connect() as conn:
        row = conn.execute(select(db.transcript_records)).mappings().first()
    with pytest.raises(IntegrityError), seeded_engine.begin() as conn:
        conn.execute(
            db.transcript_records.update()
            .where(
                db.transcript_records.c.revision_id == row["revision_id"],
                db.transcript_records.c.profile_id == row["profile_id"],
                db.transcript_records.c.course_code == row["course_code"],
            )
            .values(grade=grade, passed=passed)
        )


def test_external_prerequisites_remain_unverified(seeded_engine):
    with seeded_engine.connect() as conn:
        external = (
            conn.execute(
                select(db.prerequisite_options).where(
                    db.prerequisite_options.c.external_code.is_not(None)
                )
            )
            .mappings()
            .all()
        )
    assert external
    assert all(
        row["required_code"] is None and row["verification_status"] == "unverified"
        for row in external
    )
    row = external[0]
    with pytest.raises(IntegrityError), seeded_engine.begin() as conn:
        conn.execute(
            db.prerequisite_options.update()
            .where(
                db.prerequisite_options.c.revision_id == row["revision_id"],
                db.prerequisite_options.c.course_code == row["course_code"],
                db.prerequisite_options.c.group_no == row["group_no"],
                db.prerequisite_options.c.option_no == row["option_no"],
            )
            .values(verification_status="verified")
        )


def changed_sources(tmp_path, catalog_root):
    root = tmp_path / "curricula"
    shutil.copytree(catalog_root, root)
    path = root / "khdl_7460108_2022" / "curriculum.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["notes"].append("Integration test revision")
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return root


def test_changed_source_creates_revision_without_overwriting_history(
    seeded_engine, tmp_path, source_bundle
):
    catalog_root, profiles_path = source_bundle
    before = counts(seeded_engine)
    result = seed_database(
        seeded_engine,
        data_root=changed_sources(tmp_path, catalog_root),
        profiles_path=profiles_path,
    )
    assert result["new_revisions"] == 1
    after = counts(seeded_engine)
    assert after["catalog_revisions"] == before["catalog_revisions"] + 1
    assert after["courses"] == before["courses"] + len(
        PostgresRepository(seeded_engine).load_catalog("khdl").courses
    )
    with seeded_engine.connect() as conn:
        assert (
            len(
                conn.execute(
                    select(db.catalog_revisions).where(db.catalog_revisions.c.active.is_(True))
                ).all()
            )
            == 4
        )
    assert (
        PostgresRepository(seeded_engine).load_catalog("khdl").program.notes[-1]
        == "Integration test revision"
    )


def test_failed_seed_rolls_back_all_new_rows(seeded_engine, tmp_path, monkeypatch, source_bundle):
    catalog_root, profiles_path = source_bundle
    before = counts(seeded_engine)
    from tools import seed_database as seed_module

    original = seed_module._seed_revision

    def fail_after_insert(conn, revision_id, bundle):
        original(conn, revision_id, bundle)
        raise RuntimeError("Simulated import failure")

    monkeypatch.setattr(seed_module, "_seed_revision", fail_after_insert)
    with pytest.raises(RuntimeError, match="Simulated"):
        seed_database(
            seeded_engine,
            data_root=changed_sources(tmp_path, catalog_root),
            profiles_path=profiles_path,
        )
    assert counts(seeded_engine) == before


def test_seed_missing_profiles_or_invalid_envelope_fails_before_mutation(
    seeded_engine, tmp_path, source_bundle
):
    catalog_root, profiles_path = source_bundle
    before = counts(seeded_engine)
    nonexistent = tmp_path / "nonexistent.json"
    with pytest.raises(ValueError, match="Profiles file not found"):
        seed_database(seeded_engine, data_root=catalog_root, profiles_path=nonexistent)
    assert counts(seeded_engine) == before

    root = tmp_path / "curricula_bad"
    shutil.copytree(catalog_root, root)
    courses_file = root / "khdl_7460108_2022" / "courses.json"
    envelope = json.loads(courses_file.read_text(encoding="utf-8"))
    envelope["metadata_schema_version"] = "99.0"
    courses_file.write_text(json.dumps(envelope), encoding="utf-8")

    with pytest.raises(StorageDataError):
        seed_database(seeded_engine, data_root=root, profiles_path=profiles_path)
    assert counts(seeded_engine) == before


@pytest.mark.parametrize("component", ["vocabulary", "evidence", "source_rows", "profiles"])
def test_changing_bundle_creates_new_revision(seeded_engine, tmp_path, source_bundle, component):
    catalog_root, profiles_path = source_bundle
    before = counts(seeded_engine)
    root = tmp_path / "curricula_vocab"
    shutil.copytree(catalog_root, root)
    if component == "profiles":
        document = json.loads(profiles_path.read_text(encoding="utf-8"))
        document[0]["label"] += " revised"
        profiles_path = tmp_path / "profiles_changed.json"
        profiles_path.write_text(json.dumps(document), encoding="utf-8")
    else:
        filename = {
            "vocabulary": "vocabulary.json",
            "evidence": "courses.json",
            "source_rows": "source_rows.json",
        }[component]
        path = root / "khdl_7460108_2022" / filename
        document = json.loads(path.read_text(encoding="utf-8"))
        if component == "vocabulary":
            document["note"] = "Revised synthetic vocabulary note"
        elif component == "evidence":
            document["courses"][0]["field_evidence"]["topics"][0]["note"] = "Revised evidence note"
        else:
            document[0]["source_note"] = "Revised transcription note"
        path.write_text(json.dumps(document), encoding="utf-8")

    result = seed_database(seeded_engine, data_root=root, profiles_path=profiles_path)
    assert result["new_revisions"] == 1
    after = counts(seeded_engine)
    assert after["catalog_revisions"] == before["catalog_revisions"] + 1


def test_runtime_api_uses_postgresql(seeded_engine, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "postgres")
    monkeypatch.setenv("DATABASE_MODEL", "legacy")
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setattr("app.infrastructure.postgres_repository.get_engine", lambda: seeded_engine)
    with TestClient(app) as client:
        assert client.get("/ready").json() == {"status": "ok", "storage": "postgres"}
        assert len(client.get("/programs").json()) == 4
        assert len(client.get("/profiles").json()) == 12
        assert len(client.get("/courses", params={"program_id": "khdl"}).json()) == len(
            PostgresRepository(seeded_engine).load_catalog("khdl").courses
        )
        assert client.get("/profiles/khdl_01/transcript/summary").status_code == 200
        response = client.post("/recommendations", json={"program_id": "khdl"})
        assert response.status_code == 200
        assert response.json()["recommendations"]
        assert client.get("/courses", params={"program_id": "foreign"}).status_code == 404


def test_migration_upgrade_downgrade_upgrade(postgres_engine, source_bundle):
    catalog_root, profiles_path = source_bundle
    engine, namespace = postgres_engine
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    with engine.begin() as conn:
        config.attributes["connection"] = conn
        command.upgrade(config, "head")
        assert set(inspect(conn).get_table_names(schema=namespace)) == set(db.metadata.tables) | {
            "alembic_version"
        }
        command.downgrade(config, "base")
        assert inspect(conn).get_table_names(schema=namespace) == ["alembic_version"]
        command.upgrade(config, "head")
    assert (
        seed_database(engine, data_root=catalog_root, profiles_path=profiles_path)["new_revisions"]
        == 4
    )
    PostgresRepository(engine).ready()
