"""Exposed DEV-Q027: preserve requested workplace inside one source group."""
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

PACK = Path(__file__).resolve().parents[2] / 'data/hus/evaluation/diagnostic_dev_v6_career_context_r2'


def keep(question, *hits):
    return supported_hits(question, tuple(hits), aliases=MAJOR_NAMES, codes=set())


def hit(body, *, source='one', start=0, edition='unknown', **meta):
    metadata = {'field': 'careers', 'source_quote': body, 'program_variant': 'unknown',
                'review_status': 'include', 'content_origin': 'crawled_source_quote',
                'citation': {'source_id': source, 'source_sha256': 'a' * 64},
                'locator': {'start_char': start, 'end_char': start + len(body)}, **meta}
    return RetrievalHit(RAGChunk('f1', source + str(start), body, 'mathematics_informatics',
                                edition, metadata, 'test', 'a' * 64), 1.0, ())


@pytest.fixture(scope='module')
def answerer():
    return get_hus_answerer()


@pytest.mark.parametrize('case', [json.loads(line) for line in (PACK / 'questions.jsonl')
                         .read_text(encoding='utf-8').splitlines()], ids=lambda q: q['question_id'])
def test_exposed_enterprise_careers_keep_roles_and_source_scope(answerer, case):
    request = HUSQuestion(**case['request'])
    answer = chat(request, answerer).hus_answer
    if request.version:
        assert answer.status == 'no_information' and not answer.citations
        return
    assert answer.status == 'answered', answer.reply
    evidence = json.loads((PACK / 'evidence.jsonl').read_text(encoding='utf-8').splitlines()[0])
    assert evidence['value'] in answer.reply
    for role in ['lập trình viên', 'phân tích dữ liệu', 'thống kê', 'phát triển thuật toán']:
        assert role in answer.reply
    hits = answerer.retriever.search(request.question, dataset='f1', major=request.major,
                                    field='careers', top_k=5)
    assert {c.metadata['chunk_id'] for c in answer.citations} <= {h.chunk.chunk_id for h in hits}
    assert all(c.metadata['major'] == request.major and c.review_status == 'include' for c in answer.citations)
    assert all(c.metadata['program_version'] == 'unknown' for c in answer.citations)
    assert 'chưa xác minh hiệu lực hiện tại' in answer.reply


@pytest.mark.parametrize('workplace', ['doanh nghiệp', 'công ty', 'doanh nghiep', 'cong ty'])
def test_workplace_body_is_required_before_selecting_a_source(workplace):
    generic = hit('Vị trí việc làm: giảng dạy tại các trường.', source='generic')
    exact = hit(f'Làm việc tại {workplace} với vai trò lập trình viên.', source='enterprise')
    assert keep(f'Ra trường có công việc nào trong {workplace}?', generic, exact) == (exact,)
    assert keep(f'Ra trường có công việc nào trong {workplace}?', generic) == ()


@pytest.mark.parametrize('metadata', [{'title': 'Nghề nghiệp trong doanh nghiệp'},
                                     {'course_name': 'doanh nghiệp'},
                                     {'source_url': 'https://example.org/doanh-nghiep'}])
def test_metadata_or_scattered_words_cannot_supply_workplace(metadata):
    h = hit('Kinh doanh; giảng dạy chuyên nghiệp.', **metadata)
    assert keep('Công việc nào trong doanh nghiệp?', h) == ()


def test_context_and_specific_roles_can_span_one_source_group_in_source_order():
    context = hit('Làm việc tại các doanh nghiệp.', start=10)
    roles = hit('Vai trò: chuyên gia alpha.', start=70)
    generic = hit('Cơ hội nghề nghiệp: chuyên gia alpha.', source='generic')
    assert keep('Công việc alpha trong doanh nghiệp?', generic, roles, context) == (context, roles)


