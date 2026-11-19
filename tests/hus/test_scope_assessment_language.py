"""Scope qualifiers and dependent assessment wording, without QID-specific rules."""
from dataclasses import replace

import pytest

from app.hus.answering import HUSAnswerer
from app.hus.chat import chat
from app.hus.question_routing import question_intent, requested_course_fields
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion
from tests.hus.test_answer_support_gate import hit, keep


@pytest.mark.parametrize('qualifier', ['CLC', 'clc', 'hệ CLC', 'hệ chất lượng cao',
                                      'chuong trinh chat luong cao', 'chương trình đào tạo chất lượng cao'])
def test_variant_alias_uses_verified_metadata_not_repeated_body_words(qualifier):
    right = hit('Tư vấn, phân tích và thiết kế dự án.', variant='high_quality', source='right')
    wrong = hit('Tư vấn, phân tích và thiết kế dự án CLC.', variant='standard', source='wrong')
    assert keep(f'Cơ hội nghề nghiệp {qualifier} về phân tích và thiết kế?', wrong, right) == (right,)


@pytest.mark.parametrize('variant', ['unknown', 'standard', 'talent'])
@pytest.mark.parametrize('body', ['Tư vấn và thiết kế.', 'Tư vấn và thiết kế cho hệ CLC.'])
def test_wrong_or_unknown_scope_cannot_be_overridden_by_title_or_body(variant, body):
    wrong = hit(body, variant=variant)
    wrong = replace(wrong, chunk=replace(wrong.chunk, metadata={**wrong.chunk.metadata, 'title': 'Ngành CLC'}))
    assert not keep('Cơ hội nghề nghiệp CLC về thiết kế?', wrong)


@pytest.mark.parametrize('question', [
    'Cơ hội nghề nghiệp CLC về lượng tử?',
    'Cơ hội nghề nghiệp CLC có 997 hướng?',
    'Cơ hội nghề nghiệp CLC theo edition 2008?',
    'Cơ hội nghề nghiệp CLC và hệ chuẩn?',
    'Cơ hội nghề nghiệp CLCX?',
    'Cơ hội nghề nghiệp CLC123?',
    'Cơ hội nghề nghiệp có chất lượng cao?',
])
def test_variant_recognition_never_erases_unrelated_facts_or_edition(question):
    assert not keep(question, hit('Tư vấn và thiết kế.', variant='high_quality'))


@pytest.mark.parametrize('question', [
    'Gợi ý đánh giá MAT3557 theo phần tham khảo AI đã lưu có nội dung gì?',
    'Phần gợi ý đánh giá MAT3533 có nội dung gì?',
    'Noi dung cua phan goi y danh gia MAT3300 la gi?',
    'Nội dung của gợi ý đánh giá MAT3539 là gì?',
    'Đề xuất kiểm tra MAT3533 có nội dung như thế nào?',
])
def test_content_of_assessment_is_a_single_field(question):
    assert requested_course_fields(question) == ('suggested_assessment',)
    assert question_intent(question) == ('f3', 'suggested_assessment')


