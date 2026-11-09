"""Source interpretation and single-turn Q&A, independent of course advice."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from app.hus.answering import HUSAnswerer, prerequisite_status
from app.hus.chat import chat
from app.schemas.hus import HUSQuestion
from app.services.hus_service import get_hus_answerer

PACK = Path(__file__).resolve().parents[2] / 'data/hus/evaluation/diagnostic_dev_v4_contracts'
CASES = [json.loads(line) for line in (PACK / 'cases.jsonl').read_text(encoding='utf-8').splitlines()]


@pytest.fixture(scope='module')
def answerer():
    return get_hus_answerer()


def ask(answerer, question, **hints):
    return chat(HUSQuestion(question=question, major='data_science', version='QD3569-2023', **hints), answerer).hus_answer


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['question_id'])
def test_frozen_development_contract(answerer, case):
    answer = chat(HUSQuestion(**case['request']), answerer).hus_answer
    if 'expected_status' in case:
        assert answer.status == case['expected_status']
        assert not answer.facts and not answer.citations
        return
    assert answer.status == 'answered'
    assert answer.facts.get('prerequisite_status') == case['expected_prerequisite_status']
    course = answerer.data.get_f2_course(answer.facts['course_code'], major=answer.major, version=answer.version)
    assert answer.facts['value'] == [r.get('prerequisite_source_text') for r in course.source_rows]
    assert answer.facts['review_status'] == course.review_status
    assert len(answer.citations) == len(course.source_rows)
    if case['expected_prerequisite_status'] == 'unknown':
        assert 'không có tiên quyết' in answer.reply
        assert any('chưa đủ căn cứ' in warning.lower() for warning in answer.warnings)


@pytest.mark.parametrize('question', [
    'MAT3533 có tên gì, bao nhiêu tín chỉ và tiên quyết gì?',
    'MAT3533 có bao nhiêu tín chỉ và học trước môn nào?',
    'Tên đầy đủ và số giờ của MAT3533?',
    'Số tín chỉ và nội dung MAT3533?',
    'MAT3533 có bao nhiêu tín chỉ và thi thế nào?',
    'MAT3533 có bao nhiêu tín chỉ và hướng tới năng lực nào?',
    'MAT3533 có bao nhiêu tín chỉ và học những gì?',
    'MAT3533 có tên gì và mục đích đào tạo là gì?',
    'MAT3533 co bao nhieu tin chi va hoc nhung chuong nao?',
    'MAT3533 co bao nhieu tin chi va hoc   nhung chuong nao?',
])
@pytest.mark.parametrize('hints', [{}, {'dataset': 'f2', 'field': 'credits'},
                                 {'dataset': 'f3', 'field': 'content', 'allow_generated_reference': True}])
def test_multi_field_never_silently_answers_only_one(answerer, question, hints):
    answer = ask(answerer, question, **hints)
    assert answer.status == 'needs_clarification'
    assert not answer.facts and not answer.citations
    assert 'một loại thông tin' in answer.reply


@pytest.mark.parametrize('question', [
    'MAT3533 có bao nhiêu tín chỉ, khối lượng tín chỉ ra sao?',
    'Số tín chỉ MAT3533?',
])
def test_repeated_same_field_is_one_request(answerer, question):
    answer = ask(answerer, question)
    assert answer.status == 'answered' and answer.facts['field'] == 'credits'


@pytest.mark.parametrize('question,field', [
    ('Không hỏi tên môn; MAT3533 có bao nhiêu tín chỉ?', 'credits'),
    ('Không hỏi số tín chỉ MAT3533 mà hỏi tiên quyết là gì?', 'prerequisites'),
    ('Không cần tiên quyết; số giờ MAT3533?', 'hours'),
    ('Khong hoi noi dung, chi hoi tin chi MAT3533?', 'credits'),
    ('Không hỏi mục tiêu, chỉ hỏi tín chỉ MAT3533?', 'credits'),
    ('Không hỏi gợi ý đánh giá, chỉ hỏi tín chỉ MAT3533?', 'credits'),
    ('Không hỏi thi, chỉ hỏi tín chỉ MAT3533?', 'credits'),
])
def test_negated_field_does_not_count_as_an_additional_request(answerer, question, field):
    answer = ask(answerer, question)
    assert answer.status == 'answered' and answer.facts['field'] == field


def test_followup_does_not_inherit_previous_course(answerer):
    assert ask(answerer, 'Số tín chỉ MAT3533?').status == 'answered'
    followup = ask(answerer, 'Môn đó có bao nhiêu tín chỉ?')
    assert followup.status == 'needs_clarification'
    assert not followup.facts and not followup.citations
    course = answerer.data.get_f2_course('MAT3533', major='data_science', version='QD3569-2023')
    assert ask(answerer, f"Môn {course.course['course_name']} có bao nhiêu tín chỉ?").status == 'answered'


@pytest.mark.parametrize('review', ['verified', 'draft_unverified'])
def test_blank_source_is_unknown_even_after_project_review(answerer, monkeypatch, review):
    original = answerer.data.get_f2_course('MAT2400', major='data_science', version='QD3569-2023')
    changed = replace(original, review_status=review)
    monkeypatch.setattr(answerer.data, 'get_f2_course', lambda *args, **kwargs: changed)
    answer = ask(HUSAnswerer(answerer.data), 'Tiên quyết MAT2400?')
    assert answer.facts.get('prerequisite_status') == 'unknown'
    assert answer.facts['value'] == [None]
    assert answer.facts['review_status'] == review


@pytest.mark.parametrize('raw,parse,external,conflict,expected', [
    ([None, 'MAT2505'], 'parsed', (), False, 'unknown'),
    (['MAT2505'], 'unparsed', (), False, 'unresolved'),
    (['MAT2505'], 'ambiguous', (), False, 'unresolved'),
    (['MAT2505'], 'parsed', ('MAT9999',), False, 'unresolved'),
    (['MAT2505', 'MAT2301'], 'parsed', (), False, 'conflict'),
    (['MAT2505'], 'parsed', ('MAT9999',), True, 'conflict'),
])
def test_source_status_does_not_hide_ambiguity(answerer, raw, parse, external, conflict, expected):
    original = answerer.data.get_f2_course('MAT1202', major='data_science', version='QD3569-2023')
    rows = tuple({**original.source_rows[0], 'prerequisite_source_text': value,
                  'prerequisite_parse_status': parse} for value in raw)
    changed = replace(original, source_rows=rows, unresolved_prerequisites=external,
                      has_prerequisite_conflict=conflict)
    assert prerequisite_status(changed) == expected
    assert [row['prerequisite_source_text'] for row in changed.source_rows] == raw


def test_basic_help_explains_single_turn(answerer):
    answer = chat(HUSQuestion(question='Hướng dẫn sử dụng?', major='data_science'), answerer)
    assert 'mỗi lượt' in answer.reply.lower() and 'mã hoặc tên' in answer.reply.lower()
