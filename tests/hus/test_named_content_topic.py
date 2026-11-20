"""Verified course-unit titles are topic selectors, not extra assessment requests."""
import pytest

from app.hus.answering import HUSAnswerer
from app.hus.chat import chat
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.fixture(autouse=True)
def llm_off(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'lexical')


@pytest.mark.parametrize('question', [
    'Nội dung MAT3370: Dự báo và kiểm tra mô hình?',
    'Xin trích mục Dự báo và kiểm tra mô hình trong phần nội dung AI của học phần MAT3370.',
    'Nội dung chủ đề “Dự báo và kiểm tra mô hình” của MAT3370?',
])
def test_existing_unit_title_selects_content_with_its_citation(answerer, question):
    answer = chat(HUSQuestion(major='mathematics', version='QD3565-2023',
        question=question, allow_generated_reference=True), answerer).hus_answer
    assert answer.status == 'answered', answer.reply
    assert answer.dataset == 'f3' and answer.citations
    assert all(c.metadata['field'] == 'content' and c.display_label == 'kiến thức AI'
               and c.metadata['course_code'] == 'MAT3370' for c in answer.citations)
    assert 'Dự báo và kiểm tra mô hình' in answer.reply


@pytest.mark.parametrize('question', [
    'Nội dung MAT3370: Dự báo và kiểm tra mô hình và gợi ý đánh giá?',
    'Nội dung MAT3370 và kiểm tra bằng hình thức nào?',
    'Nội dung MAT1204: Dự báo và kiểm tra mô hình?',
])
def test_extra_assessment_or_title_of_another_course_is_not_hidden(answerer, question):
    answer = chat(HUSQuestion(major='mathematics', version='QD3565-2023',
        question=question, allow_generated_reference=True), answerer).hus_answer
    assert answer.status != 'answered' and not answer.citations


def test_title_does_not_grant_f3_permission(answerer):
    answer = chat(HUSQuestion(major='mathematics', version='QD3565-2023',
        question='Nội dung MAT3370: Dự báo và kiểm tra mô hình?'), answerer).hus_answer
    assert answer.status == 'needs_clarification' and not answer.citations
