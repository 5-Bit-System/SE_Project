"""Bundle validation uses synthetic courses and never opens prerequisites within a plan."""

import pytest

from app.academic_context import AcademicContextError
from app.services.course_status_service import course_board, validate_plan_courses
from tests.eligibility.test_course_status import context, curriculum  # noqa: F401


def test_valid_bundle_uses_server_credits_and_keeps_selected_courses_unpassed(curriculum):  # noqa: F811
    board = course_board(curriculum, context('A'))
    rows = validate_plan_courses(board, ['B', 'X'], 5)
    assert sum(row['credits'] for row in rows) == 5
    with pytest.raises(AcademicContextError, match='course_unavailable'):
        validate_plan_courses(board, ['B', 'C'], 20)


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


def test_paused_plan_cannot_be_saved_even_when_empty():
    with pytest.raises(AcademicContextError, match='not_ready'):
        validate_plan_courses({'status': 'partial', 'can_plan': False}, [], 20)
