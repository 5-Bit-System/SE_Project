"""Exposed A7 diagnostics and independent phrasing/safety regressions, never holdout."""

import json
from pathlib import Path

import pytest

from app.hus.answer_support import supported_hits
from app.hus.answering import MAJOR_NAMES, HUSAnswerer
from app.hus.chat import chat
from app.hus.question_routing import question_intent, unsupported_request
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion
from tests.hus.test_answer_support_gate import hit

PACK = Path('data/hus/evaluation/a7_v4_candidate_20261111_r2/pack.json')
EXPOSED = json.loads(PACK.read_bytes())
FAILED = {f'A7V4-Q{i:03d}' for i in (1, 2, 7, 14, 20, 32, 37, 38, 43)}


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.mark.parametrize('case', [q for q in EXPOSED['questions']
                                if q['question_id'] in FAILED - {'A7V4-Q001'}],
                         ids=lambda q: q['question_id'])
def test_exposed_failures_answer_from_correct_field_and_immutable_sources(answerer, case):
    gold = next(g for g in EXPOSED['gold'] if g['question_id'] == case['question_id'])
    answer = chat(HUSQuestion(**case['request']), answerer).hus_answer
    assert answer.status == 'answered', answer.reply
    assert answer.dataset == gold['expected_dataset']
    assert answer.citations
    assert all(c.metadata['field'] == gold['expected_field'] for c in answer.citations)
    assert all(c.quote and c.quote in answer.reply for c in answer.citations)
    if answer.dataset == 'f3':
        assert all(c.display_label == 'kiến thức AI' and c.open_url is None for c in answer.citations)


def test_historical_admission_with_unknown_variant_still_cannot_answer_standard_scope(answerer, monkeypatch):
    case = next(q for q in EXPOSED['questions'] if q['question_id'] == 'A7V4-Q001')
    seen, calls = [], []
    real = answerer.retriever.search

    def search(*args, **kwargs):
        calls.append(kwargs)
        result = real(*args, **kwargs)
        seen.extend(result)
        return result

    monkeypatch.setattr(answerer.retriever, 'search', search)
    answer = chat(HUSQuestion(**case['request']), answerer).hus_answer
    assert calls, 'Historical admissions should reach retrieval rather than the current-admission block'
    assert calls[0]['program_variant'] == 'standard'
    # The historical evidence still exists, but the explicit scope now excludes
    # it before ranking instead of fetching unknown-scope hits then refusing.
    assert any('2012' in c.metadata.get('source_quote', '')
               and c.metadata.get('program_variant') == 'unknown'
               for c in answerer.data.chunks('f1', major='computer_science', field='introduction'))
    assert all(h.chunk.metadata.get('program_variant') == 'standard' for h in seen)
    assert answer.status == 'no_information' and not answer.citations


@pytest.mark.parametrize('question,expected', [
    ('Nội dung MAT3500 về lý thuyết đồ thị?', ('f3', 'content')),
    ('Noi dung MAT3500 ve do thi?', ('f3', 'content')),
    ('Nội dung MAT2501: đồ thị và xấp xỉ?', ('f3', 'content')),
    ('Nội dung MAT3500 và thi cuối kỳ chiếm bao nhiêu phần trăm?', ('f3', 'official_assessment')),
    ('MAT3500 thi tự luận hay trắc nghiệm?', ('f3', 'official_assessment')),
    ('Gợi ý đánh giá MAT3500?', ('f3', 'suggested_assessment')),
    ('Mục tiêu ngành đào tạo cho nghề nghiệp nào?', ('f1', 'objectives')),
    ('Ngành này có cơ hội nghề nghiệp gì?', ('f1', 'careers')),
    ('Vị trí nghề nghiệp phù hợp năng lực nào?', ('f1', 'careers')),
    ('Lịch sử chương trình: trước đây từng mang tên gì?', ('f1', 'introduction')),
    ('MAT3500 mang tên gì?', ('f2', 'name')),
    ('Tên môn MAT3500?', ('f2', 'name')),
])
def test_polysemous_terms_keep_subject_and_field(question, expected):
    assert question_intent(question) == expected


@pytest.mark.parametrize('question', [
    'Nội dung MAT2311 về ước lượng khoảng?',
    'Noi dung MAT2311 ve uoc luong khoang?',
    'Giới thiệu ngành bắt đầu tuyển sinh năm nào?',
    'Ngành tuyển sinh lần đầu vào năm nào?',
])
def test_supported_scientific_and_historical_context_is_not_current_salary_or_admission(question):
    assert not unsupported_request(question)


