"""Read the checked-in HUS export, independently of synthetic UI fixtures."""

import json

import pytest

from app.config import PROJECT_ROOT
from database.hus_db.catalog_builder import build_catalogs


@pytest.fixture(scope="module")
def source_bundle():
    path = PROJECT_ROOT / "database" / "data" / "hus_source.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def source_catalogs(source_bundle):
    return {c.program.program_id: c for c in build_catalogs(source_bundle)}
