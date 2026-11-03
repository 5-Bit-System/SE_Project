"""Validation must not become weaker after an import or edit."""
import pytest

from app.curriculum.import_service import validate_and_parse_csv
from app.curriculum.publication_gate import check_revision_validation, compute_payload_digest
from app.curriculum.rule_service import validate_full_revision_payload


@pytest.mark.parametrize('credits', [-3, 0, 21, 1.5, float('nan'), float('inf'), 'not-a-number', True])
def test_revalidate_rejects_invalid_credits(credits):
    result = validate_full_revision_payload({'courses': [{'code': 'A', 'name': 'A', 'credits': credits, 'prerequisites': []}]})
    assert result['valid'] is False


@pytest.mark.parametrize('courses', [[], [{'code': 'A', 'name': '', 'credits': 3}],
    [{'code': 'A', 'name': 'A', 'credits': 3, 'prerequisites': ['MISSING']}],
    [{'code': 'A', 'name': 'A', 'credits': 3, 'prerequisites': [[]]}]])
def test_revalidate_rejects_incomplete_courses(courses):
    assert not validate_full_revision_payload({'courses': courses})['valid']


def test_source_digest_cannot_replace_payload_validation():
    revision = {'payload': {'courses': []}, 'source_digest': 'old-source',
                'validation_summary': {'valid': True, 'digest': 'old-source', 'errors': []}}
    assert check_revision_validation(revision)[0] is False


def test_forged_successful_summary_does_not_skip_content_validation():
    payload = {'courses': [{'code': 'A', 'name': 'A', 'credits': -3}]}
    revision = {'payload': payload, 'validation_summary': {'valid': True, 'errors': [], 'payload_digest': compute_payload_digest(payload)}}
    assert check_revision_validation(revision)[0] is False


@pytest.mark.parametrize('credits', ['nan', 'inf', '-3'])
def test_csv_and_revalidation_agree(credits):
    parsed = validate_and_parse_csv(f'code,name,credits\nA,Course,{credits}\n', 'test', 'test')
    assert not parsed['valid']
    assert not validate_full_revision_payload({'courses': parsed['courses']})['valid']
