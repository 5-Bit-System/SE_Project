"""The discoverable menu must describe scoped, answerable questions, not test gold."""

import pytest
from fastapi.testclient import TestClient

from app.hus.demo import app
from app.services.hus_service import get_hus_answerer


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_catalog_requires_known_exact_scope_and_never_falls_back(client):
    assert client.get('/hus/questions').status_code == 422
    assert client.get('/hus/questions', params={'major': 'foreign', 'version': 'QD3569-2023'}).status_code == 422
    assert client.get('/hus/questions', params={'major': 'mathematics', 'version': 'QD3569-2023'}).status_code == 404


@pytest.mark.parametrize('major,version', [
    ('mathematics', 'QD3565-2023'), ('mathematics_informatics', 'QD3567-2023'),
    ('computer_science', 'QD3568-2023'), ('data_science', 'QD3569-2023'),
])
def test_catalog_covers_scoped_sources_and_courses_without_promoting_ai(client, major, version):
    response = client.get('/hus/questions', params={'major': major, 'version': version})
    assert response.status_code == 200, response.text
    assert response.headers['cache-control'] == 'no-store'
    value = response.json()
    assert value['major'] == major and value['version'] == version
    assert value['release_sha256'] == get_hus_answerer().data.release_identity['release_sha256']
    groups = {group['id']: group for group in value['groups']}
    assert set(groups) == {'f1', 'f2', 'f3', 'help'}
    entries = [item for group in value['groups'] for item in group['questions']]
    assert len({item['id'] for item in entries}) == len(entries)
    courses = get_hus_answerer().data.f2_courses(major=major, version=version)
    assert {item['request']['course_code'] for item in groups['f2']['questions']
            if 'course_code' in item['request']} == {c.course_code for c in courses}
    for item in entries:
        assert item['request']['major'] == major
        assert 'allow_generated_reference' not in item['request']
        assert item['requires_ai'] == (item in groups['f3']['questions'])
    assert not any(item['request'].get('field') == 'official_assessment' for item in entries)
    assert all(item['request']['version'] == version for name in ('f2', 'f3') for item in groups[name]['questions'])
    available_f1 = {(c.version, c.metadata.get('program_variant'), c.metadata['field'])
                    for c in get_hus_answerer().data.chunks('f1', major=major)}
    assert {(q['request']['version'], q['request'].get('program_variant'), q['request']['field'])
            for q in groups['f1']['questions']} == available_f1


def test_each_exposed_question_uses_real_answer_path_and_preserves_evidence(client):
    """Exhaustive menu smoke; this is a product contract, not a holdout metric."""
    for scope in client.get('/hus/config').json()['majors']:
        response = client.get('/hus/questions', params={'major': scope['id'], 'version': scope['version']})
        assert response.status_code == 200
        for group in response.json()['groups']:
            for item in group['questions']:
                payload = {**item['request'], 'allow_generated_reference': item['requires_ai']}
                response = client.post('/hus/chat', json=payload)
                assert response.status_code == 200, item
                value = response.json()
                if group['id'] == 'help':
                    assert value['mode'] == 'basic_chat' and value['hus_answer'] is None
                    continue
                answer = value['hus_answer']
                assert answer['status'] == 'answered', (item, answer['reply'])
                assert answer['dataset'] == group['id'] and answer['major'] == scope['id']
                assert answer['citations']
                assert all(c['review_status'] for c in answer['citations'])
                if item['requires_ai']:
                    assert all(c['display_label'] == 'kiến thức AI' and c['open_url'] is None
                               and c['content_origin'] == 'generated' for c in answer['citations'])
                else:
                    assert all(c['content_origin'] != 'generated' for c in answer['citations'])


def test_catalog_ai_questions_cannot_enable_their_own_consent(client):
    response = client.get('/hus/questions', params={'major': 'data_science', 'version': 'QD3569-2023'})
    assert response.status_code == 200
    ai = next(group for group in response.json()['groups'] if group['id'] == 'f3')['questions'][0]
    answer = client.post('/hus/chat', json=ai['request']).json()['hus_answer']
    assert answer['status'] == 'needs_clarification' and not answer['citations']


def test_catalog_data_error_is_sanitized(client, monkeypatch):
    from app.hus import demo
    from app.hus.rag_loader import RAGDataError

    def corrupt():
        raise RAGDataError('private/path')

    monkeypatch.setattr(demo, 'get_hus_answerer', corrupt)
    response = client.get('/hus/questions', params={'major': 'data_science', 'version': 'QD3569-2023'})
    assert response.status_code == 503 and 'private/path' not in response.text


def test_missing_or_conflicting_credits_and_hours_are_not_advertised():
    from dataclasses import replace
    from types import SimpleNamespace

    from app.hus.question_catalog import question_catalog

    original = get_hus_answerer().data.f2_courses(major='data_science', version='QD3569-2023')[0]
    for rows in [({'credits_in_source': None},),
                 ({'credits_in_source': 2}, {'credits_in_source': 3})]:
        course = replace(original, source_rows=rows, course_metadata={'values': {'hours': None}})
        data = SimpleNamespace(f2_courses=lambda **_: (course,), chunks=lambda *_, **__: (),
                               get_f2_program=lambda **_: None,
                               release_identity={})
        value = question_catalog(data, major='data_science', version='QD3569-2023')
        questions = next(g for g in value['groups'] if g['id'] == 'f2')['questions']
        assert {q['request']['field'] for q in questions} == {'name', 'prerequisites'}
        assert not next(g for g in value['groups'] if g['id'] == 'f3')['questions']