@pytest.mark.parametrize('change', ['source', 'version', 'variant', 'review', 'major', 'field', 'origin', 'hash'])
def test_context_cannot_be_borrowed_across_source_scopes(change):
    context = hit('Làm việc tại các doanh nghiệp.', start=10)
    roles = hit('Vai trò: chuyên gia alpha.', start=70)
    if change == 'source':
        context = hit('Làm việc tại các doanh nghiệp.', source='other', start=10)
    elif change in {'version', 'major'}:
        context = replace(context, chunk=replace(context.chunk, **{change: 'other'}))
    else:
        key = {'variant': 'program_variant', 'review': 'review_status', 'field': 'field',
               'origin': 'content_origin', 'hash': 'citation'}[change]
        value = {'source_id': 'one', 'source_sha256': 'b' * 64} if change == 'hash' else 'other'
        context = replace(context, chunk=replace(context.chunk, metadata={**context.chunk.metadata, key: value}))
    assert keep('Công việc alpha trong doanh nghiệp?', context, roles) == ()


def test_workplace_does_not_erase_other_domain_requirements_or_edition():
    h = hit('Làm việc trong doanh nghiệp với vai trò lập trình viên.')
    assert not keep('Công việc trong doanh nghiệp về lượng tử?', h)
    assert not keep('Có 997 công việc trong doanh nghiệp?', h)
    assert not keep('Theo edition 2015, công việc nào trong doanh nghiệp?', h)


def test_negated_workplace_is_not_a_positive_requirement():
    h = hit('Giảng dạy tại trường đại học.')
    assert keep('Không hỏi công ty đang tuyển; cơ hội nghề nghiệp là gì?', h) == (h,)


def test_workplace_rule_is_bounded_to_career_field():
    h = hit('Mục tiêu rèn luyện nền tảng kiến thức.', field='objectives')
    assert keep('Mục tiêu ngành theo tài liệu doanh nghiệp?', h) == (h,)


@pytest.mark.parametrize('refusal', ['Không hỏi công ty', 'Khong hoi doanh nghiep',
                                  'Không cần công việc trong doanh nghiệp',
                                  'Không yêu cầu về công ty'])
def test_refused_workplace_does_not_become_a_positive_context(refusal):
    # Keep all other lexical requirements supported; this test isolates only
    # whether the refused workplace is incorrectly made a positive constraint.
    teaching = hit('Cơ hội giảng dạy theo yêu cầu tại trường.', source='teaching')
    enterprise = hit('Công việc giảng dạy theo yêu cầu trong doanh nghiệp.', source='enterprise')
    assert keep(f'{refusal}; cơ hội nghề nghiệp giảng dạy nào?', teaching, enterprise) == (teaching,)


@pytest.mark.parametrize('separator', ['; ', ', ', ' mà '])
def test_refusing_one_workplace_does_not_erase_a_later_positive_request(separator):
    company = hit('Công việc trong công ty.', source='company')
    enterprise = hit('Công việc trong doanh nghiệp.', source='enterprise')
    question = f'Không hỏi công ty{separator}hỏi công việc trong doanh nghiệp?'
    assert keep(question, company, enterprise) == (enterprise,)
    assert keep(question, company) == ()


def test_factual_negation_is_not_treated_as_a_refused_request():
    h = hit('Giảng dạy tại trường.')
    assert keep('Công việc không có doanh nghiệp?', h) == ()


@pytest.mark.parametrize('workplace', ['cong ty', 'doanh nghiep'])
def test_real_teaching_request_ignores_only_the_refused_workplace(answerer, workplace):
    question = f'Khong hoi {workplace}; Toan tin co co hoi nghe nghiep giang day nao?'
    answer = chat(HUSQuestion(question=question, major='mathematics_informatics'), answerer).hus_answer
    assert answer.status == 'answered'
    assert all(c.metadata['program_version'] == '2015' for c in answer.citations)
    assert 'giảng dạy' in answer.reply
