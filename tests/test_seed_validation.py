"""Seed preflight and JSONB contract checks that require no live database."""

import json

import pytest
from sqlalchemy import create_engine

from app.catalog_normalization import normalize_catalog
from app.db import schema as db
from app.errors import StorageDataError
from app.infrastructure.postgres_repository import PostgresRepository
from tests.catalog_fixtures import create_catalog_fixture
from tools.seed_database import _seed_revision, seed_database


def metadata_bundle():
    program = {
        "program_id": "khdl_7460108_2022",
        "name": "Synthetic",
        "total_credits": 3,
        "source_file": "synthetic",
        "source_pages": "1-1",
        "choice_groups": [],
        "track_selection": {"tracks": []},
        "graduation_selection": {"paths": []},
        "catalog_revision": "source-revision",
        "metadata_schema_version": "1.0",
        "vocabulary_version": "1.0",
    }
    course = {
        "code": "TEST1",
        "name": "Synthetic course",
        "credits": 3,
        "block": "major",
        "requirement_type": "required",
        "counted_in_total": True,
        "prerequisite_status": "unknown",
        "prerequisites": [],
        "choice_group_ids": [],
        "graduation_path_ids": [],
        "source_status": "draft_unverified",
        "offering_status": "unknown",
        "field_evidence": {},
    }
    for field in (
        "code",
        "name",
        "credits",
        "block",
        "requirement_type",
        "counted_in_total",
        "prerequisites",
        "choice_group_ids",
        "graduation_path_ids",
    ):
        course["field_evidence"][field] = [
            {
                "source_ref": "synthetic-test-contract",
                "locator": "test-definition",
                "method": "transcription",
                "status": "draft_unverified",
            }
        ]
    envelope = {
        "metadata_schema_version": "1.0",
        "vocabulary_version": "1.0",
        "program_id": program["program_id"],
        "catalog_revision": "source-revision",
        "courses": [course],
    }
    return {
        "program": program,
        "courses": [course],
        "envelope": envelope,
        "vocabulary": {"vocabulary_version": "1.0", "topics": [], "career_paths": []},
        "sources": [],
        "profiles": [],
    }


def read_bundle(bundle):
    engine = create_engine("sqlite://")
    db.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            db.programs.insert().values(program_id=bundle["program"]["program_id"], name="Test")
        )
        _seed_revision(conn, "a" * 64, bundle)
        conn.execute(db.catalog_revisions.update().values(active=True))
        return PostgresRepository(engine)._load_catalog(conn, "khdl")


def test_jsonb_metadata_round_trip_matches_json_without_program_pollution():
    bundle = metadata_bundle()
    actual = read_bundle(bundle)
    expected = normalize_catalog(bundle["program"], bundle["envelope"], bundle["vocabulary"])
    assert actual.model_dump() == expected.model_dump()
    assert actual.program.catalog_revision != "a" * 64


def test_database_read_revalidates_envelope_vocabulary_contract():
    bundle = metadata_bundle()
    bundle["vocabulary"]["vocabulary_version"] = "corrupted"
    with pytest.raises(StorageDataError, match="vocabulary"):
        read_bundle(bundle)


def test_legacy_jsonb_payload_uses_same_status_normalization_as_json():
    bundle = metadata_bundle()
    bundle["envelope"] = None
    bundle["vocabulary"] = None
    bundle["courses"][0]["prerequisite_status"] = "transcribed"
    actual = read_bundle(bundle)
    assert actual == normalize_catalog(bundle["program"], bundle["courses"])


class NoDatabaseAccess:
    def begin(self):
        pytest.fail("Invalid sources must fail before opening a database transaction")


def test_missing_profiles_does_not_open_database(tmp_path):
    with pytest.raises(ValueError, match="Profiles file not found"):
        seed_database(NoDatabaseAccess(), data_root=tmp_path, profiles_path=tmp_path / "missing")


def test_conflicting_root_aliases_fail_before_database_access(tmp_path):
    with pytest.raises(ValueError, match="source_root.*data_root"):
        seed_database(NoDatabaseAccess(), source_root=tmp_path / "a", data_root=tmp_path / "b")


@pytest.mark.parametrize("problem", ["envelope", "missing_catalog", "missing_rows"])
def test_invalid_sources_fail_before_transaction(tmp_path, problem):
    catalog_root, profiles_path = create_catalog_fixture(tmp_path, envelope=True)
    directory = catalog_root / "khdl_7460108_2022"
    if problem == "envelope":
        path = directory / "courses.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["catalog_revision"] = "wrong-revision"
        path.write_text(json.dumps(document), encoding="utf-8")
    elif problem == "missing_rows":
        (directory / "source_rows.json").unlink()
    else:
        # An entirely missing catalog must not let any valid catalog publish first.
        import shutil

        shutil.rmtree(directory)
    with pytest.raises((ValueError, OSError, StorageDataError)):
        seed_database(NoDatabaseAccess(), data_root=catalog_root, profiles_path=profiles_path)
