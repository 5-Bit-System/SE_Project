"""Regression of the actual publication, rollback and source integrity boundaries."""
import copy

import pytest
from sqlalchemy import text

from app.infrastructure.hus_repository import HusRepository
from tests.support.admin_catalog import PROGRAM, runtime_courses
from tests.support.admin_database import admin_test_engine

pytestmark = pytest.mark.hus_postgres


@pytest.fixture
def admin(verified_client, fake_accounts, monkeypatch):
    for account in fake_accounts.sessions.values():
        account['role'] = 'admin'
    monkeypatch.setattr('app.api.admin.engine', admin_test_engine)
    return verified_client


def imported(client, suffix='A'):
    with admin_test_engine().connect() as conn:
        first = runtime_courses(conn)[0]
    return client.post('/admin/catalog-revisions/import', json={'program_id': PROGRAM,
        'version_title': 'Synthetic ' + suffix, 'csv_content': f"code,name,credits\n{first['code']},Synthetic {suffix},3\n"}).json()['revision_id']


def publish(client, rid):
    assert client.post(f'/admin/catalog-revisions/{rid}/approve', json={'reason': 'Synthetic review'}).status_code == 200
    return client.post(f'/admin/catalog-revisions/{rid}/publish', json={'reason': 'Synthetic publish'})


def active_id():
    with admin_test_engine().connect() as conn:
        return conn.execute(text('SELECT revision_id FROM hus_catalog_revisions WHERE program_id=:p AND active'), {'p': PROGRAM}).scalar_one()


def test_publish_changes_actual_runtime_and_rollback_restores_exact_snapshot(admin):
    before = active_id()
    a = imported(admin)
    assert publish(admin, a).status_code == 200
    first = active_id()
    assert first != before
    with admin_test_engine().connect() as conn:
        catalog = HusRepository.__new__(HusRepository)._load_catalog(conn, PROGRAM)
        assert catalog.courses[0].name == 'Synthetic A'
        assert catalog.program.catalog_status == 'draft_unverified'
    b = imported(admin, 'B')
    assert publish(admin, b).status_code == 200
    assert active_id() != first
    assert admin.post(f'/admin/catalog-revisions/{a}/rollback', json={'reason': 'Synthetic rollback'}).status_code == 200
    assert active_id() == first


def test_invalid_revalidate_and_published_mutation_are_blocked(admin):
    bad = admin.post('/admin/catalog-revisions/import', json={'program_id': PROGRAM, 'version_title': 'Invalid',
        'csv_content': 'code,name,credits\nBAD,Invalid,-3\n'}).json()['revision_id']
    before = active_id()
    assert not admin.post(f'/admin/catalog-revisions/{bad}/validate').json()['validation_summary']['valid']
    assert publish_attempt(admin, bad).status_code == 400
    assert active_id() == before
    rid = imported(admin)
    assert publish(admin, rid).status_code == 200
    original = admin.get(f'/admin/catalog-revisions/{rid}').json()
    assert admin.post(f'/admin/catalog-revisions/{rid}/validate').status_code == 400
    with admin_test_engine().connect() as conn:
        from app.curriculum.repository import update_revision_payload
        with pytest.raises(ValueError, match='immutable'):
            update_revision_payload(conn, rid, copy.deepcopy(original['payload']))
    assert admin.get(f'/admin/catalog-revisions/{rid}').json()['payload'] == original['payload']


def publish_attempt(client, rid):
    return client.post(f'/admin/catalog-revisions/{rid}/approve', json={'reason': 'Synthetic review'})


def test_stale_base_and_tampered_manifest_fail_closed(admin):
    a, b = imported(admin, 'A'), imported(admin, 'B')
    assert publish(admin, a).status_code == 200
    current = active_id()
    assert publish(admin, b).status_code == 400
    assert active_id() == current
    c = imported(admin, 'C')
    assert publish(admin, c).status_code == 200
    with admin_test_engine().begin() as conn:
        conn.execute(text("UPDATE curriculum_revisions SET payload=jsonb_set(payload,'{courses,0,name}', '\"Tampered\"') WHERE revision_id=:id"), {'id': a})
    assert admin.post(f'/admin/catalog-revisions/{a}/rollback', json={'reason': 'Synthetic rollback'}).status_code == 400


def test_audit_failure_rolls_back_runtime_and_admin_pointer(admin, monkeypatch):
    rid = imported(admin)
    assert publish_attempt(admin, rid).status_code == 200
    before = active_id()
    def fail(*args, **kwargs):
        raise RuntimeError('Synthetic audit failure')
    monkeypatch.setattr('app.api.admin.log_admin_action', fail)
    with pytest.raises(RuntimeError, match='audit failure'):
        admin.post(f'/admin/catalog-revisions/{rid}/publish', json={'reason': 'Synthetic publish'})
    assert active_id() == before
    assert admin.get(f'/admin/catalog-revisions/{rid}').json()['status'] == 'approved'


