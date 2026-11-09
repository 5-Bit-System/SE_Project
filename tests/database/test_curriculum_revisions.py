"""Runtime-backed revision lifecycles on rollback-only test transactions."""
import pytest

from app.curriculum.publication_gate import compute_payload_digest
from app.curriculum.repository import (
    create_revision,
    get_active_revision,
    get_revision,
    list_reviews,
    publish_revision,
    review_revision,
    rollback_revision,
    update_validation,
)
from tests.support.admin_catalog import PROGRAM, complete_draft
from tests.support.admin_database import admin_test_engine

pytestmark = pytest.mark.hus_postgres

@pytest.fixture
def db_conn():
    with admin_test_engine().begin() as conn:
        yield conn

def approve_publish(conn, rev):
    review_revision(conn, rev['revision_id'], None, 'approved', 'Synthetic review')
    return publish_revision(conn, rev['revision_id'], None, 'Synthetic publish')

def test_create_curriculum_revision(db_conn):
    rev = complete_draft(db_conn)
    assert rev['status'] == 'validated' and not rev['is_active']
    assert get_revision(db_conn, rev['revision_id'])['payload'] == rev['payload']
    assert rev['payload']['runtime_catalog']['program']['program_id'] == PROGRAM

def test_status_transitions_and_review_audit(db_conn):
    rev = complete_draft(db_conn)
    published = approve_publish(db_conn, rev)
    assert published['status'] == 'published' and published['is_active']
    assert get_active_revision(db_conn, PROGRAM)['revision_id'] == rev['revision_id']
    assert {'created','validated','approved','published'} <= {r['action'] for r in list_reviews(db_conn, rev['revision_id'])}

def test_only_one_active_revision_and_rollback(db_conn):
    a = complete_draft(db_conn, 'A')
    approve_publish(db_conn, a)
    b = complete_draft(db_conn, 'B')
    approve_publish(db_conn, b)
    assert not get_revision(db_conn, a['revision_id'])['is_active']
    assert get_active_revision(db_conn, PROGRAM)['revision_id'] == b['revision_id']
    rollback_revision(db_conn, PROGRAM, a['revision_id'], None, 'Synthetic rollback')
    assert get_active_revision(db_conn, PROGRAM)['revision_id'] == a['revision_id']

def test_approval_rejects_missing_or_stale_validation(db_conn):
    payload = {'courses': [{'code': 'A', 'name': 'A', 'credits': 3}]}
    rev = create_revision(db_conn, PROGRAM, 'Invalid review', payload, 'synthetic')
    with pytest.raises(ValueError, match='validat'):
        review_revision(db_conn, rev['revision_id'], None, 'approved', 'Synthetic review')
    bad = {'valid': False, 'errors': ['invalid'], 'payload_digest': compute_payload_digest(payload)}
    update_validation(db_conn, rev['revision_id'], 'draft', bad)
    with pytest.raises(ValueError, match='validat'):
        review_revision(db_conn, rev['revision_id'], None, 'approved', 'Synthetic review')
    with pytest.raises(ValueError, match='Stale'):
        update_validation(db_conn, rev['revision_id'], 'validated', {'valid': True, 'payload_digest': 'stale'})

def test_rollback_restrictions_fail_closed(db_conn):
    active = complete_draft(db_conn, 'Active')
    approve_publish(db_conn, active)
    draft = complete_draft(db_conn, 'Draft')
    with pytest.raises(ValueError, match='previously published'):
        rollback_revision(db_conn, PROGRAM, draft['revision_id'], None, 'Invalid rollback')
    review_revision(db_conn, draft['revision_id'], None, 'rejected', 'Synthetic rejection')
    with pytest.raises(ValueError, match='previously published'):
        rollback_revision(db_conn, PROGRAM, draft['revision_id'], None, 'Invalid rollback')
    approved = complete_draft(db_conn, 'Approved')
    review_revision(db_conn, approved['revision_id'], None, 'approved', 'Synthetic review')
    with pytest.raises(ValueError, match='previously published'):
        rollback_revision(db_conn, PROGRAM, approved['revision_id'], None, 'Invalid rollback')
    other = complete_draft(db_conn, 'Other', 'toan_tin_7460117_2022')
    approve_publish(db_conn, other)
    with pytest.raises(ValueError, match='belongs to'):
        rollback_revision(db_conn, PROGRAM, other['revision_id'], None, 'Invalid rollback')
    assert get_active_revision(db_conn, PROGRAM)['revision_id'] == active['revision_id']
