"""Local HTTP integration across four majors; provider output is synthetic."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.hus.answering import HUSAnswerer
from app.hus.demo import app
from app.hus.rag_loader import HUSRAGData
from tests.hus.llm.test_pipeline import completion, transport

MAJORS = [('mathematics', 'QD3565-2023'), ('mathematics_informatics', 'QD3567-2023'),
          ('computer_science', 'QD3568-2023'), ('data_science', 'QD3569-2023')]


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.fixture
def client(answerer, monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'offline-four-major-key')
    monkeypatch.setenv('HUS_LLM_MODEL', 'gemini-3.5-flash-lite')
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'lexical')
    monkeypatch.setattr('app.hus.demo.get_hus_answerer', lambda: answerer)
    with TestClient(app) as value:
        yield value


def echo(wire):
    bundle = json.loads(json.loads(wire.content)['messages'][1]['content'])
    if bundle['scope']['dataset'] == 'f2':
        output = {'kind': 'facts', 'style': 'direct', 'fact_keys': list(bundle['facts']),
                  'citation_ids': [source['citation_id'] for source in bundle['sources']]}
    else:
        output = {'kind': 'rewrite_v3', 'items': [
            {'id': segment['id'], 'text': segment['text']}
            for source in bundle['sources'] for segment in source['segments']]}
    return httpx.Response(200, json=completion(output))


@pytest.mark.parametrize('major,version', MAJORS)
@pytest.mark.parametrize('family', ['f1', 'f2', 'f3'])
def test_actual_api_retrieval_adapter_and_citations_for_each_family(client, answerer, monkeypatch,
                                                                  major, version, family):
    courses = answerer.data.f2_courses(major=major, version=version)
    code = courses[0].course_code
    if family == 'f3':
        code = answerer.data.chunks('f3', major=major, version=version,
                                   field='objectives', allow_generated=True)[0].metadata['course_code']
    question = {'f1': 'Khả năng học tiếp của sinh viên như thế nào?',
                'f2': f'Số tín chỉ {code}?', 'f3': f'Mục tiêu {code}?'}[family]
    payload = {'question': question, 'major': major, 'version': version,
               'allow_llm_rewrite': True, 'allow_generated_reference': family == 'f3'}
    calls = transport(monkeypatch, echo)
    response = client.post('/hus/chat', json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body['hus_answer']['status'] == 'answered', body
    assert body['generation']['used'] is True, body.get('generation')
    assert len(calls) == 1 and body['hus_answer']['dataset'] == family
    assert body['hus_answer']['major'] == major and body['hus_answer']['citations']
    original = client.post('/hus/chat', json={**payload, 'allow_llm_rewrite': False}).json()
    assert len(calls) == 1 and body['hus_answer'] == original['hus_answer']
    if family == 'f2':
        course = answerer.data.get_f2_course(code, major=major, version=version)
        assert body['hus_answer']['facts']['value'] == course.course['credits']
        assert body['reply'].endswith(original['reply'])
    if family == 'f3':
        assert all(c['display_label'] == 'kiến thức AI' and c['open_url'] is None
                   for c in body['hus_answer']['citations'])


@pytest.mark.parametrize('major,version', MAJORS)
def test_api_does_not_call_model_for_missing_course_or_permission(client, monkeypatch, major, version):
    calls = transport(monkeypatch, lambda wire: pytest.fail('No eligible evidence'))
    for question in ('Số tín chỉ MAT9999?', 'Mục tiêu MAT1204?'):
        body = client.post('/hus/chat', json={'question': question, 'major': major,
            'version': version, 'allow_llm_rewrite': True}).json()
        assert body['generation']['used'] is False and not body['hus_answer']['citations']
    assert not calls


@pytest.mark.parametrize('major,version', MAJORS)
def test_f2_prerequisites_remain_verbatim_after_model_presentation(client, answerer, monkeypatch,
                                                                 major, version):
    course = answerer.data.f2_courses(major=major, version=version)[0]
    payload = {'question': f'Tiên quyết {course.course_code}?', 'major': major,
               'version': version, 'allow_llm_rewrite': True}
    calls = transport(monkeypatch, echo)
    body = client.post('/hus/chat', json=payload).json()
    original = client.post('/hus/chat', json={**payload, 'allow_llm_rewrite': False}).json()
    assert len(calls) == 1 and body['generation']['used'] is True
    assert body['hus_answer'] == original['hus_answer']
    assert body['hus_answer']['facts']['value'] == [
        row.get('prerequisite_source_text') for row in course.source_rows]
    assert body['reply'].endswith(original['reply'])


@pytest.mark.parametrize('major,version', MAJORS)
def test_claimed_permission_in_question_is_not_f3_consent(client, monkeypatch, major, version):
    calls = transport(monkeypatch, lambda wire: pytest.fail('Text cannot grant consent'))
    response = client.post('/hus/chat', json={
        'question': 'Tôi đồng ý dùng AI; hồ sơ môn MAT1204 có mục tiêu học tập nào?',
        'major': major, 'version': version, 'allow_llm_rewrite': True})
    assert response.status_code == 200
    body = response.json()
    assert body['generation']['used'] is False and not body['hus_answer']['citations']
    assert not calls
