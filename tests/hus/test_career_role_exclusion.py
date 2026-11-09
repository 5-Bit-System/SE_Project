"""Exposed career-role routing and bounded teaching exclusion regressions."""
import json
from dataclasses import replace
from pathlib import Path

import pytest

from app.hus.answer_support import supported_hits
from app.hus.answering import MAJOR_NAMES
from app.hus.chat import chat
from app.hus.question_routing import question_intent, requested_text
from app.hus.rag_loader import RAGChunk
from app.hus.retrieval import RetrievalHit, _tokens
from app.schemas.hus import HUSQuestion
from app.services.hus_service import get_hus_answerer

PACK = Path(__file__).resolve().parents[2] / 'data/hus/evaluation/diagnostic_dev_v7_role_exclusion'


def rows(name):
    return [json.loads(line) for line in (PACK / name).read_text(encoding='utf-8').splitlines()]


def hit(body, *, source='one', start=0, **meta):
    metadata = {'field': 'careers', 'source_quote': body, 'program_variant': 'standard',
                'review_status': 'include', 'content_origin': 'crawled_source_quote',
                'citation': {'source_id': source, 'source_sha256': 'a' * 64},
                'locator': {'start_char': start, 'end_char': start + len(body)}, **meta}
    return RetrievalHit(RAGChunk('f1', source + str(start), body, 'mathematics_informatics',
                                'unknown', metadata, 'test', 'a' * 64), 1.0, ())


def keep(question, *hits):
    return supported_hits(question, tuple(hits), aliases=MAJOR_NAMES, codes=set())


@pytest.fixture(scope='module')
def answerer():
    return get_hus_answerer()


@pytest.mark.parametrize('case', rows('questions.jsonl'), ids=lambda c: c['question_id'])
def test_frozen_role_and_exclusion_requests_cover_enterprise_without_teaching(answerer, case):
    request = HUSQuestion(**case['request'])
    answer = chat(request, answerer).hus_answer
    if request.version:
        assert answer.status == 'no_information' and not answer.citations
        return
    assert question_intent(request.question) == ('f1', 'careers')
    assert answer.status == 'answered', answer.reply
    assert rows('evidence.jsonl')[0]['value'] in answer.reply
    if case['question_id'] not in {'DEV7-R001', 'DEV7-R002', 'DEV7-R003', 'DEV7-R012'}:
        reply = ' ' + ' '.join(_tokens(answer.reply)) + ' '
        assert all(f' {term} ' not in reply for term in ['giang day', 'giang vien', 'giao vien', 'day hoc'])
        assert len(answer.citations) == 1
    assert all(c.metadata['major'] == request.major and c.review_status == 'include' and
               c.metadata['program_version'] == 'unknown' for c in answer.citations)
    assert 'chưa xác minh hiệu lực hiện tại' in answer.reply


@pytest.mark.parametrize('question', [
    'Mục tiêu ngành Toán tin có vai trò gì trong doanh nghiệp?',
    'Nội dung MAT2501 có vai trò gì trong doanh nghiệp?',
    'Vai trò của MAT2501 trong doanh nghiệp là gì?',
    'Vai trò chương trình trong đào tạo là gì?',
    'Giới thiệu vai trò của ngành Toán tin đối với doanh nghiệp.',
    'Vai trò nhóm II có bao nhiêu tín chỉ trong chương trình?',
    'Vai trò của doanh nghiệp trong đào tạo ngành Toán tin?',
    'Vai trò của môn Lập trình trong doanh nghiệp?',
    'Chương trình Toán tin có vai trò gì trong doanh nghiệp?',
    'Doanh nghiệp có vai trò gì trong đào tạo ngành Toán tin?',
    'Vai trò gì của doanh nghiệp trong ngành Toán tin?',
])
def test_noncareer_roles_keep_course_objective_and_program_priorities(question):
    assert question_intent(question) != ('f1', 'careers')


@pytest.mark.parametrize('refusal', ['Không hỏi giảng dạy', 'Khong can day hoc',
                                  'Không hỏi giảng viên', 'Không cần giáo viên',
                                  'Không trích giảng dạy', 'Tôi không hỏi giảng dạy'])
