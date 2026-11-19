"""Focused policy is explicit; old source/ranking fixtures are never rewritten."""
import json

import pytest

from app.hus.answering import HUSAnswerer
from app.hus.chat import chat
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion


@pytest.fixture(scope='module')
def data():
    return HUSRAGData.load_current()


def ask(data, text, major='mathematics_informatics', version='QD3567-2023', **kwargs):
    req = HUSQuestion(question=text, major=major, version=version,
                      allow_generated_reference=True, **kwargs)
    return chat(req, HUSAnswerer(data, answer_policy='focused')).hus_answer


def test_ambiguous_f1_is_resolved_before_retrieval(data):
    class NeverSearch:
        def search(self, *args, **kwargs):
            raise AssertionError('Ambiguous source must not reach retrieval')
    answerer = HUSAnswerer(data, retriever=NeverSearch(), answer_policy='focused')
    result = chat(HUSQuestion(question='Ngành KHMTTT có thể học tiếp sau đại học như thế nào?',
        major='computer_science', version='QD3568-2023'), answerer).hus_answer
    assert result.status == 'needs_clarification' and not result.citations
    assert len(result.source_choices) >= 3
    assert {c.version for c in result.source_choices} >= {'2015', '2023', 'unknown'}
    assert all(c.source_id and c.review_status for c in result.source_choices)


def test_explicit_f1_choice_uses_exact_edition_and_family(data):
    text = 'Ngành KHMTTT có thể học tiếp sau đại học như thế nào?'
    first = ask(data, text, 'computer_science', 'QD3568-2023')
    choice = next(c for c in first.source_choices if c.version == '2015' and c.program_variant == 'standard')
    result = ask(data, text, 'computer_science', choice.version,
                 program_variant=choice.program_variant, source_id=choice.source_id)
    assert result.status == 'answered'
    assert all(c.metadata['program_version'] == '2015' for c in result.citations)
    assert all(c.metadata['citation']['source_id'] == choice.source_id for c in result.citations)
    assert not result.source_choices


def test_unknown_source_is_not_inferred_standard(data):
    result = ask(data, 'Cho mình một bức tranh khái quát về ngành Toán tin.')
    assert result.status == 'answered' and result.dataset == 'f1'
    assert all(c.metadata['program_variant'] == 'unknown' for c in result.citations)
    assert all(c.metadata['program_version'] == 'unknown' for c in result.citations)


@pytest.mark.parametrize('text,titles', [
    ('Trong nội dung MAT1202, các đối tượng và kế thừa được giải thích thế nào?',
     ['Đối tượng, lớp và bất biến', 'Kế thừa, đa hình và khả năng thay thế']),
    ('Giải thích đối tượng và kế thừa trong môn Lập trình hướng đối tượng.',
     ['Đối tượng, lớp và bất biến', 'Kế thừa, đa hình và khả năng thay thế']),
])
def test_all_requested_aspects_have_direct_descriptions(data, text, titles):
    result = ask(data, text)
    assert result.status == 'answered'
    plan = json.loads(result.focus_plan)
    assert len(plan['aspects']) == 2
    assert [u['title'] for u in plan['units']] == titles
    assert 'Hợp thành tạo' not in result.reply
    assert 'thể hiện cụ thể' in result.reply and 'chứ không chỉ có cùng tên phương thức' in result.reply
    assert 'Ví dụ minh họa' not in result.reply
    assert all(c.display_label == 'kiến thức AI' for c in result.citations)
    assert 'focus_plan' not in result.model_dump()


def test_research_question_and_scope_keep_whole_description_only(data):
    result = ask(data, 'Nội dung MAT1204 hướng dẫn đặt câu hỏi nghiên cứu và giới hạn phạm vi ra sao?',
                 'computer_science', 'QD3568-2023')
    assert result.status == 'answered'
    plan = json.loads(result.focus_plan)
    assert len(plan['aspects']) == 2 and len(plan['units']) == 1
    assert 'dấu hiệu quan sát phù hợp' in result.reply
    assert 'không trả lời được câu hỏi ban đầu' in result.reply
    assert 'Tổng quan tài liệu' not in result.reply


def test_everyday_overfitting_is_related_concept_not_universal_diagnosis(data):
    text = 'Nội dung MAT3533 lý giải chuyện mô hình học thuộc dữ liệu cũ nhưng dự đoán kém trên dữ liệu mới như thế nào?'
    result = ask(data, text, 'data_science', 'QD3569-2023')
    assert result.status == 'answered'
    assert 'có thể ghi nhớ nhiễu' in result.reply and 'không kết luận' in result.reply
    plan = json.loads(result.focus_plan)
    assert len(plan['units']) == 1 and plan['units'][0]['title'] == 'Khái quát và điều chuẩn'
    assert 'Điều chuẩn và kiểm soát độ phức tạp' in result.reply


