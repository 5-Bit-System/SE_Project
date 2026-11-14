"""Offline VT-102 40-actor ASGI experiment. Never invokes VNU, a real DB or an LLM."""

import argparse
import asyncio
import importlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/vt102/evidence/load.json"))
    args = parser.parse_args()
    # Use the same explicit offline environment as the repository's test suite.
    importlib.import_module("tests.conftest")
    import pytest

    from app.config import get_settings
    from tests.support.catalog_fixtures import create_catalog_fixture
    from tests.support.vt102_harness import workload

    parent = Path("backups/vt102_load")
    parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=parent) as temporary, pytest.MonkeyPatch.context() as patch:
        catalog_root, _ = create_catalog_fixture(Path(temporary) / "catalogs")
        patch.setattr("app.catalog.DATA_ROOT", catalog_root)
        get_settings.cache_clear()
        report = asyncio.run(workload(patch, 40))
    report["target_p95_ms"] = 1500
    report["passed"] = report["error_rate"] == 0 and all(
        row["p95_ms"] <= 1500 for row in report["metrics"].values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
