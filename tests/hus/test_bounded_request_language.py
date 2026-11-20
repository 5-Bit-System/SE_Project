"""General bounded routing/language regressions; no QIDs or provider calls."""
from dataclasses import replace

import pytest

from app.hus.answering import HUSAnswerer
from app.hus.chat import chat
from app.hus.question_routing import question_intent
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion
from tests.hus.test_answer_support_gate import hit, keep


@pytest.mark.parametrize('question', [
    'Các chức danh lập trình viên và quản trị dự án được liệt kê kèm điều kiện gì?',
    'Nguồn liệt kê chức danh của cử nhân tại công ty ra sao?',
    'Cử nhân Toán học có cơ hội giảng dạy tại trường nào theo nguồn?',
    'Nguồn ghi cơ hội giảng dạy tại trường của người tốt nghiệp ra sao?',
    'Ngành KHDL có những vai trò công tác nào tại trường và viện?',
    'Nguồn ghi vai trò công tác gì tại viện nghiên cứu?',
])
def test_profession_and_teaching_request_forms_route_careers(question):
    assert question_intent(question) == ('f1', 'careers')


@pytest.mark.parametrize('question', [
    'Vai trò công tác của viện nghiên cứu trong đào tạo là gì?',
    'Vai trò công tác nào của nhà trường trong chương trình?',
    'Trường đại học có cơ hội giảng dạy trong chương trình nào?',
    'Mục tiêu MAT1204 về năng lực giảng dạy?',
    'Nội dung MAT1204 về các chức danh trong tổ chức?',
])
def test_organizations_and_course_topics_are_not_graduate_roles(question):
    assert question_intent(question) != ('f1', 'careers')


@pytest.mark.parametrize('question', [
    'Khả năng học tập nâng cao của người tốt nghiệp Toán học là gì?',
    'Theo edition 2015 hệ tài năng, khả năng học tập nâng cao được trình bày thế nào?',
    'Khả năng học tập và nâng cao trình độ sau khi tốt nghiệp ra sao?',
])
def test_further_study_heading_forms(question):
    assert question_intent(question) == ('f1', 'further_study')


@pytest.mark.parametrize('question', [
    'Nội dung nâng cao của MAT2302 là gì?',
    'Mục tiêu học tập nâng cao MAT2302?',
    'Nội dung về khả năng học tập nâng cao của môn MAT2302?',
])
def test_advanced_course_content_is_not_further_study(question):
    assert question_intent(question) != ('f1', 'further_study')


@pytest.mark.parametrize('question', [
    'Tên tiếng Việt của mã học phần MAT2403 là gì?',
    'Xin đọc tên bằng tiếng Việt của học phần MAT2304.',
    'Mã MAT2304 có tên tiếng Việt là gì?',
    'Theo danh mục ngành KHDL, tên tiếng Việt của mã MAT2403 là gì?',
])
def test_vietnamese_course_names_route_canonical_name(question):
    assert question_intent(question) == ('f2', 'name')


@pytest.mark.parametrize('question,expected', [
    ('Nội dung MAT1204 về phương pháp viết tiếng Việt?', ('f3', 'content')),
    ('Mục tiêu MAT1202 về đặt tên tiếng Việt cho lớp?', ('f3', 'objectives')),
    ('Không hỏi tên tiếng Việt; xin số tín chỉ MAT2304.', ('f2', 'credits')),
])
def test_language_topics_and_refused_name_are_not_name_requests(question, expected):
    assert question_intent(question) == expected


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.fixture(autouse=True)
def llm_off(monkeypatch):
    monkeypatch.setenv('HUS_LLM_ENABLED', 'false')


def test_vietnamese_name_lookup_preserves_exact_canonical_fact(answerer):
    result = chat(HUSQuestion(major='data_science', version='QD3569-2023',
        question='Tên tiếng Việt của mã học phần MAT2403 là gì?'), answerer).hus_answer
    assert result.status == 'answered'
    assert result.facts['field'] == 'name' and result.facts['value'] == 'Phương trình vi phân'
    assert result.facts['course_code'] == 'MAT2403' and result.citations


@pytest.mark.parametrize('hint', [False, True])
@pytest.mark.parametrize('question', [
    'Tên tiếng Anh của mã học phần MAT2403 là gì?',
    'Tên đầy đủ bằng tiếng Anh của MAT2403 là gì?',
    'Tên môn MAT2403 bằng tiếng Anh là gì?',
    'Tên học phần MAT2403 trong tiếng Anh là gì?',
])
def test_english_name_request_never_borrows_vietnamese_fact(answerer, question, hint):
    values = {'dataset': 'f2', 'field': 'name', 'course_code': 'MAT2403'} if hint else {}
    answer = chat(HUSQuestion(major='data_science', version='QD3569-2023',
                             question=question, **values), answerer).hus_answer
    assert answer.status != 'answered' and not answer.facts and not answer.citations


def test_name_language_guard_with_code_only_in_hint(answerer):
    answer = chat(HUSQuestion(major='data_science', version='QD3569-2023',
        question='Tên tiếng Anh là gì?', dataset='f2', field='name', course_code='MAT2403'), answerer).hus_answer
    assert answer.status != 'answered' and not answer.facts and not answer.citations


def test_refused_english_content_is_not_an_english_name_request(answerer):
    answer = chat(HUSQuestion(major='data_science', version='QD3569-2023',
        question='Tên môn MAT2403 là gì; không hỏi nội dung bằng tiếng Anh.'), answerer).hus_answer
    assert answer.status == 'answered' and answer.facts['value'] == 'Phương trình vi phân'


