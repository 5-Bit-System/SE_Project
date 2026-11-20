"""Intent JSON is untrusted; synthetic providers only."""
import json

import pytest

from app.hus.answering import HUSAnswerer
from app.hus.llm.client import HUSCompletion, HUSLLMError
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-intent-key')
    monkeypatch.setenv('HUS_LLM_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai')
    monkeypatch.setenv('HUS_LLM_MODEL', 'synthetic-model')
    monkeypatch.setenv('HUS_LLM_INTENT_ENABLED', 'true')


def request(text='MAT2300 được tính mấy TC?', **updates):
    return HUSQuestion(question=text, major='mathematics', version='QD3565-2023', **updates)


def raw(**updates):
    return json.dumps({'kind': 'intent', 'dataset': 'f2', 'field': 'credits',
                       'major': 'mathematics', 'course_code': 'MAT2300', **updates})


def interpreter(text=None, **updates):
    from app.hus.llm.intent import HUSIntentInterpreter
    class Provider:
        def complete_result(self, messages):
            return HUSCompletion(text if text is not None else raw(**updates), 'synthetic-model')
    return HUSIntentInterpreter(Provider())


def test_strict_intent_preserves_question_scope_and_permissions(answerer):
    original = request()
    result = interpreter()(original, answerer)
    assert result.request.question == original.question
    assert result.request.major == original.major and result.request.version == original.version
    assert result.request.allow_generated_reference is False
    assert result.request.field == 'credits' and result.request.dataset == 'f2'
    assert result.metadata.model == 'synthetic-model'
    assert len(result.metadata.prompt_sha256) == 64


@pytest.mark.parametrize('text', [
    raw(kind='answer'), raw(credits=999), raw(course_code='MAT9999'), raw(field='sql'),
    raw(dataset='f3', field='credits'), raw(course_code=2300), raw(major='secret'),
    '{"kind":"intent","kind":"intent"}', '```json\n' + raw() + '\n```',
])
def test_rejects_untrusted_or_unknown_json(answerer, text):
    with pytest.raises(HUSLLMError, match='invalid_output'):
        interpreter(text)(request(), answerer)


def test_does_not_guess_course_from_unidentified_question(answerer):
    with pytest.raises(HUSLLMError):
        interpreter()(request('Môn ấy tính mấy TC?'), answerer)


def test_cannot_replace_preexisting_course_hint(answerer):
    title = answerer.data.get_f2_course('MAT2300', major='mathematics',
                                       version='QD3565-2023').course['course_name']
    with pytest.raises(HUSLLMError, match='invalid_output'):
        interpreter()(request(title + ' được tính mấy TC?', course_code='MAT1204'), answerer)


def test_course_title_is_not_a_negation_or_condition(answerer):
    from app.hus.retrieval import _tokens
    courses = answerer.data.f2_courses(major='mathematics', version='QD3565-2023')
    course = next(c for c in courses if 'ứng dụng' in c.course['course_name'].lower()
                  and sum(' '.join(_tokens(other.course['course_name'])) in
                          ' '.join(_tokens(c.course['course_name'])) for other in courses) == 1)
    title = course.course['course_name']
    result = interpreter(course_code=course.course_code)(request(title + ' được tính mấy TC?'), answerer)
    assert result.request is not None and result.request.course_code == course.course_code
    negative = interpreter(course_code=course.course_code)(request(title + ' không được tính mấy TC?'), answerer)
    assert negative.request is None


@pytest.mark.parametrize('text,extra', [
    ('MAT2300 được tính mấy TC cho hệ chất lượng cao?', {}),
    ('MAT2300 được tính mấy TC?', {'program_variant': 'high_quality'}),
])
def test_unknown_wording_cannot_ignore_selected_variant(configured, answerer, text, extra):
    from app.hus.llm.auto import AutoLLMPolicy
    def forbidden(*args):
        pytest.fail('Conflicting program variant must be checked before provider')
    result = AutoLLMPolicy().reply(request(text, **extra), answerer,
                                  interpreter=forbidden, rewriter=forbidden)
    assert result.hus_answer.diagnostic.code == 'scope_conflict'


