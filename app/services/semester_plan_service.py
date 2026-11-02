"""Durable personal plans; account, source and catalog are checked under locks."""

import json
import uuid

from sqlalchemy import text

from app.academic_context import AcademicContextError, build_context
from app.academic_policies import POLICIES
from app.auth import portal, repository
from app.auth.security import AuthFailure
from app.catalog_contracts import digest
from app.infrastructure.hus_repository import HusRepository
from app.program_bindings import binding_current, catalog_fingerprint
from app.rules import _prepare_selection_context
from app.services.course_status_service import (
    course_board,
    reviewed_course_board,
    validate_plan_courses,
)


class PlanError(AuthFailure):
    def __init__(self, code):
        super().__init__(code, 409)


def basis_for(saved, catalog, track, path):
    """No app-session token or timestamp: a new login must not stale a plan."""
    binding = (saved.get('profile') or {}).get('academic_binding') or {}
    return {'snapshot_digest': (saved.get('snapshot') or {}).get('digest'),
            'source_scope': binding.get('source_scope'),
            'catalog_revision': digest(catalog.model_dump(mode='json')),
            'binding_digest': digest(binding),
            'policy_digest': digest(vars(POLICIES[binding['policy_version']]))
            if binding.get('policy_version') in POLICIES else None,
            'track': track, 'path': path}


def source(conn, principal, *, lock=False):
    link = repository.portal_link(principal['account_id'], conn)
    if not link:
        return None
    row = conn.execute(text('''
        SELECT u.profile, s.payload AS snapshot FROM portal_users u
        LEFT JOIN portal_transcript_snapshots s ON s.owner=u.id AND s.id=u.current_snapshot_id
        WHERE u.id=:owner
    ''' + (' FOR UPDATE OF u' if lock else '')), {'owner': link['owner']}).mappings().one_or_none()
    return dict(row) if row else None


def serialize(row):
    result = dict(row)
    result['id'] = str(result['id'])
    result.pop('account_id', None)
    for key in ('created_at', 'updated_at'):
        result[key] = result[key].isoformat()
    result['course_codes'] = [course['code'] for course in result['courses']]
    return result


def list_plans(principal):
    with repository.engine().begin() as conn:
        actor = repository.current(conn, principal['session_id'], lock=True)
        saved = source(conn, actor, lock=True)
        rows = conn.execute(text('''SELECT * FROM semester_plans WHERE account_id=:account
            ORDER BY updated_at DESC, id'''), {'account': actor['account_id']}).mappings().all()
        result = []
        for row in rows:
            item = serialize(row)
            reasons = []
            if not saved or not saved.get('snapshot'):
                reasons.append('source_missing')
            elif not binding_current(saved.get('profile') or {}):
                reasons.append('program_binding_unverified')
            else:
                try:
                    catalog = HusRepository(conn.engine)._load_catalog(conn, row['program_id'])
                    current = basis_for(saved, catalog, row['selected_track_id'],
                                        row['selected_graduation_path_id'])
                    if current != row['basis']:
                        reasons.append('academic_data_changed')
                except ValueError:
                    reasons.append('program_unavailable')
            item.update(needs_review=bool(reasons), review_reasons=reasons)
            result.append(item)
        return result