@pytest.mark.parametrize('question,fields', [
    ('Nội dung MAT3557 và gợi ý đánh giá MAT3557?', {'content', 'suggested_assessment'}),
    ('Gợi ý đánh giá MAT3557 và nội dung gì?', {'content', 'suggested_assessment'}),
    ('Gợi ý đánh giá MAT3557 có nội dung gì; nội dung môn học là gì?', {'content', 'suggested_assessment'}),
    ('Nội dung của gợi ý đánh giá MAT3557 và mục tiêu nào?', {'objectives', 'suggested_assessment'}),
    ('MAT3557 có bao nhiêu tín chỉ và thi thế nào?', {'credits', 'suggested_assessment'}),
    ('Nội dung MAT3557 là gì?', {'content'}),
    ('Không hỏi nội dung MAT3557, chỉ hỏi gợi ý đánh giá.', {'suggested_assessment'}),
    ('Gợi ý đánh giá MAT3557; không hỏi nội dung môn học.', {'suggested_assessment'}),
])
def test_independent_fields_and_negation_are_preserved(question, fields):
    assert set(requested_course_fields(question)) == fields


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.fixture(autouse=True)
def llm_off(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')


@pytest.mark.parametrize('qualifier', ['CLC', 'hệ chất lượng cao', 'chương trình CLC'])
def test_real_f1_scope_is_filtered_before_retrieval_and_quote_stays_canonical(answerer, monkeypatch, qualifier):
    calls = []
    search = answerer.retriever.search

    def capture(query, **kwargs):
        calls.append(kwargs)
        return search(query, **kwargs)

    monkeypatch.setattr(answerer.retriever, 'search', capture)
    request = HUSQuestion(major='computer_science', version='QD3568-2023',
        question=f'Cơ hội nghề nghiệp ngành Máy tính và Khoa học thông tin {qualifier} về phân tích và thiết kế?')
    result = chat(request, answerer)
    assert result.hus_answer.status == 'answered', result.reply
    assert calls and calls[0]['program_variant'] == 'high_quality'
    assert all(c.metadata['program_variant'] == 'high_quality' for c in result.hus_answer.citations)
    assert all(c.quote in result.reply for c in result.hus_answer.citations)
    assert all('clc' not in c.quote.casefold() for c in result.hus_answer.citations)


@pytest.mark.parametrize('question,variant', [
    ('Cơ hội nghề nghiệp KHMTTT CLC và hệ chuẩn?', None),
    ('Cơ hội nghề nghiệp KHMTTT CLC?', 'standard'),
    ('Cơ hội nghề nghiệp KHMTTT hệ chất lượng cao?', 'unknown'),
])
def test_conflicting_scope_is_clarified_without_search(answerer, monkeypatch, question, variant):
    monkeypatch.setattr(answerer.retriever, 'search', lambda *a, **k: pytest.fail('Conflicting scope searched'))
    result = chat(HUSQuestion(major='computer_science', question=question, program_variant=variant), answerer)
    assert result.hus_answer.status == 'needs_clarification'
    assert not result.hus_answer.citations and not result.hus_answer.facts


@pytest.mark.parametrize('major,version,code', [
    ('computer_science', 'QD3568-2023', 'MAT3557'),
    ('data_science', 'QD3569-2023', 'MAT3533'),
    ('mathematics', 'QD3565-2023', 'MAT3300'),
    ('mathematics_informatics', 'QD3567-2023', 'MAT3539'),
])
def test_missing_assessment_after_single_field_reading_is_not_invented(answerer, major, version, code):
    request = HUSQuestion(major=major, version=version, allow_generated_reference=True,
        question=f'Gợi ý đánh giá {code} theo phần AI tham khảo có nội dung gì?')
    result = chat(request, answerer)
    assert result.hus_answer.status == 'no_information'
    assert not result.hus_answer.facts and not result.hus_answer.citations
    denied = chat(request.model_copy(update={'allow_generated_reference': False}), answerer)
    assert denied.hus_answer.status == 'needs_clarification' and not denied.hus_answer.citations


@pytest.mark.parametrize('question', [
    'Nội dung MAT3557 và gợi ý đánh giá MAT3557?',
    'Gợi ý đánh giá MAT3557 có nội dung gì; nội dung môn MAT3557 gồm gì?',
    'Nội dung của gợi ý đánh giá MAT3557 và số tín chỉ?',
])
def test_real_multi_field_stays_clarification_even_with_field_hint(answerer, question):
    result = chat(HUSQuestion(major='computer_science', version='QD3568-2023', question=question,
        dataset='f3', field='suggested_assessment', allow_generated_reference=True), answerer)
    assert result.hus_answer.status == 'needs_clarification'
    assert not result.hus_answer.facts and not result.hus_answer.citations


def test_official_assessment_request_still_cannot_use_ai(answerer):
    result = chat(HUSQuestion(major='computer_science', version='QD3568-2023', allow_generated_reference=True,
        question='Nội dung gợi ý đánh giá MAT3557 có xác nhận tỷ lệ thi cuối kỳ chính thức không?'), answerer)
    assert result.hus_answer.status == 'no_information'
    assert not result.hus_answer.citations


def test_alternative_source_and_explicit_edition_are_not_rewritten_to_old_gold(answerer):
    broad = chat(HUSQuestion(major='computer_science', version='QD3568-2023',
        question='Học tiếp ngành KHMTTT ở bậc Thạc sĩ, Tiến sĩ có những lĩnh vực nào theo nguồn?'), answerer)
    assert broad.hus_answer.status == 'answered'
    assert any(c.metadata['program_version'] == '2023' and 'đủ điều kiện' in c.quote
               for c in broad.hus_answer.citations)
    impossible = chat(HUSQuestion(major='computer_science', question=
        'Học tiếp ngành KHMTTT theo edition 1999 hệ chuẩn có những lĩnh vực nào?'), answerer)
    assert impossible.hus_answer.status == 'no_information' and not impossible.hus_answer.citations


def test_variant_enumeration_requires_one_source_body_and_rejects_comparison_or_conflict(answerer, monkeypatch):
    question = 'Theo trang giới thiệu đã lưu, Toán học có hệ chuẩn và hệ tài năng như thế nào?'
    both = hit('Khoa có 2 chương trình đào tạo cử nhân hệ chuẩn và hệ cử nhân tài năng.',
               field='introduction', variant='unknown', source='both')
    only_std = hit('Chương trình đào tạo cử nhân hệ chuẩn.', field='introduction', variant='standard', source='std')
    only_tal = hit('Chương trình đào tạo hệ cử nhân tài năng.', field='introduction', variant='talent', source='tal')
    assert keep(question, only_std, only_tal) == ()
    assert keep(question, only_std, both) == (both,)
    assert not keep('Theo trang giới thiệu đã lưu, Toán học không có hệ chuẩn và hệ tài năng như thế nào?', both)
    result = chat(HUSQuestion(major='mathematics', question=question), answerer).hus_answer
    assert result.status == 'answered' and result.dataset == 'f1'
    assert all(c.metadata['program_variant'] == 'unknown' for c in result.citations)
    monkeypatch.setattr(answerer.retriever, 'search', lambda *a, **k: pytest.fail('Conflicting/comparison scope searched'))
    for blocked, variant in [
        ('Ngành Toán học có hệ chuẩn và hệ tài năng khác nhau như thế nào?', None),
        (question, 'standard'),
    ]:
        clarify = chat(HUSQuestion(major='mathematics', question=blocked, program_variant=variant), answerer).hus_answer
        assert clarify.status == 'needs_clarification' and not clarify.citations