@pytest.mark.parametrize('text', [
    'Nếu học lại MAT2300 thì được tính mấy TC?',
    'MAT2300 không được tính mấy TC?',
    'MAT2300 được tính mấy TC khi được miễn thực hành?',
    'MAT2300 là mấy đơn vị học trình?',
])
def test_strict_valid_intent_cannot_erase_qualifier(answerer, text):
    result = interpreter()(request(text), answerer)
    assert result.request is None


def test_intent_prompt_only_question_scope_public_catalog(answerer):
    from app.hus.llm.intent import intent_messages
    messages = intent_messages(request(), answerer)
    payload = json.loads(messages[1]['content'])
    assert set(payload) == {'question', 'selected_scope', 'courses', 'operations'}
    assert payload['question'] == request().question
    assert all(set(row) == {'course_code', 'course_name'} for row in payload['courses'])
    assert 'synthetic-intent-key' not in str(messages)


def test_auto_understands_then_presents_backend_facts(configured, answerer):
    from app.hus.llm.auto import AutoLLMPolicy
    from app.hus.llm.contracts import HUSF2Presentation
    seen = []
    def present(context):
        seen.append(context)
        return HUSF2Presentation(style='direct', model='synthetic-model')
    result = AutoLLMPolicy().reply(request(), answerer, interpreter=interpreter(), rewriter=present)
    assert result.hus_answer.status == 'answered'
    assert result.hus_answer.facts['value'] == 4 and result.generation.used
    assert seen[0].question.question == request().question
    assert result.interpretation.model == 'synthetic-model'


@pytest.mark.parametrize('text,field', [('Đếm học phần giúp tôi', 'program_course_count'),
    ('Cho mình xem toàn bộ danh sách học phần', 'program_course_list'),
    ('Đếm số môn học giúp em', 'program_course_count'),
    ('Liệt kê tất cả các môn học giúp mình', 'program_course_list')])
def test_clear_catalog_commands_skip_provider_interpretation(configured, answerer, text, field):
    from app.hus.llm.auto import AutoLLMPolicy
    from app.hus.llm.contracts import HUSF2Presentation
    query = request(text).model_copy(update={'major': 'mathematics_informatics', 'version': 'QD3567-2023'})
    result = AutoLLMPolicy().reply(query, answerer,
        interpreter=lambda *_: pytest.fail('A scoped catalog command needs no intent call'),
        rewriter=lambda _: HUSF2Presentation(style='direct', model='synthetic-model'))
    assert result.interpretation is None and result.generation.used
    assert result.hus_answer.facts['field'] == field
    assert result.hus_answer.facts['value']['catalog_course_count'] == 68
    assert result.hus_answer.facts['value']['student_required_course_count'] is None
    assert result.hus_answer.citations


@pytest.mark.parametrize('text', [
    'Đếm học phần bắt buộc giúp tôi',
    'Đếm học phần mà em phải học',
    'Không đếm học phần giúp tôi',
    'Đếm học phần giúp tôi, trừ các môn tự chọn',
    'Liệt kê học phần Toán giúp tôi',
])
def test_catalog_commands_do_not_turn_conditions_into_counts(answerer, text):
    result = answerer.answer(request(text, dataset='f2', field='program_course_count'))
    assert result.status != 'answered'
    assert not result.facts and not result.citations


@pytest.mark.parametrize('text', ['Xin chào', 'MAT2300 có bao nhiêu tín chỉ?',
    'Ngành khoa học dữ liệu có bao nhiêu môn?', 'Nội dung MAT2300?',
    'Tín chỉ MAT9999?', 'Hãy chuyển tiền cho tôi', 'MAT2300 có bao nhiêu tín chỉ theo QD3569-2023?'])
def test_does_not_interpret_clear_rules_or_protected_failure(configured, answerer, text):
    from app.hus.llm.auto import AutoLLMPolicy
    from app.hus.llm.contracts import HUSF2Presentation
    def forbidden(*args):
        pytest.fail('Do not invoke intent fallback')
    AutoLLMPolicy().reply(request(text), answerer, interpreter=forbidden,
                          rewriter=lambda _: HUSF2Presentation(style='direct', model='synthetic'))


