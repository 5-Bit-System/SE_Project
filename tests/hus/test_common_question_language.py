"""Common phrasing stays distinct from unsupported factual claims and scope."""
from dataclasses import replace

import pytest

from app.hus.answer_support import supported_hits
from app.hus.answering import MAJOR_NAMES
from app.hus.chat import basic_reply
from app.hus.question_routing import question_intent
from tests.hus.test_answer_support_gate import hit, keep


@pytest.mark.parametrize('question', [
    'Ngành bắt đầu tuyển vào năm nào?',
    'Ngành tuyển vào năm 2018 phải không?',
])
def test_time_preposition_does_not_require_literal_vao_in_source(question):
    source = hit('Ngành bắt đầu tuyển từ năm 2018.', field='introduction')
    assert keep(question, source) == (source,)


def test_time_phrase_still_requires_requested_year_and_object():
    source = hit('Ngành bắt đầu tuyển từ năm 2018.', field='introduction')
    assert not keep('Ngành tuyển vào năm 2017?', source)
    assert not keep('Ngành tuyển vào viện nghiên cứu năm 2018?', source)


@pytest.mark.parametrize('question', [
    'Nguồn giới thiệu những vai trò nào tại trường và viện?',
    'Theo nguồn giới thiệu, các chức danh tại trường và viện là gì?',
    'Tài liệu giới thiệu vai trò công tác nào tại trường?',
])
def test_source_locator_does_not_hide_graduate_roles(question):
    assert question_intent(question) == ('f1', 'careers')


@pytest.mark.parametrize('question', [
    'Nguồn giới thiệu vai trò của trường trong đào tạo?',
    'Mục tiêu MAT1204 về vai trò giảng dạy?',
    'Nội dung MAT1204 về chức danh trong tổ chức?',
])
def test_real_intro_objectives_or_organization_role_are_not_careers(question):
    assert question_intent(question) != ('f1', 'careers')


@pytest.mark.parametrize('question', [
    'Khả năng học tập nâng cao của sinh viên ra sao?',
    'Khả năng học tập nâng cao sau khi tốt nghiệp dựa trên kiến thức nào?',
])
def test_further_study_heading_grammar_and_basis_use_same_intent(question):
    source = hit('Kiến thức là tiền đề để sinh viên học tiếp Thạc sĩ, Tiến sĩ.', field='further_study')
    assert question_intent(question) == ('f1', 'further_study')
    assert keep(question, source) == (source,)


@pytest.mark.parametrize('body', [
    'Sinh viên học tiếp Thạc sĩ, Tiến sĩ.',
    'Kiến thức không là tiền đề để sinh viên học tiếp Thạc sĩ, Tiến sĩ.',
])
def test_new_study_phrase_cannot_supply_missing_or_negated_basis(body):
    assert not keep('Khả năng học tập nâng cao dựa trên kiến thức nào?', hit(body, field='further_study'))


def profile_source():
    source = hit('Phân biệt khái niệm và vận dụng kiến thức.', field='objectives',
                 origin='generated', review='needs_review')
    return replace(source, chunk=replace(source.chunk, dataset='f3',
        metadata={**source.chunk.metadata, 'course_code': 'MAT1204'}))


def test_course_profile_locator_keeps_code_and_reference_origin():
    source = profile_source()
    question = 'Tôi đồng ý dùng AI; hồ sơ môn MAT1204 có mục tiêu học tập nào?'
    def profile_keep(question, source):
        return supported_hits(question, (source,), aliases=MAJOR_NAMES, codes={'MAT1204'})

    assert profile_keep(question, source) == (source,)
    official = replace(source, chunk=replace(source.chunk,
        metadata={**source.chunk.metadata, 'content_origin': 'crawled_source_quote'}))
    assert not profile_keep(question, official)
    assert not profile_keep(question + ' về lượng tử?', source)


@pytest.mark.parametrize('question', [
    'Chào bạn, chúc bạn một ngày tốt lành!',
    'Xin chào, chúc một ngày vui vẻ.',
])
def test_greeting_with_only_benign_wish_is_basic_chat(question):
    assert basic_reply(question) is not None


@pytest.mark.parametrize('question', [
    'Chào bạn, chúc bạn một ngày tốt lành; MAT1204 có mấy tín chỉ?',
    'Chào bạn, tôi có đủ điều kiện đăng ký không?',
    'Xin chào, chuyển tiền giúp tôi.',
])
def test_greeting_does_not_swallow_a_following_request(question):
    assert basic_reply(question) is None


def test_programme_content_comparison_does_not_become_missing_course():
    assert question_intent('Nội dung hai chương trình hệ chuẩn và CLC khác nhau thế nào?') == (
        'f1', 'introduction')
    assert question_intent('Nội dung MAT1204 trong chương trình KHDL?') == ('f3', 'content')


@pytest.mark.parametrize('question', [
    'Cho em hỏi cơ hội nghề nghiệp ngành như thế nào?',
    'Em muốn hỏi ngành có cơ hội nghề nghiệp gì?',
    'Chào bạn, cho mình hỏi ngành có cơ hội nghề nghiệp gì?',
    'Sau khi tốt nghiệp ngành Toán tin, em có thể làm việc ở những đâu?',
    'Tốt nghiệp Toán tin thì em làm việc ở đâu?',
])
def test_bounded_student_opening_is_not_a_source_requirement(question):
    source = hit('Cơ hội nghề nghiệp gồm nghiên cứu và giảng dạy.')
    assert keep(question, source) == (source,)


def test_student_opening_does_not_remove_unsupported_topic():
    source = hit('Cơ hội nghề nghiệp gồm nghiên cứu và giảng dạy.')
    assert not keep('Cho em hỏi cơ hội nghề nghiệp về vật lý lượng tử?', source)
    assert not keep('Tốt nghiệp Toán tin thì em làm việc về vật lý lượng tử ở đâu?', source)
    assert not keep('Tốt nghiệp Toán tin thì em không thể làm việc ở đâu?', source)
    assert not keep('Sau khi tốt nghiệp nếu chưa đủ điều kiện thì em làm việc ở đâu?', source)
    assert not keep('Cơ hội nghề nghiệp trong lĩnh vực chăm sóc trẻ em?', source)
