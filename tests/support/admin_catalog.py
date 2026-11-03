"""Complete runtime-backed drafts for isolated admin database tests."""
from sqlalchemy import text

from app.curriculum.publication_gate import compute_payload_digest
from app.curriculum.repository import create_revision, update_validation
from app.curriculum.runtime_publication import prepare_catalog

PROGRAM = 'khdl_7460108_2022'


def runtime_courses(conn, program=PROGRAM):
    payload = conn.execute(text('SELECT payload FROM hus_catalog_revisions WHERE program_id=:p AND active'), {'p': program}).scalar_one()
    return payload['courses']


def complete_draft(conn, title='Synthetic test draft', program=PROGRAM):
    first = runtime_courses(conn, program)[0]
    courses = [{**first, 'name': first['name'] + ' ' + title}]
    payload = {'courses': courses, **prepare_catalog(conn, program, courses, 'synthetic-' + title)}
    rev = create_revision(conn, program, title, payload, 'synthetic-' + title)
    return update_validation(conn, rev['revision_id'], 'validated', {
        'valid': True, 'errors': [], 'payload_digest': compute_payload_digest(payload)})
