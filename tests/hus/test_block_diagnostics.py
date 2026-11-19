"""Block reasons must identify the real stage, without provider calls or secrets."""
import logging

import pytest
from fastapi.testclient import TestClient

from app.hus import answering, demo
from app.hus.answering import HUSAnswerer
from app.hus.chat import chat
from app.schemas.hus import HUSQuestion
from app.services.hus_service import get_hus_answerer


@pytest.fixture(scope='module')
def answerer():
    return get_hus_answerer()


def ask(answerer, question):
    return chat(HUSQuestion(question=question, major='data_science', version='QD3569-2023'), answerer).hus_answer


def test_wrong_major_suggests_exact_major_without_search(answerer, monkeypatch):
    monkeypatch.setattr(answerer.retriever, 'search', lambda *a, **k: pytest.fail('Wrong scope searched'))
    answer = ask(answerer, 'Ngành khoa học máy tính có bao nhiêu môn học?')
    assert answer.diagnostic.code == 'scope_conflict'
    assert answer.diagnostic.suggested_major == 'computer_science'
    assert 'Khoa học dữ liệu' in answer.reply and 'Khoa học máy tính và thông tin' in answer.reply
    assert not answer.citations


@pytest.mark.parametrize('question,code', [
    ('Tôi muốn biết vài điều', 'routing_unknown'),
    ('Ngành khoa học dữ liệu có bao nhiêu môn bắt buộc?', 'unsupported_operation'),
    ('So sánh tín chỉ MAT3533 và MAT3534', 'unsupported_operation'),
])
def test_unknown_and_unsupported_are_distinct(answerer, question, code):
    assert ask(answerer, question).diagnostic.code == code


def test_empty_retrieval_is_not_support_rejection(answerer, monkeypatch):
    monkeypatch.setattr(answerer.retriever, 'search', lambda *a, **k: ())
    assert ask(answerer, 'Giới thiệu ngành').diagnostic.code == 'retrieval_empty'


@pytest.mark.parametrize('policy', ['legacy', 'focused'])
def test_missing_assessment_names_the_missing_field(answerer, policy):
    request = HUSQuestion(question='MAT2300 thi gi?', major='mathematics', version='QD3565-2023',
                          allow_generated_reference=True)
    result = HUSAnswerer(answerer.data, answer_policy=policy).answer(request)
    assert result.status == 'no_information' and result.dataset == 'f3'
    assert result.diagnostic.code == 'retrieval_empty'
    assert 'dữ liệu đánh giá' in result.reply
    assert 'đề cương' in result.reply
    assert not result.facts and not result.citations


def test_retrieved_but_unsupported_has_own_label(answerer, monkeypatch):
    monkeypatch.setattr(answering, 'supported_hits', lambda *a, **k: ())
    assert ask(answerer, 'Giới thiệu ngành').diagnostic.code == 'evidence_rejected'


def test_answered_contract_does_not_gain_diagnostic(answerer):
    answer = ask(answerer, 'MAT3533 có bao nhiêu tín chỉ?')
    assert answer.status == 'answered' and answer.facts['value'] == 3
    assert 'diagnostic' not in answer.model_dump(mode='json')


def test_api_logs_only_safe_code(answerer, monkeypatch, caplog):
    monkeypatch.setenv('HUS_LLM_AUTO', 'false')
    monkeypatch.setattr(demo, 'current_answerer', lambda: answerer)
    caplog.set_level(logging.INFO, logger='hus.diagnostics')
    with TestClient(demo.app) as client:
        result = client.post('/hus/chat', json={'question': 'Tôi muốn biết vài điều secret-test-only',
                                               'major': 'data_science', 'version': 'QD3569-2023'})
    assert result.json()['hus_answer']['diagnostic']['code'] == 'routing_unknown'
    logs = [r.getMessage() for r in caplog.records if r.name == 'hus.diagnostics']
    assert logs == ['hus_chat_block code=routing_unknown']
    assert 'secret-test-only' not in '\n'.join(logs)
