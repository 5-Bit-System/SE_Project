"""General request syntax and graduate workplaces; synthetic, exposed dev cases."""
from dataclasses import replace

import pytest

from app.hus.answering import HUSAnswerer
from app.hus.chat import chat
from app.hus.question_routing import question_intent
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion
from tests.hus.test_answer_support_gate import hit, keep


@pytest.mark.parametrize('question', [
    'Vị trí lập trình viên được nêu kèm điều kiện nào?',
    'Công việc quản trị dự án được liệt kê kèm những điều kiện gì?',
    'Theo nguồn, cơ hội nghề nghiệp được ghi kèm điều kiện ra sao?',
])
def test_accompanying_condition_question_keeps_original_conditional_quote(question):
    body = 'Lập trình viên, quản trị dự án (tùy theo năng lực) tại doanh nghiệp.'
    source = hit(body)
    assert keep(question, source) == (source,)
    assert source.chunk.metadata['source_quote'] == body


@pytest.mark.parametrize('question', [
    'Vị trí lập trình viên được nêu kèm điều kiện nào?',
    'Cơ hội nghề nghiệp kèm chứng nhận ISO?',
    'Vị trí lập trình viên được nêu kèm điều kiện 997 năm kinh nghiệm nào?',
    'Cơ hội nghề nghiệp kèm kỹ năng lập trình máy bay?',
])
def test_condition_syntax_does_not_supply_missing_conditions_or_requirements(question):
    assert not keep(question, hit('Lập trình viên và quản trị dự án tại doanh nghiệp.'))


@pytest.mark.parametrize('question,field', [
    ('Tài liệu ngành Toán học trình bày những hướng học tiếp nào?', 'further_study'),
    ('Nguồn ngành Toán học trình bày mục tiêu gì?', 'objectives'),
    ('Chương trình ngành Toán học trình bày mục tiêu như thế nào?', 'objectives'),
    ('Mục tiêu ngành Toán học được trình bày ra sao?', 'objectives'),
    ('Mục tiêu ngành Toán học được trình bày như thế nào?', 'objectives'),
    ('Mục tiêu ngành Toán học được trình bày thế nào?', 'objectives'),
])
def test_source_subject_and_passive_tail_are_request_syntax(question, field):
    source = hit('Nghiên cứu khoa học, học tiếp cao học và nghiên cứu sinh.', field=field)
    assert keep(question, source) == (source,)


@pytest.mark.parametrize('question', [
    'Mục tiêu về năng lực trình bày báo cáo?',
    'Tài liệu ngành Toán học có năng lực trình bày báo cáo không?',
    'Nội dung về kỹ năng trình bày báo cáo được trình bày ra sao?',
    'Mục tiêu về lập trình máy bay được trình bày ra sao?',
    'Tài liệu ngành Toán học trình bày mục tiêu lượng tử?',
    'Mục tiêu được trình bày ra sao và có chứng nhận ISO?',
    'Mục tiêu được trình bày ra sao; có 997 năm kinh nghiệm không?',
])
def test_presentation_skills_topics_and_later_facts_remain_required(question):
    assert not keep(question, hit('Nghiên cứu khoa học và lập trình.', field='objectives'))


def test_real_presentation_skill_can_still_be_supported():
    source = hit('Năng lực trình bày báo cáo khoa học.', field='objectives')
    assert keep('Mục tiêu về năng lực trình bày báo cáo?', source) == (source,)


@pytest.mark.parametrize('question', [
    'Mục tiêu ngành Toán học không được trình bày ra sao?',
    'Mục tiêu ngành Toán học chưa được trình bày như thế nào?',
    'Vị trí lập trình viên không được nêu kèm điều kiện nào?',
    'Tài liệu ngành Toán học không trình bày mục tiêu gì?',
])
def test_negated_source_claim_is_not_an_affirmative_presentation_request(question):
    assert not keep(question, hit('Lập trình viên (tùy theo năng lực).', field='objectives'))


@pytest.mark.parametrize('scope', ['edition 1999', 'hệ CLC', 'edition chưa xác định'])
def test_passive_question_never_relaxes_explicit_scope(scope):
    assert not keep(f'Theo {scope}, mục tiêu ngành Toán học được trình bày ra sao?',
                    hit('Nghiên cứu khoa học.', field='objectives'))


