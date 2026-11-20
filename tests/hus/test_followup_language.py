"""Exposed A7 follow-up: bounded pilot/imperative/basis language, not holdout."""

from dataclasses import replace

import pytest

from app.hus.answer_support import supported_hits
from app.hus.answering import MAJOR_NAMES, HUSAnswerer
from app.hus.chat import chat
from app.hus.question_routing import question_intent, requested_course_fields
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion
from tests.hus.test_answer_support_gate import hit


@pytest.mark.parametrize('question', [
    'Giới thiệu ngành Khoa học dữ liệu được giao đào tạo thí điểm theo QĐ số 720?',
    'Gioi thieu nganh duoc giao dao tao thi diem theo QD so 720?',
    'Giới thiệu chương trình thí điểm của ngành?',
    'Tổng quan đề án triển khai thí điểm đào tạo của ngành?',
])
def test_pilot_program_is_not_an_exam_request(question):
    assert question_intent(question) == ('f1', 'introduction')
    assert 'suggested_assessment' not in requested_course_fields(question)


@pytest.mark.parametrize('question,field', [
    ('Đào tạo thí điểm; bài thi điểm bao nhiêu phần trăm?', 'official_assessment'),
    ('Chương trình thí điểm thi tự luận hay trắc nghiệm?', 'official_assessment'),
    ('Giới thiệu ngành đào tạo thí điểm; thi cuối kỳ chiếm 60%?', 'official_assessment'),
    ('Bài thi điểm bao nhiêu phần trăm?', 'official_assessment'),
    ('Gợi ý đánh giá môn học trong chương trình thí điểm?', 'suggested_assessment'),
])
def test_pilot_context_does_not_hide_a_real_assessment(question, field):
    assert question_intent(question) == ('f3', field)


def keep(question, *sources):
    return supported_hits(question, tuple(sources), aliases=MAJOR_NAMES, codes=set())


@pytest.mark.parametrize('prefix', ['Tìm hiểu', 'Xin tìm hiểu', 'Tôi muốn tìm hiểu', 'Nhờ bạn tìm hiểu'])
def test_learning_imperative_is_grammar_but_the_topic_still_needs_a_quote(prefix):
    source = hit('Vị trí và màu là các kênh thị giác.', field='content')
    assert keep(f'{prefix} nội dung về kênh thị giác.', source) == (source,)
    assert not keep(f'{prefix} nội dung về lượng tử.', source)


def test_learning_skill_is_not_an_imperative_and_boundaries_are_preserved():
    source = hit('Mục tiêu: phân tích kênh thị giác.', field='objectives')
    assert not keep('Mục tiêu về năng lực tìm hiểu kênh thị giác?', source)
    assert not keep('Tìm; hiểu nội dung về kênh thị giác.', source)
    actual = hit('Mục tiêu: năng lực tìm hiểu kênh thị giác.', field='objectives')
    assert keep('Mục tiêu về năng lực tìm hiểu kênh thị giác?', actual) == (actual,)


@pytest.mark.parametrize('phrase,scattered', [
    ('lượng tử', 'Dữ liệu định lượng được sắp theo thứ tự.'),
    ('đồ thị', 'Dùng đồ dùng để biểu diễn thị giác.'),
    ('ước lượng', 'Quy ước về đại lượng cần được nêu rõ.'),
])
def test_ambiguous_compounds_need_contiguous_body_words_not_individual_tokens(phrase, scattered):
    question = f'Tìm hiểu nội dung về {phrase}?'
    wrong = hit(scattered, field='content')
    right = hit(f'Nội dung giải thích {phrase}.', field='content')
    assert not keep(question, wrong)
    assert keep(question, right) == (right,)


def test_scientific_compound_cannot_be_assembled_across_passages_or_supplied_by_title():
    first = hit('Đại lượng.', field='content', start=0)
    second = hit('Các toán tử.', field='content', start=100)
    assert not keep('Tìm hiểu nội dung về lượng tử?', first, second)
    titled = replace(first, chunk=replace(first.chunk, metadata={**first.chunk.metadata, 'title': 'Lượng tử'}))
    assert not keep('Tìm hiểu nội dung về lượng tử?', titled)


@pytest.mark.parametrize('wording', [
    'Khả năng học tiếp dựa trên tư duy logic và mô hình hóa ra sao?',
    'Khả năng học lên dựa trên tư duy logic và mô hình hóa như thế nào?',
    'Cơ hội học cao hơn dựa trên tư duy logic và mô hình hóa?',
])
def test_further_study_basis_requires_subjects_and_explicit_basis_evidence(wording):
    source = hit('Tư duy logic và mô hình hóa là tiền đề để học tiếp.', field='further_study')
    assert keep(wording, source) == (source,)
    list_only = hit('Tư duy logic và mô hình hóa.', field='further_study')
    assert not keep(wording, list_only)
    wrong_subject = hit('Khả năng giao tiếp là tiền đề để học tiếp.', field='further_study')
    assert not keep(wording, wrong_subject)