def test_independent_name_and_credits_still_need_clarification(answerer):
    answer = chat(HUSQuestion(major='data_science', version='QD3569-2023',
        question='Xin tên tiếng Việt và số tín chỉ của MAT2403.'), answerer).hus_answer
    assert answer.status == 'needs_clarification' and not answer.facts and not answer.citations


@pytest.mark.parametrize('question', [
    'Nguồn ghi khả năng học tiếp kèm điều kiện gì?',
    'Khả năng học tiếp được ghi kèm điều kiện gì?',
    'Nguồn nêu khả năng học sau đại học kèm những điều kiện nào?',
])
def test_bare_further_study_condition_is_explicit_evidence(question):
    source = hit('Sinh viên đủ điều kiện và có nhu cầu học tập nâng cao trình độ '
                 'sẽ có thể học tiếp Thạc sĩ, Tiến sĩ.', field='further_study')
    assert keep(question, source) == (source,)


@pytest.mark.parametrize('body', [
    'Sinh viên có thể học tiếp Thạc sĩ, Tiến sĩ.',
    'Không yêu cầu sinh viên đủ điều kiện và có nhu cầu để có thể học tiếp.',
    'Sinh viên không cần đủ điều kiện và có nhu cầu để có thể học tiếp.',
    'Sinh viên đủ điều kiện. Người khác có nhu cầu sẽ có thể học tiếp.',
])
def test_bare_condition_never_invents_or_merges_condition_conjuncts(body):
    assert not keep('Nguồn ghi khả năng học tiếp kèm điều kiện gì?',
                    hit(body, field='further_study'))


@pytest.mark.parametrize('question', [
    'Bản nguồn ngành Toán học trình bày khả năng học tiếp ra sao?',
    'Theo bản tài liệu ngành Toán học trình bày khả năng học tiếp như thế nào?',
])
def test_bounded_source_subject_prefixes(question):
    source = hit('Sinh viên có thể học tiếp cao học.', field='further_study')
    assert keep(question, source) == (source,)


def test_profession_head_is_grammar_but_named_roles_are_facts():
    source = hit('Lập trình viên, quản trị dự án, trưởng phòng (tùy theo năng lực).')
    assert keep('Các chức danh lập trình viên và quản trị dự án được liệt kê kèm điều kiện gì?', source) == (source,)
    assert not keep('Các chức danh phi hành gia được liệt kê kèm điều kiện gì?', source)
    assert not keep('Chức danh lập trình viên được nêu kèm điều kiện chứng nhận ISO nào?', source)


def test_work_role_head_keeps_literal_workplaces():
    source = hit('Giảng viên, nghiên cứu viên tại trường và viện.')
    assert keep('Nguồn liệt kê vai trò công tác nào tại trường và viện?', source) == (source,)
    assert not keep('Nguồn liệt kê vai trò công tác nào tại doanh nghiệp?', source)


def ai_hit(body):
    source = hit(body, field='objectives')
    return replace(source, chunk=replace(source.chunk, dataset='f3',
        metadata={**source.chunk.metadata, 'content_origin': 'generated', 'review_status': 'needs_review'}))


@pytest.mark.parametrize('prefix', ['trong hồ sơ AI tham khảo đã lưu', 'theo hồ sơ AI tham khảo'])
def test_ai_record_locator_is_not_a_required_academic_topic(prefix):
    source = ai_hit('Mục tiêu: phân tích dữ liệu và giải thích mô hình.')
    assert keep(f'Các mục tiêu nào {prefix}?', source) == (source,)


@pytest.mark.parametrize('question', [
    'Mục tiêu về lập hồ sơ khoa học?',
    'Mục tiêu về họ phân phối và số liệu?',
    'Mục tiêu về kỹ năng trình bày báo cáo?',
    'Mục tiêu về lập trình máy bay?',
])
def test_record_presentation_and_aircraft_topics_remain_factual(question):
    assert not keep(question, ai_hit('Phân tích dữ liệu và giải thích mô hình.'))


def test_ai_locator_never_selects_official_source_instead():
    assert not keep('Các mục tiêu nào trong hồ sơ AI tham khảo đã lưu?',
                    hit('Mục tiêu: phân tích dữ liệu.', field='objectives'))


@pytest.mark.parametrize('question', [
    'Các mục tiêu không có trong hồ sơ AI tham khảo đã lưu?',
    'Các mục tiêu chưa được lưu trong hồ sơ AI tham khảo đã lưu?',
])
def test_negated_profile_claim_cannot_become_positive_source_evidence(question):
    assert not keep(question, ai_hit('Mục tiêu: phân tích dữ liệu.'))


def test_profile_selector_does_not_erase_negative_claim_in_next_clause():
    assert not keep('Các mục tiêu trong hồ sơ AI tham khảo đã lưu, không có những mục tiêu nào?',
                    ai_hit('Mục tiêu: phân tích dữ liệu.'))


@pytest.mark.parametrize('question', [
    'Bản nguồn ngành Toán học không trình bày khả năng học tiếp ra sao?',
    'Nguồn ghi khả năng học tiếp kèm điều kiện chứng nhận ISO nào?',
])
def test_new_source_grammar_keeps_negation_and_added_requirements(question):
    assert not keep(question, hit('Sinh viên đủ điều kiện và có nhu cầu sẽ có thể học tiếp.',
                                 field='further_study'))