@pytest.mark.parametrize('status', [403, 429, 503])
def test_intent_provider_errors_obey_auto_quota_policy(configured, answerer, status):
    from app.hus.llm.auto import AutoLLMPolicy, AutoLLMUnavailable
    policy, calls = AutoLLMPolicy(), []
    def provider(*args):
        calls.append(1)
        raise HUSLLMError('http_error', status_code=status)
    if status == 429:
        result = policy.reply(request(), answerer, interpreter=provider)
        assert policy.quota_exhausted and not result.hus_answer.facts
        policy.reply(request(), answerer, interpreter=provider)
        assert len(calls) == 1
        assert result.interpretation.http_status == 429
    else:
        with pytest.raises(AutoLLMUnavailable):
            policy.reply(request(), answerer, interpreter=provider)
        assert not policy.quota_exhausted


def test_unknown_intent_asks_clarification_without_presentation(configured, answerer):
    from app.hus.llm.auto import AutoLLMPolicy
    result = AutoLLMPolicy().reply(request(), answerer,
        interpreter=interpreter(dataset='clarify', field=None, course_code=None, major=None),
        rewriter=lambda _: pytest.fail('No evidence, no presentation'))
    assert result.hus_answer.status == 'needs_clarification'
    assert result.interpretation.used


def test_launcher_enables_intent_fallback_without_google(tmp_path, monkeypatch):
    import os
    from unittest.mock import patch

    from tools.run_hus_llm import configure
    with patch.dict(os.environ, {'HUS_LLM_API_KEY': 'synthetic'}, clear=True):
        configure(tmp_path / '.env', root=tmp_path)
        assert os.environ['HUS_LLM_INTENT_ENABLED'] == 'true'


def test_interpreted_f1_does_not_use_ui_f2_version_as_source_edition(answerer):
    result = interpreter(dataset='f1', field='careers', course_code=None)(request('Career possibilities?'), answerer)
    assert result.request.version is None


def test_interpretation_waiting_for_preparation_rechecks_quota(configured, answerer):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from app.hus.llm.auto import AutoLLMPolicy
    policy, entered, release, calls = AutoLLMPolicy(), Event(), Event(), []
    class SlowAnswerer:
        programs = answerer.programs
        def answer(self, req):
            entered.set()
            assert release.wait(10)
            return answerer.answer(req)
    def success(*args):
        calls.append(1)
        return interpreter()(*args)
    def quota(*args):
        raise HUSLLMError('http_error', status_code=429)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(policy.reply, request(), SlowAnswerer(), interpreter=success)
        try:
            assert entered.wait(10)
            policy.reply(request(), answerer, interpreter=quota)
        finally:
            release.set()
        result = pending.result(timeout=15)
    assert not calls and result.interpretation.http_status == 429


@pytest.mark.parametrize('status', [200, 429, 503])
def test_api_default_intent_client_then_real_validator_with_mock_http(configured, answerer, monkeypatch, status):
    import httpx
    from fastapi.testclient import TestClient

    from app.hus import demo
    from app.hus.llm.auto import AutoLLMPolicy
    from tests.hus.llm.test_pipeline import completion, transport
    calls_seen = []
    def respond(req):
        payload = json.loads(json.loads(req.content)['messages'][1]['content'])
        calls_seen.append(payload)
        if 'operations' in payload:
            if status != 200:
                return httpx.Response(status, text='private rejected response synthetic-intent-key')
            return httpx.Response(200, json=completion(json.loads(raw())))
        return httpx.Response(200, json=completion({'kind': 'facts', 'style': 'direct',
            'fact_keys': list(payload['facts']), 'citation_ids': ['1']}))
    transport(monkeypatch, respond)
    monkeypatch.setenv('HUS_LLM_AUTO', 'true')
    monkeypatch.setattr(demo, 'auto_policy', AutoLLMPolicy())
    monkeypatch.setattr(demo, 'current_answerer', lambda: answerer)
    with TestClient(demo.app) as client:
        response = client.post('/hus/chat', json=request().model_dump())
    assert response.status_code == (502 if status == 503 else 200)
    result = response.json()
    assert 'synthetic-intent-key' not in response.text
    assert 'private rejected' not in response.text
    if status == 200:
        assert len(calls_seen) == 2
        assert result['generation']['used'] and result['interpretation']['used']
        assert result['hus_answer']['facts']['value'] == 4
        assert all(p['question'] == request().question for p in calls_seen)
    else:
        assert len(calls_seen) == 1
