"""Bundle validation uses synthetic courses and never opens prerequisites within a plan."""

import pytest

from app.academic_context import AcademicContextError
from app.models import Course
from app.services.course_status_service import (
    course_board,
    reviewed_course_board,
    validate_plan_courses,
)
from tests.eligibility.test_course_status import context, curriculum, pending_context  # noqa: F401


def test_valid_bundle_uses_server_credits_and_keeps_selected_courses_unpassed(curriculum):  # noqa: F811
    board = course_board(curriculum, context('A'))
    rows = validate_plan_courses(board, ['B', 'X'], 5)
    assert sum(row['credits'] for row in rows) == 5
    for orphan in (['C'], ['C', 'X']):
        with pytest.raises(AcademicContextError, match='course_unavailable'):
            validate_plan_courses(board, orphan, 20)
    co_rows = validate_plan_courses(board, ['C', 'B'], 20)
    assert [row['code'] for row in co_rows] == ['C', 'B']
    assert sum(row['credits'] for row in co_rows) == 6
    assert [row['code'] for row in board['courses']['completed']] == ['A']


@pytest.mark.parametrize(('codes', 'budget', 'error'), [
    (['B', 'B'], 20, 'duplicate_course'),
    (['A'], 20, 'course_unavailable'),
    (['D'], 20, 'course_unavailable'),
    (['FOREIGN'], 20, 'course_unavailable'),
    (['B', 'X'], 4, 'budget_exceeded'),
    (['E1', 'E2'], 20, 'group_full'),
])
def test_invalid_bundles_rejected(curriculum, codes, budget, error):  # noqa: F811
    with pytest.raises(AcademicContextError, match=error):
        validate_plan_courses(course_board(curriculum, context('A')), codes, budget)


def test_unverified_catalog_courses_cannot_be_saved_to_a_plan(curriculum):  # noqa: F811
    curriculum.program.catalog_status = 'draft_unverified'
    board = course_board(curriculum, context('A'))

    with pytest.raises(AcademicContextError, match='course_unavailable'):
        validate_plan_courses(board, ['B'], 20)


def test_unverified_course_source_cannot_be_saved_to_a_plan(curriculum):  # noqa: F811
    next(course for course in curriculum.courses if course.code == 'E1').source_status = 'draft_unverified'
    board = course_board(curriculum, context('A'))

    with pytest.raises(AcademicContextError, match='course_unavailable'):
        validate_plan_courses(board, ['E1'], 20)


def test_paused_plan_cannot_be_saved_even_when_empty():
    with pytest.raises(AcademicContextError, match='not_ready'):
        validate_plan_courses({'status': 'partial', 'can_plan': False}, [], 20)


def test_reviewed_defaults_can_be_saved_without_satisfying_downstream_courses(curriculum):  # noqa: F811
    curriculum.courses.append(Course(
        code='FOLLOWUP', name='Synthetic follow-up', credits=3, block='major',
        prerequisites=[['E1']], prerequisite_status='verified', source_status='verified',
    ))
    pending = pending_context()
    board = reviewed_course_board(curriculum, pending)
    rows = validate_plan_courses(board, ['E1', 'X'], 5)
    assert [row['code'] for row in rows] == ['E1', 'X']
    assert sum(row['credits'] for row in rows) == 5
    assert [row['code'] for row in board['courses']['completed']] == ['A']
    assert board['progress']['total']['earned_credits'] == 3
    with pytest.raises(AcademicContextError, match='course_unavailable'):
        validate_plan_courses(board, ['E1', 'FOLLOWUP'], 20)
    assert next(row for row in board['courses']['blocked']
                if row['code'] == 'FOLLOWUP')['reasons'][0]['missing_prerequisites'] == [['E1']]
    assert next(row for row in pending['outcomes'] if row['code'] == 'E1')['state'] == 'unresolved'


@pytest.mark.parametrize('gate', ['selection', 'outside', 'program'])
@pytest.mark.parametrize('codes', [[], ['E1', 'X']])
def test_defaults_cannot_be_saved_across_global_planning_gates(curriculum, gate, codes):  # noqa: F811
    if gate == 'program':
        curriculum.program.planning_blockers = ['synthetic-rule-conflict']
    board = reviewed_course_board(
        curriculum, pending_context(outside=gate == 'outside'),
        selection_blockers=['graduation_selection_required'] if gate == 'selection' else None,
    )
    assert {'E1', 'X'} <= {row['code'] for row in board['courses']['eligible']}
    with pytest.raises(AcademicContextError, match='not_ready'):
        validate_plan_courses(board, codes, 20)


def test_khmtt_co_enrolled_plan_validates_and_rejects_orphan():
    import json

    from app.config import PROJECT_ROOT
    from app.services.course_status_service import course_board_display
    from database.hus_db.catalog_builder import build_catalogs

    bundle = json.loads((PROJECT_ROOT / 'database/data/hus_source.json').read_text(encoding='utf-8'))
    khmtt = next(c for c in build_catalogs(bundle) if c.program.program_id == 'khmtt_7480113qtd_2022')
    req_minus_three = [
        c.code
        for c in khmtt.courses
        if c.requirement_type == 'required'
        and c.counted_in_total
        and c.code not in {'MAT3374', 'MAT1207', 'MAT3373E'}
    ]
    passed_107 = [
        *req_minus_three,
        'FLF1107',
        'HUS1021',
        'HUS1022',
        'MAT1208',
        'MAT3519',
        'MAT2034',
        'MAT3148',
    ]
    raw_board = course_board(khmtt, context(*passed_107), max_credits=20, selected_graduation_path_id='V.3.1')
    display_board = course_board_display(raw_board)

    # Dependent MAT1207 before prerequisite MAT3374 succeeds on both raw board (used by save_plan) and display view.
    for target in (raw_board, display_board):
        saved = validate_plan_courses(
            target, ['MAT1207', 'MAT3374', 'MAT3373E', 'MAT3538', 'MAT3561E'], 20
        )
        assert sum(row['credits'] for row in saved) == 15
        with pytest.raises(AcademicContextError, match='semester_plan_course_unavailable'):
            validate_plan_courses(target, ['MAT1207', 'MAT3373E'], 20)
