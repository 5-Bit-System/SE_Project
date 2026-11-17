"""Shared synthetic account/source fixtures for source-owned API integration tests."""

import copy

import pytest
from fastapi.testclient import TestClient

from app.integrations.daotao import runtime, store
from app.main import app


@pytest.fixture
def client(monkeypatch, fake_accounts):
    runtime.sessions.clear()
    seen = []
    data = {"subject": "synthetic", "profile": {}, "snapshot": {
        "schema_version": 1, "completeness": "unknown", "digest": "synthetic",
        "attempts": [], "unknown_rows": []}, "fetched_at": None}

    def profile(owner):
        seen.append(owner)
        return copy.deepcopy(data)

    monkeypatch.setattr(store, "profile", profile)
    with TestClient(app, base_url="http://127.0.0.1:8000") as value:
        value.headers["origin"] = "http://127.0.0.1:8000"
        value.seen_owners = seen
        value.profile_data = data
        value.fake_accounts = fake_accounts
        yield value
    runtime.sessions.clear()


@pytest.fixture
def ready_context(client, monkeypatch):
    # Test-only evidence/policy. Never enable these settings for a real account.
    import importlib.util
    assert importlib.util.find_spec('app.api.academic') is not None, 'Source-owned API missing'
    from app.api import academic
    from tests.support.catalog_fixtures import mark_catalog_reviewed_for_test

    load_catalog = academic.load_catalog
    monkeypatch.setattr(academic, 'load_catalog', lambda program_id:
                        mark_catalog_reviewed_for_test(load_catalog(program_id)))

    client.fake_accounts.issue(client, 'synthetic-owner', 'synthetic', linked=True)
    client.profile_data['profile'].update(program='Khoa học dữ liệu', cohort='68')
    client.profile_data['snapshot'].update(completeness='complete', attempts=[{
        'row_key': '0', 'code': 'PHI1006', 'credits': '3', 'grade10': '4.2',
        'letter': 'D', 'grade4': '1'}])
    context = client.get('/me/academic-context?program_id=khdl').json()
    assert context['status'] == 'ready'
    assert context['completed_course_codes'] == ['PHI1006']
    return context
