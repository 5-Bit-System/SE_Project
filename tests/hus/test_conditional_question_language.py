"""Exposed natural20 failures and new paraphrases are dev regressions, not scores."""
import unicodedata

import pytest

from app.hus.answering import HUSAnswerer
from app.hus.chat import chat
from app.hus.question_routing import question_intent, requested_course_fields, requested_text
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion
from tests.hus.test_answer_support_gate import hit, keep


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'lexical')


@pytest.mark.parametrize('text,expected', [
    ('Tốt nghiệp Toán học thì có thể làm việc ở những đâu?', ('f1', 'careers')),
    ('Học xong ngành Toán tin thì làm việc ở đâu?', ('f1', 'careers')),
    ('Cử nhân KHDL có thể làm việc trong lĩnh vực nào?', ('f1', 'careers')),
    ('Muốn học Lập trình hướng đối tượng thì phải hoàn thành môn nào trước?', ('f2', 'prerequisites')),
    ('Để học MAT1202 cần hoàn thành học phần nào trước?', ('f2', 'prerequisites')),
    ('Trước khi học MAT1202, em phải học những môn nào?', ('f2', 'prerequisites')),
    ('Tôi muốn biết trong môn Đại số tuyến tính 1 sẽ gặp các khái niệm gì?', ('f3', 'content')),
    ('Trong học phần MAT2300 sẽ học những khái niệm nào?', ('f3', 'content')),
    ('Giải thích khái niệm không gian vector trong MAT2300.', ('f3', 'content')),
    ('Nếu tính mỗi mã học phần một lần thì ngành Toán học có bao nhiêu môn trong danh mục?',
     ('f2', 'program_course_count')),
])
def test_common_requests_route_without_menu(text, expected):
    assert question_intent(text) == expected


def test_decomposed_unicode_particle_is_not_exam():
    text = unicodedata.normalize('NFD', 'Tốt nghiệp Toán học thì làm việc ở đâu?')
    assert question_intent(text) == ('f1', 'careers')


@pytest.mark.parametrize('text', [
    'MAT2300 thi như thế nào?', 'MAT2300 thi gì?', 'MAT2300 thi gi?',
    'Nếu học MAT2300 thì thi như thế nào?',
    'Neu hoc MAT2300 thi thi nhu the nao?',
])
def test_true_exams_are_not_erased(text):
    assert question_intent(text) == ('f3', 'suggested_assessment')
    assert 'suggested_assessment' in requested_course_fields(text)


@pytest.mark.parametrize('text', [
    'Nếu học MAT2300 thì thi cuối kỳ chiếm bao nhiêu phần trăm?',
    'MAT2300 thi cuối kỳ 70% đúng không?',
])
def test_official_exam_requests_remain_unavailable(text, answerer):
    assert question_intent(text) == ('f3', 'official_assessment')
    result = chat(HUSQuestion(question=text, major='mathematics', version='QD3565-2023',
                             allow_generated_reference=True), answerer).hus_answer
    assert result.status != 'answered' and not result.citations


def test_conditional_and_negation_words_are_retained():
    text = requested_text('Nếu chưa hoàn thành MAT2300 thì không được học MAT2400?')
    assert 'neu chua hoan thanh mat2300' in text
    assert 'khong duoc hoc mat2400' in text


def test_generic_careers_syntax_keeps_specific_requirements():
    source = hit('Cơ hội nghề nghiệp gồm giảng dạy và nghiên cứu.')
    assert keep('Tốt nghiệp Toán học thì có thể làm việc ở những đâu?', source) == (source,)
    assert not keep('Tốt nghiệp Toán học thì làm việc về vật lý lượng tử ở đâu?', source)
    assert not keep('Tốt nghiệp Toán học thì làm việc ở công ty hàng không?', source)


@pytest.mark.parametrize('text', [
    'Nếu không đủ điều kiện thì có thể học tiếp sau đại học?',
    'Nếu chưa đủ điều kiện thì có thể học tiếp sau đại học?',
])
def test_conditional_negation_cannot_borrow_positive_eligibility(text):
    source = hit('Nếu đủ điều kiện thì có thể học tiếp sau đại học.', field='further_study')
    assert not keep(text, source)


