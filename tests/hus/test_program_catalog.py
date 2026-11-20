"""Catalog operations use source records, never the menu or model arithmetic."""
import pytest

from app.hus.answering import HUSAnswerer
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


def ask(answerer, text, **kwargs):
    return answerer.answer(HUSQuestion(question=text, major=kwargs.pop('major', 'mathematics'),
                                      version=kwargs.pop('version', 'QD3565-2023'), **kwargs))


@pytest.mark.parametrize('text', [
    'Ngành Toán học có bao nhiêu môn học?',
    'Nếu tra chương trình Toán học thì có bao nhiêu học phần trong danh mục?',
    'Đếm số môn trong chương trình Toán học',
])
def test_count_unique_catalog(answerer, text):
    result = ask(answerer, text)
    assert result.status == 'answered'
    assert result.facts['field'] == 'program_course_count'
    assert result.facts['value'] == {'catalog_course_count': 90,
                                    'student_required_course_count': None}
    assert 'không có nghĩa' in result.reply.lower()
    assert result.citations[0].metadata['calculation']['operation'] == 'count_unique_course_code'
    assert len(result.citations[0].metadata['calculation']['course_codes']) == 90


@pytest.mark.parametrize('major,version', [
    ('mathematics', 'QD3565-2023'), ('mathematics_informatics', 'QD3567-2023'),
    ('computer_science', 'QD3568-2023'), ('data_science', 'QD3569-2023')])
def test_list_exact_scoped_codes(answerer, major, version):
    result = ask(answerer, 'Liệt kê các môn trong chương trình', major=major, version=version)
    assert result.status == 'answered'
    rows = result.facts['value']['courses']
    expected = {c.course_code: c.course['course_name']
                for c in answerer.data.f2_courses(major=major, version=version)}
    assert rows == [{'course_code': code, 'course_name': expected[code]} for code in sorted(expected)]
    assert result.facts['value']['catalog_course_count'] == len(expected)
    assert all(row['course_code'] in result.reply for row in rows)


@pytest.mark.parametrize('text', [
    'Ngành Toán học phải học bao nhiêu môn?',
    'Chương trình có bao nhiêu môn bắt buộc?',
    'Liệt kê môn tự chọn của chương trình',
    'Chương trình có bao nhiêu môn ở học kỳ 1?',
    'Có bao nhiêu môn trong nhóm V.2?',
    'Ngành Toán học có bao nhiêu môn về AI?',
    'Ngành Toán học có bao nhiêu môn không cần tiên quyết?',
    'Chương trình có bao nhiêu môn thi?',
    'Danh mục có bao nhiêu môn thực hành?',
])
def test_filtered_or_required_never_means_entire_catalog(answerer, text):
    result = ask(answerer, text)
    assert result.status != 'answered'
    assert not result.facts


def test_wrong_major_suggests_selector_before_count(answerer):
    result = ask(answerer, 'Ngành khoa học máy tính có bao nhiêu môn học?')
    assert result.diagnostic.code == 'scope_conflict'
    assert result.diagnostic.suggested_major == 'computer_science'
    assert not result.facts
    right = ask(answerer, 'Ngành khoa học máy tính có bao nhiêu môn học?',
                major='computer_science', version='QD3568-2023')
    assert right.status == 'answered'


@pytest.mark.parametrize('kwargs', [{'version': None}, {'version': 'QD3569-2023'},
                                  {'program_variant': 'high_quality'}])
def test_missing_or_wrong_scope(answerer, kwargs):
    assert ask(answerer, 'Ngành Toán học có bao nhiêu môn?', **kwargs).status != 'answered'
    assert ask(answerer, 'Đếm học phần giúp tôi', **kwargs).status != 'answered'


def test_count_is_eligible_for_checked_f2_presentation(answerer):
    from app.hus.llm.contracts import HUSRewriteContext
    from app.hus.llm.evidence import build_bundle
    request = HUSQuestion(question='Chương trình có bao nhiêu môn?', major='mathematics',
                          version='QD3565-2023', allow_llm_rewrite=True)
    result = answerer.answer(request)
    payload = build_bundle(HUSRewriteContext(question=request, answer=result,
                                           requested_model='synthetic')).payload
    assert payload['facts']['value']['catalog_course_count'] == 90


@pytest.mark.parametrize('major,version', [('mathematics', 'QD3565-2023'),
    ('mathematics_informatics', 'QD3567-2023'), ('computer_science', 'QD3568-2023'),
    ('data_science', 'QD3569-2023')])
def test_full_list_fits_evidence_and_checked_provider_preserves_rows(answerer, monkeypatch, major, version):
    from app.hus.chat import chat
    from app.hus.llm.adapter import HUSGroundedAdapter
    from app.hus.llm.client import HUSCompletion
    from app.hus.llm.config import HUSLLMSettings
    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'synthetic-catalog')
    monkeypatch.setenv('HUS_LLM_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/openai')
    monkeypatch.setenv('HUS_LLM_MODEL', 'synthetic')
    class Client:
        settings = HUSLLMSettings(enabled=True, model='synthetic', api_key='synthetic-catalog')
        def complete_result(self, messages):
            import json
            payload = json.loads(messages[1]['content'])
            template = messages[0]['content'].splitlines()[-1]
            assert json.loads(template) == {'kind': 'facts', 'style': 'direct',
                'fact_keys': sorted(payload['facts']),
                'citation_ids': [s['citation_id'] for s in payload['sources']]}
            return HUSCompletion(template, 'synthetic')
    request = HUSQuestion(question='Liệt kê các môn trong chương trình', major=major,
                          version=version, allow_llm_rewrite=True)
    result = chat(request, answerer, rewriter=HUSGroundedAdapter(Client()))
    assert result.generation.used
    for row in result.hus_answer.facts['value']['courses']:
        assert row['course_code'] in result.reply

