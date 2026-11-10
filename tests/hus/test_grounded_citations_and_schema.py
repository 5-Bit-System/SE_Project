"""Unit and contract tests for inline citations [1], [2] and chat response schema synchronization."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.hus.chat import HUSChatReply, basic_reply, chat
from app.hus.llm_answerer import generate_grounded_answer
from app.schemas.hus import HUSCitation, HUSQuestion
from app.services.hus_service import get_hus_answerer


@pytest.fixture(scope="module")
def answerer():
    return get_hus_answerer()


def test_hus_chat_reply_schema_defaults_and_validation():
    reply = HUSChatReply(mode="hus_rag", reply="Extractive text")
    assert reply.mode == "hus_rag"
    assert reply.reply == "Extractive text"
    assert reply.hus_answer is None
    assert set(reply.model_dump()) == {"mode", "reply", "hus_answer"}

    reply_basic = HUSChatReply(mode="basic_chat", reply="Xin chào")
    assert reply_basic.mode == "basic_chat"
    assert reply_basic.reply == "Xin chào"
    assert set(reply_basic.model_dump()) == {"mode", "reply", "hus_answer"}

    with pytest.raises(Exception):
        HUSChatReply(mode="invalid_mode", reply="test")  # type: ignore[arg-type]


def test_chat_returns_basic_chat(answerer):
    req = HUSQuestion(question="Xin chào", major="computer_science")
    res = chat(req, answerer)
    assert res.mode == "basic_chat"
    assert res.reply == basic_reply("Xin chào")
    assert set(res.model_dump()) == {"mode", "reply", "hus_answer"}


def test_chat_sets_extractive_mode_when_llm_disabled(answerer, monkeypatch):
    monkeypatch.setattr(
        "app.hus.llm_answerer.get_settings",
        lambda: SimpleNamespace(
            hus_rag_llm_enabled=False,
            gemini_api_key="",
            hus_rag_llm_model="gemini-3.5-flash-lite",
            gemini_base_url="",
            gemini_model="gemini-2.5-flash",
            recommendation_llm_enabled=False,
        ),
    )
    req = HUSQuestion(
        question="Môn CSDL bao nhiêu tín?",
        major="computer_science",
        version="QD3568-2023",
    )
    res = chat(req, answerer)
    assert res.mode == "hus_rag"
    assert res.hus_answer is not None
    assert res.hus_answer.status == "answered"
    assert res.reply == res.hus_answer.reply
    assert set(res.model_dump()) == {"mode", "reply", "hus_answer"}


def test_generate_grounded_answer_prompt_and_citations_sync(answerer, monkeypatch):
    captured_prompts: list[str] = []

    def fake_call_gemini_llm(prompt: str, **kwargs) -> str:
        captured_prompts.append(prompt)
        return "Thông tin học phần:\n- Mã học phần: MAT3507 [1]\nNội dung môn học nghiên cứu về CSDL quan hệ [2]."

    monkeypatch.setattr("app.hus.llm_answerer.call_gemini_llm", fake_call_gemini_llm)
    monkeypatch.setattr(
        "app.hus.llm_answerer.get_settings",
        lambda: SimpleNamespace(
            hus_rag_llm_enabled=True,
            gemini_api_key="test-key-mock",
            hus_rag_llm_model="gemini-3.5-flash-lite",
            gemini_base_url="",
            gemini_model="gemini-2.5-flash",
            recommendation_llm_enabled=False,
        ),
    )

    req = HUSQuestion(
        question="Môn CSDL học gì?",
        major="computer_science",
        version="QD3568-2023",
        allow_generated_reference=True,
    )
    base_answer = answerer.answer(req)
    result = generate_grounded_answer(req, answerer, answer=base_answer)

    assert result is not None
    generated_text, citations = result

    # 1. Check return format
    assert isinstance(generated_text, str)
    assert "[1]" in generated_text
    assert isinstance(citations, list)
    assert len(citations) >= 1
    assert all(isinstance(c, HUSCitation) for c in citations)

    # 2. Check prompt instructions
    assert len(captured_prompts) == 1
    prompt = captured_prompts[0]
    expected_instruction = (
        "Khi trích dẫn hoặc sử dụng luận điểm từ các đoạn trích dẫn tài liệu ở mục B, "
        "hãy gắn số thứ tự trích dẫn dạng [1], [2],... tương ứng với số thứ tự của đoạn trích dẫn vào cuối câu hoặc mệnh đề."
    )
    assert expected_instruction in prompt

    # 3. Check citation IDs start from 1 and are sequential
    citation_ids = [c.citation_id for c in citations]
    assert citation_ids[0] == "1"
    assert len(citation_ids) == len(set(citation_ids))  # all distinct


def test_chat_syncs_citations_from_llm(answerer, monkeypatch):
    mock_llm_text = "Học phần MAT3507 có 4 tín chỉ [1]. Nội dung về CSDL quan hệ và chuẩn hóa dữ liệu [2]."

    def fake_generate_grounded_answer(request, answerer, answer=None):
        citations = []
        if answer and answer.citations:
            citations.extend(answer.citations)
        return (mock_llm_text, citations)

    monkeypatch.setattr("app.hus.chat.generate_grounded_answer", fake_generate_grounded_answer)

    req = HUSQuestion(
        question="Môn CSDL bao nhiêu tín?",
        major="computer_science",
        version="QD3568-2023",
    )
    res = chat(req, answerer)

    assert res.mode == "hus_rag"
    assert res.reply == mock_llm_text
    assert res.hus_answer is not None
    assert res.hus_answer.citations == answerer.answer(req).citations
    assert set(res.model_dump()) == {"mode", "reply", "hus_answer"}