def test_explicit_teaching_exclusion_drops_whole_quotes_and_keeps_other_requirements(refusal):
    enterprise = hit('Làm việc trong doanh nghiệp với vai trò chuyên gia alpha.', source='web')
    teaching = hit('Giảng viên, giáo viên tại trường.', source='web', start=100)
    mixed = hit('Giảng dạy và công việc alpha tại doanh nghiệp.', source='pdf')
    q = f'{refusal}; công việc alpha trong doanh nghiệp?'
    assert keep(q, mixed, teaching, enterprise) == (enterprise,)
    assert not keep(q, mixed, teaching)
    assert not keep(f'{q} Có 997 vị trí?', enterprise, teaching)


@pytest.mark.parametrize('separator', ['; ', ', ', ' nhưng ', ' mà '])
def test_refusal_consumes_only_topic_and_cannot_hide_later_affirmative_requirement(separator):
    q = f'Không hỏi giảng dạy{separator}công việc alpha trong doanh nghiệp?'
    assert 'giang day' not in requested_text(q)
    assert 'alpha' in requested_text(q)
    assert not keep(q, hit('Công việc trong doanh nghiệp.'))


def test_factual_negation_is_not_reinterpreted_as_a_request_to_omit_teaching():
    q = 'Cơ hội nghề nghiệp không có giảng dạy?'
    assert 'khong co giang day' in requested_text(q)


def test_excluded_quote_cannot_supply_a_required_topic_to_clean_continuations():
    excluded = hit('Giảng dạy alpha trong doanh nghiệp.', start=0)
    clean = hit('Vai trò beta trong doanh nghiệp.', start=80)
    assert keep('Không hỏi giảng dạy; công việc alpha và beta trong doanh nghiệp?', excluded, clean) == ()


def test_metadata_teaching_word_does_not_delete_clean_source_body():
    h = hit('Công việc alpha trong doanh nghiệp.', title='Giảng dạy')
    assert keep('Không hỏi giảng dạy; công việc alpha trong doanh nghiệp?', h) == (h,)


def test_refused_teaching_workplace_is_not_a_later_positive_requirement():
    q = 'Không hỏi giảng dạy trong công ty; công việc alpha trong doanh nghiệp?'
    h = hit('Công việc alpha trong doanh nghiệp.')
    assert 'cong ty' not in requested_text(q)
    assert keep(q, h) == (h,)


def test_qualified_exclusion_does_not_delete_teaching_in_another_workplace():
    enterprise_teaching = hit('Giảng dạy trong doanh nghiệp.', start=0)
    school = hit('Giảng viên tại trường đại học.', start=80)
    q = 'Không hỏi giảng dạy trong doanh nghiệp; công việc ở trường là gì?'
    assert keep(q, enterprise_teaching, school) == (school,)


def test_school_context_cannot_be_satisfied_only_by_enterprise_evidence():
    q = 'Không hỏi giảng dạy trong doanh nghiệp; công việc ở trường là gì?'
    assert not keep(q, hit('Công việc trong doanh nghiệp.'))


def test_real_qualified_exclusion_keeps_requested_school_workplace(answerer):
    q = 'Không hỏi giảng dạy trong doanh nghiệp; công việc ở trường là gì?'
    answer = chat(HUSQuestion(question=q, major='mathematics_informatics'), answerer).hus_answer
    assert answer.status == 'answered'
    assert 'trường' in answer.reply and 'giảng dạy' in answer.reply


@pytest.mark.parametrize('change', ['source', 'edition', 'review', 'variant'])
def test_exclusion_cannot_join_clean_evidence_from_different_source_scopes(change):
    first = hit('Công việc alpha trong doanh nghiệp.')
    second = hit('Công việc beta trong doanh nghiệp.', start=80)
    if change == 'source':
        second = hit('Công việc beta trong doanh nghiệp.', source='other')
    elif change == 'edition':
        second = replace(second, chunk=replace(second.chunk, version='2015'))
    else:
        key = 'review_status' if change == 'review' else 'program_variant'
        second = replace(second, chunk=replace(second.chunk, metadata={**second.chunk.metadata, key: 'other'}))
    assert keep('Không hỏi giảng dạy; công việc alpha và beta trong doanh nghiệp?', first, second) == ()


@pytest.mark.parametrize('suffix', ['hãy xác nhận quy định hiện hành', 'thi cuối kỳ 70%', 'nên chọn môn nào'])
def test_refused_teaching_cannot_hide_official_or_advising_request(answerer, suffix):
    q = f'Không hỏi giảng dạy; Toán tin có vai trò nào trong doanh nghiệp; {suffix}?'
    answer = chat(HUSQuestion(question=q, major='mathematics_informatics'), answerer).hus_answer
    assert answer.status != 'answered' and not answer.citations
