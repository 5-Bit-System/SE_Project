"""Compile reviewed admin drafts into complete canonical HUS snapshots."""
import json

from sqlalchemy import text

from app.catalog_contracts import catalog_payload, catalog_revision, digest
from app.catalog_validation import validate_catalog
from app.models import Catalog


def prepare_catalog(conn, program_id, courses, source_digest, source_bundle=None):
    """CSV patches known courses; full source bundles use the existing HUS builder."""
    row = conn.execute(text('SELECT * FROM hus_catalog_revisions WHERE program_id=:p AND active'),
                       {'p': program_id}).mappings().one_or_none()
    if not row:
        raise ValueError('Unknown runtime program; a canonical HUS catalog is required')
    from app.infrastructure.hus_repository import HusRepository
    base = HusRepository._validated(row, row)
    if source_bundle is not None:
        from database.hus_db.catalog_builder import build_catalogs
        selected = [c for c in build_catalogs(source_bundle) if c.program.program_id == program_id]
        if len(selected) != 1:
            raise ValueError('Source bundle does not identify this program')
        candidate = catalog_payload(selected[0])
        for course in candidate['courses']:
            course['source_status'] = 'draft_unverified'
            if course['prerequisite_status'] == 'verified':
                course['prerequisite_status'] = 'draft_unverified'
            for evidence in course['field_evidence'].values():
                for item in evidence:
                    if item['status'] == 'verified':
                        item['status'] = 'draft_unverified'
    else:
        candidate = catalog_payload(base)
        by_code = {c['code']: c for c in candidate['courses']}
        for patch in courses:
            if patch['code'] not in by_code:
                raise ValueError('New course codes require a complete HUS source bundle')
            target = by_code[patch['code']]
            for field in ('name', 'credits', 'prerequisites', 'suggested_term'):
                value = patch.get(field)
                if field == 'prerequisites':
                    value = [[p] if isinstance(p, str) else p for p in value or []]
                if field == 'suggested_term' and value is None:
                    continue
                if target.get(field) != value:
                    target[field] = value
                    target.setdefault('field_evidence', {})[field] = [{
                        'source_ref': 'admin-import:' + source_digest, 'locator': f"{patch['code']}/{field}",
                        'method': 'transcription', 'status': 'draft_unverified',
                        'note': 'Admin draft; not an official academic sign-off',
                    }]
                    target['source_status'] = 'draft_unverified'
                    if field == 'prerequisites':
                        target.update(prerequisite_status='draft_unverified', prerequisite_variants=[],
                                      prerequisites_raw=json.dumps(value), external_prerequisite_codes=[])
    # Approval is a publication decision, never a new academic certification.
    candidate['program']['catalog_status'] = 'draft_unverified'
    candidate['program']['catalog_revision'] = None
    candidate['program']['catalog_revision'] = digest(candidate)
    catalog = Catalog.model_validate(candidate)
    validate_catalog(catalog)
    return {'runtime_catalog': catalog_payload(catalog), 'runtime_base_revision': row['revision_id'],
            'runtime_source_digest': source_digest}


def validate_runtime_payload(payload, program_id):
    raw = payload.get('runtime_catalog')
    if not isinstance(raw, dict):
        raise ValueError('Publication requires a complete validated runtime catalog; import known codes or a HUS source bundle')
    catalog = Catalog.model_validate(raw)
    if catalog.program.program_id != program_id or catalog.program.catalog_status != 'draft_unverified':
        raise ValueError('Runtime catalog scope or review state does not match draft')
    validate_catalog(catalog)
    candidates = {c.code: c for c in catalog.courses}
    for course in payload['courses']:
        current = candidates.get(course['code'])
        prereqs = [[p] if isinstance(p, str) else p for p in course.get('prerequisites', [])]
        if (not current or current.name != course['name'] or current.credits != course['credits']
                or current.prerequisites != prereqs):
            raise ValueError('Runtime candidate does not match the reviewed draft')
    return catalog


def publish_runtime(conn, revision):
    payload = revision['payload']
    catalog = validate_runtime_payload(payload, revision['program_id'])
    base = conn.execute(text('SELECT * FROM hus_catalog_revisions WHERE program_id=:p AND active FOR UPDATE'),
                        {'p': revision['program_id']}).mappings().one_or_none()
    if not base or base['revision_id'] != payload.get('runtime_base_revision'):
        raise ValueError('Runtime catalog changed since import; import and review against the latest revision')
    source_digest = digest({'admin_revision': revision['revision_id'], 'payload': payload})
    runtime_id = catalog_revision(catalog, source_digest)
    conn.execute(text('''INSERT INTO hus_catalog_revisions
        (revision_id,curriculum_id,program_id,active,source_digest,payload)
        VALUES (:r,:c,:p,false,:s,CAST(:payload AS jsonb))'''),
        {'r': runtime_id, 'c': base['curriculum_id'], 'p': revision['program_id'], 's': source_digest,
         'payload': json.dumps(catalog_payload(catalog))})
    conn.execute(text('UPDATE hus_catalog_revisions SET active=false WHERE program_id=:p'), {'p': revision['program_id']})
    conn.execute(text('UPDATE hus_catalog_revisions SET active=true WHERE revision_id=:r'), {'r': runtime_id})
    return runtime_id


def activate_runtime(conn, revision, manifest):
    runtime_id = manifest.get('runtime_revision_id')
    row = conn.execute(text('SELECT * FROM hus_catalog_revisions WHERE revision_id=:r AND program_id=:p'),
                       {'r': runtime_id, 'p': revision['program_id']}).mappings().one_or_none()
    if not row:
        raise ValueError('Rollback target has no canonical runtime snapshot')
    from app.infrastructure.hus_repository import HusRepository
    catalog = HusRepository._validated(row, row)
    if catalog_payload(catalog) != revision['payload']['runtime_catalog']:
        raise ValueError('Rollback runtime snapshot differs from reviewed payload')
    conn.execute(text('UPDATE hus_catalog_revisions SET active=false WHERE program_id=:p'), {'p': revision['program_id']})
    conn.execute(text('UPDATE hus_catalog_revisions SET active=true WHERE revision_id=:r'), {'r': runtime_id})
