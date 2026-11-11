"""Phase 2 integration tests: Top-K retrieval bundle, course alias answering, semantic routing, and CLI inspector."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.hus.chat import chat
from app.hus.demo import app
from app.schemas.hus import HUSQuestion, HUSRetrievalBundle
from app.services.hus_service import get_hus_answerer
from tools import inspect_hus_topk


@pytest.fixture(scope="module")
def answerer():
    return get_hus_answerer()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize(
    "question,major,version,expected_code,expected_dataset,expected_field,expected_value",
    [
        ("Môn CSDL bao nhiêu tín?", "computer_science", "QD3568-2023", "MAT3507", "f2", "credits", 4),
        ("Điều kiện tiên quyết của GT2 là gì?", "computer_science", "QD3568-2023", "MAT2502", "f2", "prerequisites", ["MAT2501"]),
        ("Môn ĐSTT học mấy tiết?", "computer_science", "QD3568-2023", "MAT2400", "f2", "hours", {"lecture": 50, "practice": 50, "self_study": 150}),
        ("Môn GT1 có bao nhiêu tín chỉ?", "computer_science", "QD3568-2023", "MAT2501", "f2", "credits", 4),
        ("Môn XSTK ở ngành KHDL bao nhiêu tín?", "data_science", "QD3569-2023", "MAT2323", "f2", "credits", 4),
        ("Học phần MMT bao nhiêu tc?", "computer_science", "QD3568-2023", "MAT3506", "f2", "credits", 3),
        ("Môn CNPM có số tín chỉ là bao nhiêu?", "computer_science", "QD3568-2023", "MAT1207", "f2", "credits", 3),
        ("Môn Giải tích I bao nhiêu tín?", "computer_science", "QD3568-2023", "MAT2501", "f2", "credits", 4),
    ],
)
def test_answerer_resolves_course_aliases_for_f2_facts(
    answerer,
    question,
    major,
    version,
    expected_code,
    expected_dataset,
    expected_field,
    expected_value,
):
    request = HUSQuestion(question=question, major=major, version=version)
    ans = chat(request, answerer).hus_answer
    assert ans is not None
    assert ans.status == "answered"
    assert ans.dataset == expected_dataset
    assert ans.facts["course_code"] == expected_code
    assert ans.facts["field"] == expected_field
    assert ans.facts["value"] == expected_value


@pytest.mark.parametrize(
    "question,expected_code,expected_field",
    [
        ("Nội dung môn TTNT là gì?", "MAT1206E", "content"),
        ("Môn CSDL học gì?", "MAT3507", "content"),
        ("Mục tiêu môn GT1 là gì?", "MAT2501", "objectives"),
        ("Gợi ý đánh giá môn ĐSTT là gì?", "MAT2400", "suggested_assessment"),
    ],
)
def test_answerer_resolves_course_aliases_for_f3_with_support_gate(
    answerer,
    question,
    expected_code,
    expected_field,
):
    request = HUSQuestion(
        question=question,
        major="computer_science",
        version="QD3568-2023",
        allow_generated_reference=True,
    )
    ans = chat(request, answerer).hus_answer
    assert ans is not None
    assert ans.status == "answered"
    assert ans.dataset == "f3"
    assert ans.citations
    assert ans.citations[0].metadata.get("course_code") == expected_code
    assert ans.citations[0].metadata.get("field") == expected_field


def test_ambiguous_course_alias_in_mathematics_requires_clarification(answerer):
    # In Mathematics (QD3565-2023), Đại số tuyến tính 1, 2, 3 (MAT2300, MAT2301, MAT3339) exist.
    request = HUSQuestion(
        question="Môn ĐSTT bao nhiêu tín?",
        major="mathematics",
        version="QD3565-2023",
    )
    ans = chat(request, answerer).hus_answer
    assert ans is not None
    assert ans.status == "needs_clarification"
    assert not ans.facts and not ans.citations

    # When disambiguated as ĐSTT 1 or Đại số tuyến tính I, it answers cleanly.
    req_disambiguated = HUSQuestion(
        question="Môn ĐSTT 1 bao nhiêu tín?",
        major="mathematics",
        version="QD3565-2023",
    )
    ans_disambiguated = chat(req_disambiguated, answerer).hus_answer
    assert ans_disambiguated is not None
    assert ans_disambiguated.status == "answered"
    assert ans_disambiguated.facts["course_code"] == "MAT2300"


@pytest.mark.parametrize(
    "question",
    [
        "Khung chương trình chia thành những khối kiến thức nào?",
        "Khung chương trình chia thành những khối nào?",
        "Cấu trúc khung chương trình gồm các nhóm nào?",
    ],
)
def test_curriculum_framework_group_questions_route_to_program_groups(answerer, question):
    request = HUSQuestion(
        question=question,
        major="computer_science",
        version="QD3568-2023",
    )
    ans = chat(request, answerer).hus_answer
    assert ans is not None
    assert ans.status == "answered"
    assert ans.dataset == "f2"
    assert ans.facts["field"] == "program_groups"
    assert len(ans.facts["value"]) == 9


def test_retrieve_context_f1_careers_and_introduction(answerer):
    req = HUSQuestion(
        question="Sinh viên tốt nghiệp ngành Khoa học máy tính ra trường làm nghề gì?",
        major="computer_science",
    )
    bundle = answerer.retrieve_context(req, top_k=5)
    assert isinstance(bundle, HUSRetrievalBundle)
    assert bundle.dataset == "f1"
    assert bundle.field == "careers"
    assert bundle.intent_source in {"rule", "semantic"}
    assert len(bundle.top_k_chunks) >= 1
    assert bundle.top_k_chunks[0].dataset == "f1"
    assert bundle.top_k_chunks[0].field == "careers"
    assert bundle.top_k_chunks[0].passed_support_gate is True
    assert bundle.top_k_chunks[0].citation is not None
    assert "program" in bundle.structured_data


def test_retrieve_context_f2_course_alias_populates_structured_course_and_f3_chunks(answerer):
    req = HUSQuestion(
        question="Môn CSDL bao nhiêu tín?",
        major="computer_science",
        allow_generated_reference=True,
    )
    bundle = answerer.retrieve_context(req, top_k=3)
    assert bundle.dataset == "f2"
    assert bundle.field == "credits"
    assert bundle.resolved_course_code == "MAT3507"
    assert len(bundle.resolved_courses) == 1
    assert bundle.resolved_courses[0]["course_code"] == "MAT3507"
    assert bundle.resolved_courses[0]["match_type"] == "alias"
    assert "course" in bundle.structured_data
    assert bundle.structured_data["course"]["course_code"] == "MAT3507"
    assert bundle.structured_data["course"]["credits"] == 4
    assert len(bundle.top_k_chunks) == 3
    assert all(c.course_code == "MAT3507" for c in bundle.top_k_chunks)


def test_retrieve_context_f3_paraphrased_course_content_query(answerer):
    req = HUSQuestion(
        question="Môn TTNT dạy những kiến thức cốt lõi gì?",
        major="computer_science",
        allow_generated_reference=True,
    )
    bundle = answerer.retrieve_context(req, top_k=3)
    assert bundle.resolved_course_code == "MAT1206E"
    assert bundle.dataset == "f3"
    assert bundle.field == "content"
    assert bundle.intent_source == "semantic"
    assert bundle.intent_confidence >= 0.38
    assert len(bundle.top_k_chunks) >= 1
    assert bundle.top_k_chunks[0].course_code == "MAT1206E"
    assert bundle.top_k_chunks[0].field == "content"


def test_retrieve_context_ambiguous_course_alias_lists_candidate_courses(answerer):
    req = HUSQuestion(
        question="Môn ĐSTT bao nhiêu tín?",
        major="mathematics",
    )
    bundle = answerer.retrieve_context(req, top_k=5)
    assert bundle.resolved_course_code is None
    assert [c["course_code"] for c in bundle.resolved_courses] == ["MAT2300", "MAT2301", "MAT3339"]
    assert "candidate_courses" in bundle.structured_data


def test_retrieve_context_out_of_scope_returns_none_intent_and_empty_chunks(answerer):
    req = HUSQuestion(
        question="Hãy xếp hạng và chọn môn giúp mình kỳ tới 20 tín chỉ.",
        major="computer_science",
    )
    bundle = answerer.retrieve_context(req, top_k=5)
    assert bundle.intent_source == "none"
    assert bundle.dataset is None
    assert bundle.top_k_chunks == []


def test_retrieve_context_broad_fallback_returns_ranked_chunks(answerer):
    req = HUSQuestion(
        question="Thông tin thêm về MAT3507",
        major="computer_science",
        allow_generated_reference=True,
    )
    bundle = answerer.retrieve_context(req, top_k=3)
    assert bundle.resolved_course_code == "MAT3507"
    assert len(bundle.top_k_chunks) == 3
    assert all(c.course_code == "MAT3507" for c in bundle.top_k_chunks)


def test_post_hus_retrieve_endpoint(client):
    response = client.post(
        "/hus/retrieve?top_k=4",
        json={
            "question": "Môn GT1 học những nội dung gì?",
            "major": "computer_science",
            "allow_generated_reference": True,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["resolved_course_code"] == "MAT2501"
    assert payload["dataset"] == "f3"
    assert payload["field"] == "content"
    assert payload["top_k"] == 4
    assert len(payload["top_k_chunks"]) >= 1
    assert payload["top_k_chunks"][0]["course_code"] == "MAT2501"
    assert payload["structured_data"]["course"]["course_code"] == "MAT2501"


def test_cli_inspect_hus_topk_single_json_and_suite(capsys):
    rc_json = inspect_hus_topk.main(
        ["--question", "Môn CSDL học gì?", "--major", "computer_science", "--top-k", "3", "--json"]
    )
    assert rc_json == 0
    out_json = capsys.readouterr().out
    parsed = json.loads(out_json)
    assert parsed["resolved_course_code"] == "MAT3507"
    assert parsed["dataset"] == "f3"
    assert len(parsed["top_k_chunks"]) == 3

    rc_suite = inspect_hus_topk.main(["--suite", "--top-k", "2"])
    assert rc_suite == 0
    out_suite = capsys.readouterr().out
    assert "MAT3507" in out_suite
    assert "MAT1206E" in out_suite
    assert "TOP-2 CHUNKS" in out_suite
