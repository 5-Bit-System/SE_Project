"""Natural course introductions resolve through scoped F3, without live LLM."""
import pytest

from app.hus.chat import chat
from app.hus.question_routing import question_intent
from app.schemas.hus import HUSQuestion
from app.services.hus_service import get_hus_answerer


@pytest.mark.parametrize('question', [
    'tôi muốn tìm hiểu về môn thị giác máy tính',
    'Tìm hiểu về học phần MAT3562',
    'Giới thiệu môn Thị giác máy tính',
    'Tổng quan về môn Thị giác máy tính',
    'Minh muon tim hieu ve mon Thi giac may tinh',
])
def test_course_overview_intent(question):
    assert question_intent(question) == ('f3', 'content')


@pytest.fixture(scope='module')
def answerer():
    return get_hus_answerer()


@pytest.mark.parametrize('question', [
    'tôi muốn tìm hiểu về môn thị giác máy tính',
    'Giới thiệu môn Thị giác máy tính',
    'Tìm hiểu về học phần MAT3562',
])
def test_scoped_course_overview_has_ai_evidence(answerer, question):
    answer = chat(HUSQuestion(question=question, major='data_science', version='QD3569-2023',
                              allow_generated_reference=True), answerer).hus_answer
    assert answer.status == 'answered'
    assert answer.dataset == 'f3' and answer.major == 'data_science'
    assert answer.citations
    assert all(c.display_label == 'kiến thức AI' for c in answer.citations)
    assert 'MAT3562' in answer.reply


def test_course_overview_still_needs_consent(answerer):
    answer = chat(HUSQuestion(question='tôi muốn tìm hiểu về môn thị giác máy tính',
                             major='data_science', version='QD3569-2023'), answerer).hus_answer
    assert answer.status == 'needs_clarification'
    assert not answer.citations


@pytest.mark.parametrize('question', [
    'Tìm hiểu về môn thiên văn ngoài vũ trụ',
    'Tôi không muốn tìm hiểu về môn MAT3562',
    'Tìm hiểu về môn MAT9999',
    'Tìm hiểu về môn MAT3562 thuộc ngành Toán tin',
])
def test_overview_never_invents_or_borrows_course(answerer, question):
    answer = chat(HUSQuestion(question=question, major='data_science', version='QD3569-2023',
                             allow_generated_reference=True), answerer).hus_answer
    assert answer.status in {'needs_clarification', 'no_information'}
    assert not answer.citations


@pytest.mark.parametrize('question,expected', [
    ('Tôi muốn tìm hiểu về ngành Khoa học dữ liệu', ('f1', 'introduction')),
    ('Tìm hiểu về môn MAT3562 có bao nhiêu tín chỉ?', ('f2', 'credits')),
    ('Tìm hiểu về môn MAT3562: tiên quyết là gì?', ('f2', 'prerequisites')),
    ('Tìm hiểu về môn MAT3562: mục tiêu học tập?', ('f3', 'objectives')),
    ('Tìm hiểu về môn MAT3562 thi cuối kỳ bao nhiêu phần trăm?', ('f3', 'official_assessment')),
    ('Tôi không muốn tìm hiểu về môn MAT3562', (None, None)),
])
def test_explicit_fields_and_negative_requests_keep_priority(question, expected):
    assert question_intent(question) == expected
