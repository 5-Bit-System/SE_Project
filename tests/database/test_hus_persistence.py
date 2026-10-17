"""Offline checks for HUS publication and immutable revision reads."""

import copy
import json

import pytest

from app.catalog_contracts import catalog_payload, catalog_revision, digest
from app.errors import StorageDataError
from app.infrastructure.hus_repository import HusRepository
from database.hus_db.catalog_builder import build_catalogs
from database.tools.publish_catalogs import SOURCE, publish_catalogs


@pytest.fixture(scope="module")
def bundle():
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def test_revisions_are_deterministic_and_source_bound(bundle):
    first = build_catalogs(bundle)[0]
    source_digest = digest(bundle)
    revision = catalog_revision(first, source_digest)
    assert revision == catalog_revision(build_catalogs(bundle)[0], source_digest)
    assert revision != catalog_revision(first, "0" * 64)


def test_repository_rejects_tampered_revision(bundle):
    catalog = build_catalogs(bundle)[0]
    row = {
        "payload": catalog_payload(catalog),
        "program_id": catalog.program.program_id,
        "curriculum_id": 123,
        "source_digest": digest(bundle),
        "revision_id": "0" * 64,
    }
    with pytest.raises(StorageDataError, match="hash"):
        HusRepository._validated(row, {"program_id": catalog.program.program_id, "curriculum_id": 123})


def test_publisher_preflight_rejects_bad_bundle_without_connection(bundle):
    broken = copy.deepcopy(bundle)
    broken["tables"]["majors"].append(broken["tables"]["majors"][0])
    with pytest.raises(ValueError):
        publish_catalogs(None, broken)  # type: ignore[arg-type]
