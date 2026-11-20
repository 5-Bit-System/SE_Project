"""Explicit historical fixtures for tests bound to sealed v3 evidence/indexes."""

import json
import shutil
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def historical_v3_root(tmp_path_factory):
    """Reproduce the original selector from its receipt, independent of CURRENT."""
    source = Path("data/hus/rag")
    target = tmp_path_factory.mktemp("historical-v3") / "rag"
    target.mkdir()
    for path in source.iterdir():
        if path.name in {"CURRENT.json", "releases"}:
            continue
        if path.is_dir():
            shutil.copytree(path, target / path.name)
        else:
            shutil.copyfile(path, target / path.name)
    receipt = json.loads(Path("data/hus/qa/20261102/p01/reconciliation.json").read_bytes())
    pointer = receipt["release_pointer"]
    relative = pointer["release_path"]
    shutil.copytree(source / relative, target / relative)
    (target / "CURRENT.json").write_text(json.dumps(pointer), encoding="utf-8")
    return target


@pytest.fixture(scope="module")
def historical_v3_data(historical_v3_root):
    from app.hus.rag_loader import HUSRAGData

    return HUSRAGData.load_current(historical_v3_root)


@pytest.fixture
def historical_v3_auditor(monkeypatch, historical_v3_root):
    """Keep the sealed v3 source auditor on the same root as its observations."""
    from app.services.hus_service import get_hus_answerer
    from tools import verify_hus_e2e

    get_hus_answerer.cache_clear()
    oracle = verify_hus_e2e.EvidenceOracle
    monkeypatch.setattr(verify_hus_e2e, "EvidenceOracle", lambda: oracle(package=historical_v3_root))
    yield
    get_hus_answerer.cache_clear()