def test_document_queue_get_does_not_seed_and_published_metadata_is_versioned(admin):
    from app.crawler.document_review_service import create_document, get_document, review_document
    engine = admin_test_engine()
    with engine.connect() as conn:
        before = conn.execute(text('SELECT count(*) FROM crawled_documents')).scalar_one()
    assert admin.get('/admin/crawler/documents').status_code == 200
    with engine.connect() as conn:
        assert conn.execute(text('SELECT count(*) FROM crawled_documents')).scalar_one() == before
    with engine.begin() as conn:
        doc = create_document(conn, url='https://example.invalid/source', title='Original', markdown_content='# Synthetic')
        review_document(conn, doc['id'], 'approved', 'Synthetic review')
        conn.execute(text('UPDATE crawled_documents SET is_published=true WHERE id=:id'), {'id': doc['id']})
        original = get_document(conn, doc['id'])
    updated = admin.put(f"/admin/crawler/documents/{doc['id']}/metadata", json={'title': 'Replacement'}).json()
    assert updated['id'] != doc['id'] and updated['review_status'] == 'pending'
    with engine.connect() as conn:
        preserved = get_document(conn, doc['id'])
        assert {k: v for k, v in preserved.items() if k not in {'duplicates', 'duplicate_count'}} == {
            k: v for k, v in original.items() if k not in {'duplicates', 'duplicate_count'}}


def test_full_source_bundle_preserves_catalog_structure_without_new_certification(admin):
    import json
    from pathlib import Path
    source = Path(__file__).resolve().parents[2] / 'database/data/hus_source.json'
    bundle = json.loads(source.read_text(encoding='utf-8'))
    response = admin.post('/admin/catalog-revisions/import', json={'program_id': PROGRAM,
        'version_title': 'Synthetic source review', 'source_bundle': bundle})
    assert response.status_code == 200
    rid = response.json()['revision_id']
    assert publish(admin, rid).status_code == 200
    with admin_test_engine().connect() as conn:
        catalog = HusRepository.__new__(HusRepository)._load_catalog(conn, PROGRAM)
    assert len(catalog.courses) == 65
    assert catalog.program.choice_groups
    assert catalog.metadata_schema_version == '1.0'
    assert catalog.program.catalog_status == 'draft_unverified'
    assert all(course.source_status == 'draft_unverified' for course in catalog.courses)


def test_simultaneous_publication_keeps_one_consistent_runtime_pointer():
    from concurrent.futures import ThreadPoolExecutor

    from sqlalchemy import create_engine

    from app.curriculum.repository import publish_revision, review_revision
    from tests.support.admin_catalog import complete_draft
    from tests.support.admin_database import admin_test_url
    engine = create_engine(admin_test_url())
    with engine.begin() as conn:
        baseline = conn.execute(text('SELECT revision_id FROM hus_catalog_revisions WHERE program_id=:p AND active'), {'p': PROGRAM}).scalar_one()
        drafts = [complete_draft(conn, 'Concurrent A'), complete_draft(conn, 'Concurrent B')]
        for draft in drafts:
            review_revision(conn, draft['revision_id'], None, 'approved', 'Synthetic concurrent review')
    def attempt(draft):
        try:
            with engine.begin() as conn:
                return publish_revision(conn, draft['revision_id'], None, 'Synthetic concurrent publish')
        except ValueError:
            return None
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, drafts))
        winners = [r for r in results if r is not None]
        assert len(winners) == 1
        with engine.connect() as conn:
            runtime = conn.execute(text('SELECT revision_id FROM hus_catalog_revisions WHERE program_id=:p AND active'), {'p': PROGRAM}).scalars().all()
            assert runtime == [winners[0]['provenance_manifest']['runtime_revision_id']]
            assert conn.execute(text('SELECT revision_id FROM curriculum_revisions WHERE program_id=:p AND is_active'), {'p': PROGRAM}).scalar_one() == winners[0]['revision_id']
    finally:
        with engine.begin() as conn:
            conn.execute(text('UPDATE hus_catalog_revisions SET active=false WHERE program_id=:p'), {'p': PROGRAM})
            conn.execute(text('UPDATE hus_catalog_revisions SET active=true WHERE revision_id=:id'), {'id': baseline})
            for draft in drafts:
                conn.execute(text('DELETE FROM curriculum_revisions WHERE revision_id=:id'), {'id': draft['revision_id']})
        engine.dispose()
