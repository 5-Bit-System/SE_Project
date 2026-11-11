"""General training purpose must not be replaced by a skills checklist."""

import pytest

from app.hus.answer_support import supported_hits
from app.hus.answering import MAJOR_NAMES, HUSAnswerer
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion
from tests.hus.test_answer_support_gate import hit


@pytest.mark.parametrize('question', [
    'Ngành đào tạo để xử lý vấn đề thông tin và dữ liệu nào?',
    'Mục đích đào tạo của ngành là gì?',
    'Mục tiêu chung của ngành là gì?',
])
@pytest.mark.parametrize('major', ['mathematics', 'mathematics_informatics', 'computer_science', 'data_science'])
def test_purpose_prefers_focused_aims_over_higher_ranked_outcomes(question, major):
    outcomes = hit('Chuẩn đầu ra: sinh viên vận dụng kiến thức xử lý thông tin và dữ liệu.',
                   source='outcomes', field='objectives', major=major)
    mixed = hit('Mục tiêu chung: Chương trình nhằm giải quyết vấn đề thông tin và dữ liệu.\n\n'
                'Chuẩn đầu ra: sinh viên vận dụng kiến thức lập trình, quản trị và ngoại ngữ.',
                source='mixed', field='objectives', major=major)
    purpose = hit('Chương trình nhằm giải quyết vấn đề tổ chức, lưu trữ, tìm kiếm thông tin và khai phá dữ liệu.',
                  source='purpose', field='objectives', major=major)
    result = supported_hits(question, (outcomes, mixed, purpose), aliases=MAJOR_NAMES, codes=set())
    assert result == (purpose,)


def test_explicit_learning_outcomes_keep_existing_selection():
    outcomes = hit('Chuẩn đầu ra: sinh viên có năng lực xử lý dữ liệu.', source='outcomes', field='objectives')
    purpose = hit('Chương trình nhằm giải quyết các vấn đề thông tin.', source='purpose', field='objectives')
    result = supported_hits('Chuẩn đầu ra gồm năng lực nào?', (outcomes, purpose), aliases=MAJOR_NAMES, codes=set())
    assert result == (outcomes,)


def test_purpose_cannot_borrow_unknown_topic_from_outcomes():
    source = hit('Mục tiêu chung: Chương trình nhằm giải quyết vấn đề dữ liệu.\n\n'
                 'Chuẩn đầu ra: sinh viên nghiên cứu lượng tử.', source='mixed', field='objectives')
    assert not supported_hits('Ngành đào tạo để nghiên cứu lượng tử?', (source,), aliases=MAJOR_NAMES, codes=set())


def test_purpose_heading_alone_or_in_another_hit_cannot_supply_aims():
    heading = hit('Mục tiêu chung', source='same', field='objectives', chunk_id='heading')
    unrelated = hit('Sinh viên biết xử lý và khai thác dữ liệu.', source='same', field='objectives',
                    chunk_id='unrelated', start=1000)
    assert not supported_hits('Mục tiêu chung là gì?', (heading, unrelated), aliases=MAJOR_NAMES, codes=set())


def test_explicit_outcome_wording_does_not_activate_purpose_preference():
    from app.hus.answer_support import training_purpose_requested

    assert not training_purpose_requested('Chuẩn đầu ra của chương trình đào tạo để có năng lực gì?')


@pytest.fixture(scope='module')
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.mark.parametrize('question', [
    'Ngành KHMTTT đào tạo để xử lý những vấn đề thông tin và dữ liệu nào?',
    'Mục đích đào tạo ngành KHMTTT về thông tin và dữ liệu là gì?',
    'Ngành KHMTTT đào tạo nhằm giải quyết vấn đề gì về thông tin và dữ liệu?',
    'Mục đích đào tạo của Khoa học máy tính và thông tin được tài liệu nguồn mô tả ra sao?',
])
def test_real_purpose_returns_source_aims_without_outcomes_substitution(answerer, question):
    answer = answerer.answer(HUSQuestion(question=question, major='computer_science'))
    assert answer.status == 'answered'
    assert all(c.metadata['field'] == 'objectives' for c in answer.citations)
    assert any('nhằm' in c.quote or 'Mục tiêu chung' in c.quote or 'để' in c.quote for c in answer.citations)
    if question == 'Ngành KHMTTT đào tạo để xử lý những vấn đề thông tin và dữ liệu nào?':
        assert any('nhằm đáp ứng nhu cầu đào tạo nhân lực' in c.quote for c in answer.citations)
    assert all(c.metadata['major'] == 'computer_science' for c in answer.citations)
    assert not any('Program Knowledge' in c.quote for c in answer.citations)