@pytest.mark.parametrize('question', [
    'Ước lượng mức lương sau tốt nghiệp?',
    'Ngành bắt đầu tuyển sinh năm nay?',
    'Ngành bắt đầu tuyển sinh năm 2027?',
    'Chỉ tiêu tuyển sinh lần đầu bao nhiêu?',
    'Giới thiệu năm bắt đầu tuyển sinh và điểm chuẩn?',
    'Giới thiệu mốc bắt đầu tuyển sinh; đăng ký tuyển sinh ra sao?',
])
def test_salary_current_admission_metrics_and_later_requests_still_blocked(question):
    assert unsupported_request(question)


@pytest.mark.parametrize('major,version,question,anchor', [
    ('computer_science', 'QD3568-2023', 'Ngành KHMTTT bắt đầu tuyển sinh năm nào?', '2012'),
    ('computer_science', 'QD3568-2023', 'Xin giới thiệu mốc bắt đầu tuyển sinh của ngành KHMTTT.', '2012'),
    ('computer_science', 'QD3568-2023', 'Mục đích ngành KHMTTT phục vụ những bài toán dữ liệu nào?', 'lưu trữ'),
    ('data_science', 'QD3569-2023', 'Mục tiêu ngành Khoa học dữ liệu về thực hành nghề nghiệp?', 'thực hành'),
    ('mathematics_informatics', 'QD3567-2023', 'Lịch sử ngành Toán Tin từng mang tên gì?', '1993'),
    ('mathematics_informatics', 'QD3567-2023', 'Mục đích đào tạo ngành Toán Tin là gì?', 'Tin học'),
    ('computer_science', 'QD3568-2023', 'Nội dung MAT3500: đồ thị và cây?', 'Đồ thị và cây'),
    ('data_science', 'QD3569-2023', 'Nội dung MAT2501, phần đạo hàm trình bày gì?', 'Đạo hàm'),
    ('mathematics', 'QD3565-2023', 'Nội dung MAT2311: ước lượng và khoảng tin cậy?', 'khoảng tin cậy'),
    ('mathematics_informatics', 'QD3567-2023', 'Nội dung MAT3533 trình bày hàm mất mát như thế nào?', 'mất mát'),
])
def test_paraphrases_require_actual_source_body(answerer, major, version, question, anchor):
    answer = chat(HUSQuestion(question=question, major=major, version=version,
                              allow_generated_reference=True), answerer).hus_answer
    assert answer.status == 'answered', answer.reply
    assert any(anchor in c.quote for c in answer.citations)


@pytest.mark.parametrize('question', [
    'Nội dung MAT3500 về đồ thị lượng tử và cây?',
    'Nội dung MAT2311: ước lượng lỗ đen?',
    'Nội dung MAT3533 trình bày thần giao cách cảm như thế nào?',
    'Mục đích đào tạo ngành Toán Tin về du hành thời gian?',
])
def test_new_request_syntax_never_licenses_unknown_subjects(answerer, question):
    answer = chat(HUSQuestion(question=question, major='mathematics_informatics',
                             version='QD3567-2023', allow_generated_reference=True), answerer).hus_answer
    assert answer.status != 'answered' and not answer.citations


def test_presentation_skill_is_still_a_factual_requirement():
    source = hit('Chuẩn đầu ra: sinh viên có năng lực tính toán.', field='objectives')
    assert not supported_hits('Chuẩn đầu ra về năng lực trình bày?', (source,), aliases=MAJOR_NAMES, codes=set())


def test_former_name_request_cannot_be_satisfied_by_an_unrelated_introduction():
    source = hit('Chương trình đào tạo bắt đầu từ năm 1993.', field='introduction')
    assert not supported_hits('Giới thiệu lịch sử chương trình từng mang tên gì?',
                              (source,), aliases=MAJOR_NAMES, codes=set())


def test_purpose_heading_must_not_borrow_an_outcomes_only_paragraph():
    source = hit('Mục tiêu đào tạo\n\nChuẩn đầu ra: sinh viên có năng lực xử lý dữ liệu lượng tử.',
                 field='objectives')
    assert not supported_hits('Mục đích đào tạo về lượng tử?', (source,), aliases=MAJOR_NAMES, codes=set())


def test_former_name_source_must_be_rendered_even_when_only_another_hit_matches_topic():
    topic = hit('Chương trình có lĩnh vực alpha.', source='same', field='introduction', start=10)
    history = hit('Trước đây là chương trình Beta.', source='same', field='introduction', start=100)
    assert supported_hits('Giới thiệu chương trình alpha từng mang tên gì?',
                          (topic, history), aliases=MAJOR_NAMES, codes=set()) == (topic, history)


def test_inline_purpose_heading_must_not_turn_outcomes_into_program_aims():
    source = hit('Mục tiêu đào tạo\nChuẩn đầu ra: sinh viên có năng lực xử lý dữ liệu lượng tử.',
                 field='objectives')
    assert not supported_hits('Mục đích đào tạo về lượng tử?', (source,), aliases=MAJOR_NAMES, codes=set())
