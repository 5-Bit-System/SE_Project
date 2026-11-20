"""Exposed development regressions, never an independent holdout acceptance."""

import json
from pathlib import Path

import pytest

from app.hus.answering import HUSAnswerer
from app.hus.chat import chat
from app.hus.rag_loader import HUSRAGData
from app.schemas.hus import HUSQuestion
from tools.hus_rag_metrics import citation_scope, facts_match

PACK = Path(__file__).resolve().parents[2] / "data/hus/evaluation/diagnostic_dev_v1"
QUESTIONS = [json.loads(line) for line in (PACK / "questions.jsonl").read_text(encoding="utf-8").splitlines()]
GOLD = [json.loads(line) for line in (PACK / "gold.jsonl").read_text(encoding="utf-8").splitlines()]


@pytest.fixture(scope="module")
def answerer():
    return HUSAnswerer(HUSRAGData.load_current())


@pytest.mark.parametrize("question,target", list(zip(QUESTIONS, GOLD, strict=True)),
                         ids=[q["question_id"] for q in QUESTIONS])
def test_exposed_dev_requests_preserve_facts_scope_and_consent(answerer, question, target):
    answer = chat(HUSQuestion(**question["request"]), answerer).hus_answer
    assert answer is not None
    assert answer.status == target["expected_status"], answer.reply
    if target["expected_status"] != "answered":
        assert not answer.facts and not answer.citations
        return
    assert answer.dataset == target["expected_dataset"]
    assert answer.citations
    if answer.dataset == "f2":
        assert facts_match(target, answer.facts)
    if answer.dataset == "f3":
        assert question["request"]["allow_generated_reference"] is True
        assert all(c.display_label == "kiến thức AI" and c.open_url is None for c in answer.citations)
    assert all(c.dataset == answer.dataset and citation_scope(c.model_dump())["major"] == question["request"]["major"]
               for c in answer.citations)


def test_explicit_decision_in_question_cannot_borrow_selected_version(answerer):
    question = HUSQuestion(question="Số tín chỉ MAT3533 theo chương trình QD3565-2023?",
                           major="data_science", version="QD3569-2023")
    answer = chat(question, answerer).hus_answer
    assert answer.status == "no_information"
    assert not answer.facts and not answer.citations


@pytest.mark.parametrize("question", [
    "Ngành KHDL có hệ tài năng không?",
    "Ngành KHDL có chương trình tài năng không?",
    "Ngành KHDL có hệ cử nhân tài năng không?",
    "Ngành KHDL có chương trình cử nhân hai năm không?",
])
def test_specific_program_qualifiers_require_actual_quote_support(answerer, question):
    answer = chat(HUSQuestion(question=question, major="data_science", version="QD3569-2023"), answerer).hus_answer
    assert answer.status == "no_information"
    assert not answer.citations and not answer.facts