@pytest.mark.parametrize('condition', ['không đủ điều kiện', 'chưa đủ điều kiện'])
def test_positive_condition_cannot_borrow_negative_source(condition):
    source = hit('Nếu ' + condition + ' thì có thể học tiếp sau đại học.', field='further_study')
    assert not keep('Nếu đủ điều kiện thì có thể học tiếp sau đại học?', source)


def test_supported_condition_remains_available_and_specific():
    source = hit('Nếu đủ điều kiện thì có thể học tiếp sau đại học.', field='further_study')
    assert keep('Nếu đủ điều kiện thì có thể học tiếp sau đại học?', source) == (source,)
    assert not keep('Nếu đủ điều kiện tiếng Anh thì có thể học tiếp sau đại học?', source)


@pytest.mark.parametrize('tail', ['khi chưa đủ điều kiện', 'mà chưa đủ điều kiện',
                                'nếu chưa đạt tiếng Anh', 'mà không đủ điều kiện'])
def test_want_to_study_wrapper_cannot_hide_factual_conditions(tail):
    source = hit('Nếu đủ điều kiện thì có thể học tiếp sau đại học.', field='further_study')
    assert not keep('Nếu muốn học tiếp ' + tail + ' thì có thể học tiếp sau đại học?', source)


def test_pure_study_desire_is_request_context():
    source = hit('Sinh viên có thể học tiếp sau đại học.', field='further_study')
    assert keep('Nếu muốn học tiếp sau Toán học thì có thể học tiếp sau đại học?', source) == (source,)


def test_concept_grammar_is_only_neutral_for_course_content():
    source = hit('Ngành đào tạo trình độ đại học.', field='introduction')
    assert not keep('Trong ngành sẽ gặp các khái niệm gì?', source)


@pytest.mark.parametrize('text', [
    'Nếu mỗi mã học phần được tính một lần mà chỉ lấy môn bắt buộc thì ngành Toán học có bao nhiêu môn?',
    'Nếu không tính môn tự chọn thì ngành Toán học có bao nhiêu môn?',
    'Nếu tính mỗi mã học phần một lần thì ngành Toán học có bao nhiêu môn bắt buộc?',
])
def test_counting_wrapper_never_removes_required_or_negative_filter(answerer, text):
    result = chat(HUSQuestion(question=text, major='mathematics', version='QD3565-2023'), answerer).hus_answer
    assert result.status != 'answered' and not result.facts


@pytest.mark.parametrize('text', [
    'Ngành Toán học đào tạo người học theo định hướng nào?',
    'Bạn mô tả ngắn gọn ngành Khoa học dữ liệu đang học những lĩnh vực gì được không?',
    'Ngành Toán tin học những môn gì?',
])
def test_broad_major_wording_asks_which_information(answerer, text):
    major = 'data_science' if 'dữ liệu' in text else ('mathematics_informatics' if 'Toán tin' in text else 'mathematics')
    version = {'mathematics': 'QD3565-2023', 'mathematics_informatics': 'QD3567-2023',
               'data_science': 'QD3569-2023'}[major]
    result = chat(HUSQuestion(question=text, major=major, version=version), answerer).hus_answer
    assert result.status == 'needs_clarification'
    assert result.diagnostic.code == 'clarification_required'
    assert not result.citations
    assert 'ngành' in result.reply and 'môn' in result.reply


@pytest.mark.parametrize('text,expected', [
    ('Mục tiêu môn Toán rời rạc?', ('f3', 'objectives')),
    ('Nội dung chương trình ngành KHDL?', ('f1', 'introduction')),
    ('Ngành Toán học có định hướng nghề nghiệp nào?', ('f1', 'careers')),
    ('Mục tiêu MAT2300 là phân biệt các khái niệm cơ bản?', ('f3', 'objectives')),
    ('Mục tiêu chuyên môn của ngành Toán học là gì?', ('f1', 'objectives')),
    ('Ngành Toán học đào tạo năng lực chuyên môn nào?', ('f1', 'objectives')),
    ('Mục tiêu của bộ môn Toán học?', ('f1', 'objectives')),
    ('Mục tiêu đào tạo liên môn của ngành Toán học?', ('f1', 'objectives')),
])
def test_course_vs_major_and_explicit_fields_keep_priority(text, expected):
    assert question_intent(text) == expected