def save_plan(value, body, plan_id=None):
    with repository.engine().begin() as conn:
        actor = portal.bound(conn, value, lock=True)
        saved = source(conn, actor, lock=True)
        if not saved or not binding_current(saved.get('profile') or {}):
            raise PlanError('program_binding_unverified')
        # Serialize against publication/activation, then use exactly that catalog.
        conn.execute(text("SELECT pg_advisory_xact_lock(hashtext('ai07_hus_catalog_publish'))"))
        binding = saved['profile']['academic_binding']
        conn.execute(text('''SELECT revision_id FROM hus_catalog_revisions
            WHERE program_id=:program AND active FOR SHARE'''),
            {'program': binding['program_id']})
        catalog = HusRepository(conn.engine)._load_catalog(conn, binding['program_id'])
        track, path = body.selected_track_id, body.selected_graduation_path_id
        try:
            _prepare_selection_context(catalog, track, path)
        except ValueError:
            raise PlanError('academic_program_invalid') from None
        if ((catalog.program.track_selection.mode == 'exactly_one_track' and not track)
                or (catalog.program.graduation_selection.mode == 'exactly_one_path' and not path)):
            raise PlanError('semester_plan_selection_required')
        basis = basis_for(saved, catalog, track, path)
        if digest(basis) != body.expected_basis:
            raise PlanError('context_changed')
        context = build_context(saved['snapshot'], owner_id=value.owner, catalog=catalog,
            catalog_revision=catalog_fingerprint(catalog), binding=binding,
            policy=POLICIES.get(binding.get('policy_version')))
        try:
            if context['status'] == 'ready':
                board = course_board(catalog, context, body.max_credits, track, path)
            else:
                board = reviewed_course_board(catalog, context, body.max_credits, track, path)
            courses = validate_plan_courses(board, body.course_codes, body.max_credits)
        except AcademicContextError as exc:
            raise PlanError(str(exc)) from None
        params = {**body.model_dump(exclude={'expected_basis', 'expected_version', 'course_codes'}),
                  'account': actor['account_id'], 'id': str(plan_id or uuid.uuid4()),
                  'program': catalog.program.program_id,
                  'total': sum(course['credits'] for course in courses),
                  'courses': json.dumps(courses), 'basis': json.dumps(basis)}
        if plan_id:
            row = conn.execute(text('''SELECT version FROM semester_plans
                WHERE id=:id AND account_id=:account FOR UPDATE'''), params).scalar_one_or_none()
            if row is None:
                raise AuthFailure('semester_plan_not_found', 404)
            if row != body.expected_version:
                raise PlanError('semester_plan_conflict')
            statement = '''UPDATE semester_plans SET title=:title,
                academic_year_start=:academic_year_start, semester=:semester,
                program_id=:program, selected_track_id=:selected_track_id,
                selected_graduation_path_id=:selected_graduation_path_id,
                max_credits=:max_credits, total_credits=:total,
                courses=CAST(:courses AS jsonb), basis=CAST(:basis AS jsonb),
                version=version+1, updated_at=now() WHERE id=:id AND account_id=:account RETURNING *'''
        else:
            count = conn.execute(text('SELECT count(*) FROM semester_plans WHERE account_id=:account'),
                                 params).scalar_one()
            if count >= 100:
                raise PlanError('semester_plan_limit')
            statement = '''INSERT INTO semester_plans
                (id,account_id,title,academic_year_start,semester,program_id,selected_track_id,
                 selected_graduation_path_id,max_credits,total_credits,courses,basis)
                VALUES(:id,:account,:title,:academic_year_start,:semester,:program,:selected_track_id,
                 :selected_graduation_path_id,:max_credits,:total,CAST(:courses AS jsonb),
                 CAST(:basis AS jsonb)) RETURNING *'''
        result = conn.execute(text(statement), params).mappings().one()
        repository.audit(conn, actor['account_id'], actor['account_id'], 'save_semester_plan')
        return {**serialize(result), 'needs_review': False, 'review_reasons': []}


def delete_plan(principal, plan_id, version):
    with repository.engine().begin() as conn:
        actor = repository.current(conn, principal['session_id'], lock=True)
        row = conn.execute(text('''SELECT version FROM semester_plans
            WHERE id=:id AND account_id=:account FOR UPDATE'''),
            {'id': str(plan_id), 'account': actor['account_id']}).scalar_one_or_none()
        if row is None:
            raise AuthFailure('semester_plan_not_found', 404)
        if row != version:
            raise PlanError('semester_plan_conflict')
        conn.execute(text('DELETE FROM semester_plans WHERE id=:id AND account_id=:account'),
                     {'id': str(plan_id), 'account': actor['account_id']})
        repository.audit(conn, actor['account_id'], actor['account_id'], 'delete_semester_plan')