@pytest.mark.parametrize('body', [
    'Tư duy logic và mô hình hóa không là tiền đề để học tiếp.',
    'Tư duy logic và mô hình hóa chưa là nền tảng để học tiếp.',
])
def test_negated_basis_does_not_support_a_positive_basis_request(body):
    source = hit(body, field='further_study')
    assert not keep('Khả năng học tiếp dựa trên tư duy logic và mô hình hóa?', source)


def test_basis_context_is_rendered_and_cannot_be_borrowed_from_another_scope():
    topic = hit('Tư duy logic và mô hình hóa.', field='further_study', start=10)
    basis = hit('Những kiến thức này là tiền đề để học tiếp.', field='further_study', start=100)
    question = 'Khả năng học tiếp dựa trên tư duy logic và mô hình hóa ra sao?'
    assert keep(question, basis, topic) == (topic, basis)
    for wrong in (hit('Những kiến thức này là tiền đề để học tiếp.', field='further_study', source='other'),
                  hit('Những kiến thức này là tiền đề để học tiếp.', field='further_study', edition='2008'),
                  hit('Những kiến thức này là tiền đề để học tiếp.', field='further_study', variant='talent'),
                  hit('Những kiến thức này là tiền đề để học tiếp.', field='further_study', review='needs_review')):
        assert not keep(question, topic, wrong)
    wrong_field = replace(basis, chunk=replace(basis.chunk, metadata={**basis.chunk.metadata, 'field': 'careers'}))
    assert not keep(question, topic, wrong_field)


@pytest.mark.parametrize('question', [
    'Khả năng học tiếp dựa trên thần giao cách cảm ra sao?',
    'Khả năng học tiếp dựa; trên tư duy logic và mô hình hóa?',
    'Khả năng học tiếp không dựa trên tư duy logic và mô hình hóa?',
    'Theo edition 2008, khả năng học tiếp dựa trên tư duy logic và mô hình hóa?',
    'Khả năng học tiếp dựa trên tư duy logic và mô hình hóa trong một năm?',
])
def test_basis_syntax_cannot_erase_unknown_subjects_negation_scope_or_duration(question):
    source = hit('Tư duy logic và mô hình hóa là tiền đề để học tiếp.', field='further_study')
    assert not keep(question, source)


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.mark.parametrize('major,version,question,anchor', [
    ('data_science', 'QD3569-2023', 'Giới thiệu ngành Khoa học dữ liệu được giao đào tạo thí điểm theo QĐ số 720?', '720'),
    ('data_science', 'QD3569-2023', 'Xin giới thiệu việc đào tạo thí điểm ngành Khoa học dữ liệu.', 'thí điểm'),
    ('data_science', 'QD3569-2023', 'Tìm hiểu nội dung AI MAT3383 về dữ liệu và kênh thị giác.', 'Dữ liệu và kênh thị giác'),
    ('data_science', 'QD3569-2023', 'Nhờ bạn tìm hiểu nội dung MAT3383 về kênh thị giác.', 'kênh thị giác'),
    ('mathematics', 'QD3565-2023', 'Khả năng học tiếp của ngành Toán học dựa trên tư duy logic và mô hình hóa ra sao?', 'tiền đề'),
    ('mathematics', 'QD3565-2023', 'Khả năng học cao hơn ngành Toán học dựa trên mô hình hóa?', 'mô hình hóa'),
])
def test_exposed_and_related_phrasing_requires_actual_immutable_evidence(answerer, major, version, question, anchor):
    answer = chat(HUSQuestion(question=question, major=major, version=version,
                              allow_generated_reference=True), answerer).hus_answer
    assert answer.status == 'answered', answer.reply
    assert answer.citations and any(anchor in citation.quote for citation in answer.citations)
    assert all(citation.quote in answer.reply for citation in answer.citations)
    if answer.dataset == 'f3':
        assert all(c.display_label == 'kiến thức AI' and c.open_url is None for c in answer.citations)


@pytest.mark.parametrize('major,version,question,consent', [
    ('data_science', 'QD3569-2023', 'Tìm hiểu nội dung MAT3383 về lượng tử.', True),
    ('data_science', 'QD3569-2023', 'Tìm hiểu nội dung MAT3383 về kênh thị giác.', False),
    ('data_science', 'QD3569-2023', 'Đào tạo thí điểm; MAT3383 thi cuối kỳ 70%?', True),
    ('mathematics', 'QD3565-2023', 'Khả năng học tiếp dựa trên du hành thời gian?', False),
])
def test_related_phrasing_keeps_unknown_topics_ai_consent_and_exam_guards(answerer, major, version, question, consent):
    answer = chat(HUSQuestion(question=question, major=major, version=version,
                              allow_generated_reference=consent), answerer).hus_answer
    assert answer.status != 'answered' and not answer.citations