@pytest.mark.parametrize('place', ['trường', 'trường đại học', 'đại học', 'viện', 'viện nghiên cứu',
                                  'trường và viện', 'doanh nghiệp', 'công ty'])
def test_graduate_role_at_workplace_routes_careers(place):
    assert question_intent(f'Ngành KHDL có những vai trò nào tại đơn vị {place}?') == ('f1', 'careers')


@pytest.mark.parametrize('question', [
    'Vai trò của trường trong đào tạo ngành KHDL là gì?',
    'Vai trò nào của viện trong chương trình ngành KHDL?',
    'Trường đại học có vai trò gì trong ngành Toán học?',
    'Viện nghiên cứu có vai trò nào đối với ngành KHDL?',
    'Vai trò nào của doanh nghiệp trong đào tạo?',
    'Công ty có vai trò gì trong chương trình?',
    'Môn MAT1202 có vai trò gì tại trường đại học?',
    'Vai trò của học phần trong chương trình ngành KHDL tại viện là gì?',
])
def test_institution_and_course_roles_are_not_graduate_careers(question):
    assert question_intent(question) != ('f1', 'careers')


@pytest.mark.parametrize('place', ['trường', 'trường đại học', 'viện', 'viện nghiên cứu'])
def test_role_routing_never_substitutes_for_workplace_evidence(place):
    question = f'Ngành KHDL có vai trò gì tại {place}?'
    wrong = hit('Nghiên cứu tại doanh nghiệp.', field='careers')
    right = hit(f'Nghiên cứu tại {place}.', field='careers', source='right')
    assert not keep(question, wrong)
    assert keep(question, wrong, right) == (right,)
    assert not keep(f'{question} và công ty?', right)


@pytest.mark.parametrize('body', ['Sinh viên nghiên cứu tại trường.',
                                'Nhân viên nghiên cứu tại doanh nghiệp.',
                                'Sinh vien nghien cuu tai truong.',
                                'Chuyen vien nghien cuu tai cong ty.'])
def test_institute_cannot_be_inferred_from_scattered_words_or_title(body):
    source = hit(body, field='careers')
    source = replace(source, chunk=replace(source.chunk,
        metadata={**source.chunk.metadata, 'title': 'Viện nghiên cứu'}))
    assert not keep('Vai trò gì tại viện nghiên cứu?', source)


@pytest.mark.parametrize('body', ['Nghiên cứu tại viện nghiên cứu.',
                                'Nghien cuu tai vien nghien cuu.'])
def test_institute_with_or_without_accents_is_supported_by_its_body(body):
    source = hit(body)
    assert keep('Vai trò gì tại viện nghiên cứu?', source) == (source,)


@pytest.mark.parametrize('body', ['Nghiên cứu thị trường tại doanh nghiệp.',
                                'Nghiên cứu môi trường tại công ty.',
                                'Nghien cuu thi truong tai doanh nghiep.',
                                'Phân tích trường hợp và trường phái nghiên cứu.'])
def test_school_workplace_is_not_an_incidental_domain_compound(body):
    assert not keep('Vai trò gì tại trường?', hit(body))


@pytest.mark.parametrize('separator', [', ', ' và ', ' hoặc '])
def test_every_listed_workplace_requires_evidence_in_one_source(separator):
    question = f'Ngành KHDL có vai trò gì tại trường{separator}viện nghiên cứu?'
    school = hit('Nghiên cứu tại trường.', start=0)
    institute = hit('Nghiên cứu tại viện nghiên cứu.', start=60)
    foreign = hit('Nghiên cứu tại viện nghiên cứu.', source='other')
    assert not keep(question, school)
    assert not keep(question, school, foreign)
    assert keep(question, school, institute) == (school, institute)


@pytest.mark.parametrize('question', [
    'Nhà trường có vai trò gì tại viện nghiên cứu?',
    'Vai trò gì của một trường tại viện nghiên cứu?',
    'Vai trò nào của những viện trong doanh nghiệp?',
    'Các nhà trường có vai trò gì tại công ty?',
])
def test_determined_institution_subject_is_not_a_graduate_role(question):
    assert question_intent(question) != ('f1', 'careers')


