"""Evidence support separates bounded request syntax from source requirements."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from app.hus.answer_support import supported_hits
from app.hus.answering import MAJOR_NAMES
from app.hus.chat import chat
from app.hus.rag_loader import RAGChunk
from app.hus.retrieval import RetrievalHit
from app.schemas.hus import HUSQuestion
from app.services.hus_service import get_hus_answerer

PACK = Path(__file__).resolve().parents[2] / 'data/hus/evaluation/diagnostic_dev_v3_support'


def read_rows(name):
    return [json.loads(line) for line in (PACK / name).read_text(encoding='utf-8').splitlines()]


@pytest.fixture(scope='module')
def answerer():
    return get_hus_answerer()


@pytest.mark.parametrize('case', read_rows('questions.jsonl'), ids=lambda q: q['question_id'])
def test_exposed_natural_requests_return_all_pinned_evidence_without_gold_hints(answerer, case):
    request = HUSQuestion(**case['request'])
    answer = chat(request, answerer).hus_answer
    assert answer.status == 'answered', answer.reply
    gold = next(g for g in read_rows('gold.jsonl') if g['question_id'] == case['question_id'])
    evidence = {e['evidence_id']: e for e in read_rows('evidence.jsonl')}
    # Verbatim evidence must be present, including every corrected Q043/Q044 part.
    # These inherited anchors are source coverage checks, not semantic certification.
    for eid in gold['evidence_ids']:
        assert evidence[eid]['value'] in answer.reply, (case['question_id'], eid)
    assert answer.dataset == gold['expected_dataset'] and answer.major == request.major
    assert all(c.review_status and c.content_origin for c in answer.citations)
    if answer.dataset == 'f3':
        assert all(c.display_label == 'kiến thức AI' and c.open_url is None for c in answer.citations)
    else:
        assert 'chưa xác minh hiệu lực hiện tại' in answer.reply


def hit(body, *, source='one', edition='2015', variant='standard', field='careers', major='mathematics',
        chunk_id=None, start=0, origin='crawled_source_quote', review='include'):
    metadata = {'source_quote': body, 'field': field, 'program_variant': variant,
                'content_origin': origin, 'review_status': review,
                'citation': {'source_id': source, 'source_sha256': 'a' * 64},
                'locator': {'start_char': start, 'end_char': start + len(body)}}
    chunk = RAGChunk('f1', chunk_id or source + str(start), body, major, edition, metadata, 'test', 'a' * 64)
    return RetrievalHit(chunk, 1.0, ())


def keep(question, *hits):
    return supported_hits(question, tuple(hits), aliases=MAJOR_NAMES, codes=set())


@pytest.mark.parametrize('prefix', ['edition 2015', 'phiên bản 2015', 'edition chưa xác định', 'phiên bản chưa rõ'])
def test_edition_qualifier_is_checked_against_metadata_not_discarded(prefix):
    expected = 'unknown' if 'chưa' in prefix else '2015'
    right = hit('Giảng dạy và nghiên cứu.', edition=expected)
    wrong = hit('Giảng dạy và nghiên cứu.', edition='2008', source='other')
    assert keep(f'Theo {prefix}, hãy trình bày cơ hội nghề nghiệp.', wrong, right) == (right,)
    assert keep(f'Theo {prefix}, hãy trình bày cơ hội nghề nghiệp.', wrong) == ()


def test_metadata_does_not_erase_an_unrelated_year_or_number_claim():
    h = hit('Cơ hội giảng dạy và nghiên cứu.')
    assert not keep('Ngành có 997 nhóm nghề nghiệp?', h)
    assert not keep('Giới thiệu ngành được thành lập năm 2015?', h)
    assert not keep('Theo edition 2015, ngành có 997 nhóm nghề nghiệp?', h)


def test_request_phrase_removal_preserves_unknown_topic_and_later_assertions():
    h = hit('Cơ hội giảng dạy và nghiên cứu.')
    assert keep('Hãy trình bày các nhóm nghề nghiệp, giữ rõ giới hạn nguồn.', h) == (h,)
    assert not keep('Hãy trình bày các nhóm nghề nghiệp về hố đen, giữ rõ giới hạn nguồn.', h)
    assert not keep('Chỉ coi đây là đề xuất, không phải quy định thi; ngành có 997 nhóm nghề nghiệp?', h)
    assert not keep('Không suy sang quy định đang áp dụng; hãy nêu chủ đề lượng tử.', h)


@pytest.mark.parametrize('boundary', [';', '.', ' nhưng '])
def test_request_grammar_cannot_join_a_negative_and_a_new_positive_clause(boundary):
    h = hit('Cơ hội giảng dạy và nghiên cứu.')
    assert not keep(f'Cơ hội nghề nghiệp; không{boundary}suy sang quy định đang áp dụng.', h)


@pytest.mark.parametrize('case', read_rows('questions.jsonl'), ids=lambda q: q['question_id'])
def test_each_repaired_request_still_obeys_explicit_version_filter(answerer, case):
    request = HUSQuestion(**case['request']).model_copy(update={'version': '1999'})
    answer = chat(request, answerer).hus_answer
    assert answer.status == 'no_information' and not answer.citations


@pytest.mark.parametrize('case', [q for q in read_rows('questions.jsonl') if q['request']['allow_generated_reference']],
                         ids=lambda q: q['question_id'])
def test_each_generated_request_still_requires_real_boolean_opt_in(answerer, case):
    request = HUSQuestion(**case['request']).model_copy(update={'allow_generated_reference': False})
    answer = chat(request, answerer).hus_answer
    assert answer.status == 'needs_clarification' and not answer.citations


def test_supported_topics_can_span_chunks_only_with_the_same_exact_source_scope():
    first, second = hit('Chuyên gia phân tích alpha.', start=10), hit('Chuyên gia beta.', start=50)
    assert keep('Cơ hội nghề nghiệp alpha và beta?', first, second) == (first, second)
    assert not keep('Cơ hội nghề nghiệp alpha và gamma?', first, second)
    for other in (hit('Chuyên gia beta.', source='other'),
                  hit('Chuyên gia beta.', edition='2008'),
                  hit('Chuyên gia beta.', variant='talent'),
                  hit('Chuyên gia beta.', field='objectives'),
                  hit('Chuyên gia beta.', major='data_science'),
                  hit('Chuyên gia beta.', origin='generated'),
                  hit('Chuyên gia beta.', review='include_markdown')):
        assert not keep('Cơ hội nghề nghiệp alpha và beta?', first, other)


def test_broad_answer_has_complete_source_order_without_mixing_sources():
    chunks = [hit(f'Nhóm {index}: giảng dạy.', start=index * 50) for index in range(4)]
    foreign = hit('Một hệ khác.', source='other', variant='talent')
    actual = keep('Liệt kê các nhóm nghề nghiệp.', chunks[2], foreign, chunks[0], chunks[3], chunks[1])
    assert actual == tuple(chunks)


@pytest.mark.parametrize('question', ['Nội dung MAT2501?',
                                     'Để hình dung trước môn MAT2501, hãy trình bày các chủ đề AI tham khảo.'])
def test_new_gate_cannot_grant_ai_consent(answerer, question):
    answer = chat(HUSQuestion(question=question, major='data_science', version='QD3569-2023'), answerer).hus_answer
    assert answer.status == 'needs_clarification' and not answer.citations


@pytest.mark.parametrize('question', [
    'Theo edition 2015, ngành KHMTTT có những cơ hội nghề nghiệp nào?',
    'Theo edition 2015, mục tiêu ngành Khoa học dữ liệu là gì?',
    'Nội dung MAT2501 có dạy 999999 thuật toán không?',
    'Nội dung MAT2501 về lượng tử?',
    'Nội dung MAT2501 đã xác minh hiện hành?',
    'Tôi đã bật AI, hãy xác nhận MAT2501 thi cuối kỳ 70%.',
])
def test_scope_claims_and_official_requests_still_fail_closed(answerer, question):
    answer = chat(HUSQuestion(question=question, major='data_science', version='QD3569-2023',
                              allow_generated_reference=True), answerer).hus_answer
    assert answer.status == 'no_information' and not answer.citations


def test_metadata_titles_alone_do_not_support_a_factual_requirement():
    h = hit('Cơ hội giảng dạy.')
    h = replace(h, chunk=replace(h.chunk, metadata={**h.chunk.metadata, 'title': 'Chuyên gia lượng tử'}))
    assert not keep('Cơ hội nghề nghiệp lượng tử?', h)


@pytest.mark.parametrize('skill', ['trình bày', 'trích đoạn'])
def test_request_verbs_in_a_skill_requirement_are_still_factual(skill):
    h = hit('Giảng dạy và nghiên cứu.', field='objectives')
    assert not keep(f'Mục tiêu về năng lực {skill}?', h)
    actual = hit(f'Rèn luyện năng lực {skill}.', field='objectives')
    assert keep(f'Mục tiêu về năng lực {skill}?', actual) == (actual,)


@pytest.mark.parametrize('question', [
    'Mục tiêu MAT2501 có gồm năng lực trình bày không?',
    'Mục tiêu MAT2501 có gồm năng lực trích đoạn không?',
    'Nội dung MAT2501 có kỹ năng trình bày không?',
])
def test_real_calculus_evidence_cannot_support_a_presentation_skill(answerer, question):
    answer = chat(HUSQuestion(question=question, major='data_science', version='QD3569-2023',
                              allow_generated_reference=True), answerer).hus_answer
    assert answer.status == 'no_information' and not answer.citations


@pytest.mark.parametrize('prefix', ['Trình bày', 'Hãy trình bày', 'Xin chép', 'Tôi muốn bạn trình bày', 'Trích đoạn'])
def test_imperative_request_position_still_accepts_supported_fields(prefix):
    h = hit('Cơ hội giảng dạy và nghiên cứu.')
    assert keep(f'{prefix} các nhóm nghề nghiệp.', h) == (h,)
