"""Test runners must fail before connecting to the user's application database."""
import runpy
from pathlib import Path

import pytest


def test_admin_tests_require_explicit_test_url(monkeypatch):
    from tests.support.admin_database import admin_test_url
    monkeypatch.delenv('HUS_TEST_DATABASE_URL', raising=False)
    monkeypatch.setenv('DATABASE_URL', 'postgresql://synthetic:synthetic@127.0.0.1:5433/ai07')
    with pytest.raises(pytest.skip.Exception):
        admin_test_url()


def test_browser_harness_rejects_the_runtime_target_including_host_aliases(monkeypatch):
    monkeypatch.setenv('HUS_TEST_DATABASE_URL', 'postgresql://synthetic:synthetic@127.0.0.1:5433/ai07')
    monkeypatch.setattr('dotenv.dotenv_values', lambda path: {'DATABASE_URL': 'postgresql://synthetic:synthetic@localhost:5433/ai07'})
    path = Path(__file__).resolve().parents[2] / 'tools/verify_admin_console.py'
    with pytest.raises(SystemExit, match='configured application database'):
        runpy.run_path(str(path), run_name='guard_test')