@pytest.mark.parametrize('negative', ['chưa', 'không'])
def test_factual_negative_condition_after_request_cannot_be_neutralized(negative):
    question = f'Vị trí lập trình viên được nêu kèm điều kiện nào nếu {negative} đủ năng lực?'
    assert not keep(question, hit('Lập trình viên nếu đủ năng lực.'))
    actual = hit(f'Lập trình viên nếu {negative} đủ năng lực.')
    assert keep(question, actual) == (actual,)


@pytest.mark.parametrize('negative', ['không', 'chưa'])
def test_a_negated_condition_marker_cannot_supply_a_positive_condition(negative):
    assert not keep('Vị trí lập trình viên được nêu kèm điều kiện nào?',
                    hit(f'Lập trình viên {negative} tùy theo năng lực.'))


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.fixture(autouse=True)
def llm_off(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')


@pytest.mark.parametrize('question', [
    'Theo edition chưa xác định, cơ hội nghề nghiệp KHDL tại trường và viện gồm vai trò gì?',
    'Theo edition chưa xác định, ngành KHDL có những vai trò nào tại đơn vị trường và viện?',
])
def test_current_data_roles_preserve_canonical_quotes_and_workplaces(answerer, question):
    result = chat(HUSQuestion(major='data_science', question=question), answerer)
    assert result.hus_answer.status == 'answered', result.reply
    assert result.hus_answer.dataset == 'f1'
    assert result.hus_answer.citations
    assert all(c.quote in result.reply for c in result.hus_answer.citations)
    assert any('trường' in c.quote.casefold() and 'viện' in c.quote.casefold()
               for c in result.hus_answer.citations)


@pytest.mark.parametrize('question', [
    'Vị trí lập trình viên KHDL theo edition chưa xác định được nêu kèm điều kiện nào?',
    'Theo edition chưa xác định, vị trí quản trị dự án KHDL được ghi kèm điều kiện ra sao?',
])
def test_current_data_preserves_the_original_ability_condition(answerer, question):
    result = chat(HUSQuestion(major='data_science', question=question), answerer)
    assert result.hus_answer.status == 'answered', result.reply
    assert any('tùy theo năng lực' in c.quote for c in result.hus_answer.citations)
    assert all(c.quote in result.reply for c in result.hus_answer.citations)


@pytest.mark.parametrize('question', [
    'Theo edition 2015 hệ chuẩn, tài liệu ngành Toán học trình bày những hướng học tiếp nào?',
    'Theo edition 2015 hệ chuẩn, mục tiêu ngành Toán Tin được trình bày ra sao?',
])
def test_current_data_presentation_wording_returns_scoped_source(answerer, question):
    major = 'mathematics_informatics' if 'Toán Tin' in question else 'mathematics'
    result = chat(HUSQuestion(major=major, question=question), answerer)
    assert result.hus_answer.status == 'answered', result.reply
    assert result.hus_answer.citations
    assert all(c.quote in result.reply and c.metadata['program_variant'] == 'standard'
               and c.metadata['program_version'] == '2015' for c in result.hus_answer.citations)


def test_current_data_teaching_exclusion_and_independent_fields_remain_guarded(answerer):
    excluded = chat(HUSQuestion(major='data_science', question=
        'Không hỏi giảng dạy tại trường; ngành KHDL có vai trò gì tại trường?'), answerer)
    # A clean research quote may remain; never return excluded teaching text.
    assert excluded.hus_answer.status in {'answered', 'no_information'}
    assert all('giảng dạy' not in c.quote.casefold() for c in excluded.hus_answer.citations)
    multi = chat(HUSQuestion(major='data_science', question=
        'Nội dung MAT1202 và mục tiêu MAT1202 được trình bày ra sao?',
        allow_generated_reference=True), answerer)
    assert multi.hus_answer.status == 'needs_clarification'


def test_passive_f3_request_still_requires_opt_in_and_retains_ai_label(answerer):
    request = HUSQuestion(major='data_science', version='QD3569-2023',
        question='Nội dung MAT2034 được trình bày ra sao?')
    denied = chat(request, answerer).hus_answer
    assert denied.status == 'needs_clarification' and not denied.citations
    allowed = chat(request.model_copy(update={'allow_generated_reference': True}), answerer).hus_answer
    assert allowed.status == 'answered' and allowed.citations
    assert all(c.display_label == 'kiến thức AI' and c.open_url is None
               and c.quote in allowed.reply for c in allowed.citations)