def test_prerequisite_request_uses_f2_without_ai_permission(answerer):
    question = 'Muốn học Lập trình hướng đối tượng thì phải hoàn thành môn nào trước?'
    result = chat(HUSQuestion(question=question, major='mathematics_informatics',
                             version='QD3567-2023'), answerer).hus_answer
    course = answerer.data.get_f2_course('MAT1202', major='mathematics_informatics', version='QD3567-2023')
    assert result.status == 'answered' and result.dataset == 'f2'
    assert result.facts['course_code'] == 'MAT1202'
    assert result.facts['value'] == [row.get('prerequisite_source_text') for row in course.source_rows]
    assert result.citations and all(c.dataset == 'f2' for c in result.citations)


def test_careers_question_uses_actual_major_sources(answerer):
    text = 'Tốt nghiệp Toán học thì có thể làm việc ở những đâu?'
    req = HUSQuestion(question=text, major='mathematics', version='QD3565-2023')
    result = chat(req, answerer).hus_answer
    assert result.status == 'answered' and result.dataset == 'f1'
    assert all(c.metadata['field'] == 'careers' for c in result.citations)
    assert result.version is None  # UI program edition is not an F1 source edition.


def test_student_work_question_keeps_real_career_sources(answerer):
    request = HUSQuestion(question='Sau khi tốt nghiệp ngành Toán tin, em có thể làm việc ở những đâu?',
                          major='mathematics_informatics', version='QD3567-2023')
    result = chat(request, answerer).hus_answer
    baseline = chat(request.model_copy(update={
        'question': 'Sau khi tốt nghiệp ngành Toán tin, có thể làm việc ở những đâu?'}), answerer).hus_answer
    assert result.status == 'answered' and result.dataset == 'f1'
    assert result.citations == baseline.citations
    assert all(source.metadata['field'] == 'careers' for source in result.citations)


@pytest.mark.parametrize('text,dataset,status,consent', [
    ('Tốt nghiệp Toán học thì có thể làm việc ở những đâu?', 'f1', 'answered', False),
    ('Để học MAT2300 cần hoàn thành học phần nào trước?', 'f2', 'answered', False),
    ('Trong môn MAT2300 sẽ gặp các khái niệm gì?', 'f3', 'answered', True),
    ('Ngành Toán học đào tạo người học theo định hướng nào?', 'f1', 'needs_clarification', False),
])
def test_public_chat_api_resolves_natural_questions_offline(answerer, monkeypatch, text, dataset, status, consent):
    from fastapi.testclient import TestClient

    from app.hus import demo
    monkeypatch.setenv('HUS_LLM_AUTO', 'false')
    monkeypatch.setattr(demo, 'current_answerer', lambda: answerer)
    with TestClient(demo.app) as client:
        response = client.post('/hus/chat', json={'question': text, 'major': 'mathematics',
            'version': 'QD3565-2023', 'allow_generated_reference': consent})
    assert response.status_code == 200
    answer = response.json()['hus_answer']
    assert answer['dataset'] == dataset and answer['status'] == status
    assert 'generation' not in response.json() and 'interpretation' not in response.json()


def test_concept_request_uses_generated_content_only_with_consent(answerer):
    text = 'Tôi muốn biết trong môn Đại số tuyến tính 1 sẽ gặp các khái niệm gì?'
    req = HUSQuestion(question=text, major='mathematics', version='QD3565-2023')
    denied = chat(req, answerer).hus_answer
    assert denied.diagnostic.code == 'permission_required' and not denied.citations
    allowed = chat(req.model_copy(update={'allow_generated_reference': True}), answerer).hus_answer
    assert allowed.status == 'answered' and allowed.dataset == 'f3'
    assert all(c.metadata['course_code'] == 'MAT2300' and c.metadata['field'] == 'content'
               and c.display_label == 'kiến thức AI' for c in allowed.citations)


def test_explicit_unique_code_count_grammar_is_not_a_student_condition(answerer):
    text = 'Nếu tính mỗi mã học phần một lần thì ngành Toán học có bao nhiêu môn trong danh mục?'
    answer = chat(HUSQuestion(question=text, major='mathematics', version='QD3565-2023'), answerer).hus_answer
    assert answer.status == 'answered' and answer.facts['value']['catalog_course_count'] == 90