@pytest.mark.parametrize('text', [
    'Nội dung MAT3533 vì sao dự đoán kém trên dữ liệu mới?',
    'Nội dung MAT3533 không học thuộc mà vẫn dự đoán kém trên dữ liệu mới?',
    'MAT3533 học thuộc dữ liệu cũ luôn luôn làm dự đoán kém trên dữ liệu mới?',
    'Nội dung MAT1202 giải thích đối tượng và vật lý lượng tử như thế nào?',
    'Cho mình bức tranh khái quát ngành Toán tin về vật lý lượng tử.',
])
def test_unknown_or_qualified_requests_are_not_waived(data, text):
    result = ask(data, text, 'data_science', 'QD3569-2023') if 'MAT3533' in text else ask(data, text)
    assert result.status != 'answered' and not result.citations


def test_requested_examples_and_whole_content_cannot_be_dropped(data):
    example = ask(data, 'Giải thích đối tượng và kế thừa trong MAT1202 kèm ví dụ.')
    assert example.status == 'answered' and 'Ví dụ minh họa' in example.reply
    whole = ask(data, 'Toàn bộ nội dung MAT2300?', 'mathematics', 'QD3565-2023')
    assert whole.status == 'answered'
    assert len(whole.citations) == len(data.chunks('f3', major='mathematics', version='QD3565-2023',
        course_code='MAT2300', field='content', allow_generated=True))


def test_f2_and_f3_permissions_stay_separate(data):
    request = HUSQuestion(question='MAT1202 tiên quyết là gì?', major='mathematics_informatics', version='QD3567-2023')
    answerer = HUSAnswerer(data, answer_policy='focused')
    answer = chat(request, answerer).hus_answer
    assert answer.status == 'answered' and answer.facts['value'] == ['MAT2505']
    denied = chat(request.model_copy(update={'question':'Nội dung MAT1202?'}), answerer).hus_answer
    assert denied.diagnostic.code == 'permission_required' and not denied.citations


def test_source_format_selector_filters_inventory_before_ambiguity(data):
    result = ask(data, 'Theo bản DOCX, ngành KHMTTT có thể học tiếp sau đại học như thế nào?',
                 'computer_science', 'QD3568-2023')
    assert result.status == 'answered' and not result.source_choices
    assert all(c.evidence_kind == 'file' for c in result.citations)


def test_wrong_source_does_not_borrow_another_family(data):
    result = ask(data, 'Ngành KHMTTT có thể học tiếp sau đại học như thế nào?',
                 'computer_science', 'QD3568-2023', source_id='not-in-this-snapshot')
    assert result.status != 'answered' and not result.citations


def test_retriever_cannot_replace_selected_canonical_source(data):
    from dataclasses import replace

    from app.hus.rag_loader import RAGDataError
    from app.hus.retrieval import HUSRAGRetriever

    real = HUSRAGRetriever(data)
    class Tamper:
        def search(self, *args, **kwargs):
            hits = real.search(*args, **kwargs)
            return (replace(hits[0], chunk=replace(hits[0].chunk, text='tampered')), *hits[1:])
    answerer = HUSAnswerer(data, answer_policy='focused', retriever=Tamper())
    with pytest.raises(RAGDataError):
        chat(HUSQuestion(question='Nội dung MAT1202?', major='mathematics_informatics',
            version='QD3567-2023', allow_generated_reference=True), answerer)


def test_title_only_or_missing_aspect_cannot_supply_a_definition(data):
    from dataclasses import replace

    from app.hus.focused import FocusRequest, select_focus_hits
    from app.hus.retrieval import RetrievalHit

    chunk = next(c for c in data.chunks('f3', major='mathematics_informatics', version='QD3567-2023',
        course_code='MAT1202', field='content', allow_generated=True) if c.metadata.get('unit_index') == 0)
    assert not select_focus_hits((RetrievalHit(chunk, 1, ()),), FocusRequest(('object','inheritance')))
    metadata = {**chunk.metadata, 'locator': {}}
    title_only = replace(chunk, text='Đối tượng\nKhái niệm thành phần: đối tượng.', metadata=metadata)
    assert not select_focus_hits((RetrievalHit(title_only, 1, ()),), FocusRequest(('object',)))


@pytest.mark.parametrize('boundary', ['\n', ' '])
def test_unexpected_condition_after_components_keeps_the_whole_chunk(data, boundary):
    from dataclasses import replace

    from app.hus.focused import description_span
    from app.hus.retrieval import _body

    chunk = next(c for c in data.chunks('f3', major='mathematics_informatics', version='QD3567-2023',
        course_code='MAT1202', field='content', allow_generated=True) if c.metadata.get('unit_index') == 0)
    quote = ('Đối tượng\nĐối tượng là một thể hiện cụ thể.\nKhái niệm thành phần: đối tượng.' + boundary +
             'Chỉ áp dụng nếu bất biến đã được bảo toàn.\nVí dụ minh họa: một thể hiện.')
    changed = replace(chunk, text=quote, metadata={**chunk.metadata, 'locator': {}})
    start, end = description_span(changed)
    assert _body(changed)[start:end] == quote
