"""Exposed routing regressions; intent corrections must preserve source/consent."""

import json
from pathlib import Path

import pytest

from app.hus.chat import chat
from app.hus.question_routing import question_intent
from app.schemas.hus import HUSQuestion
from app.services.hus_service import get_hus_answerer
from tools.evaluate_hus_rag import TracedRetriever

PACK = Path(__file__).resolve().parents[2] / "data/hus/evaluation/diagnostic_dev_v2_routing"
QUESTIONS = [json.loads(line) for line in (PACK / "questions.jsonl").read_text(encoding="utf-8").splitlines()]
GOLD = [json.loads(line) for line in (PACK / "gold.jsonl").read_text(encoding="utf-8").splitlines()]
CASES = [json.loads(line) for line in (PACK / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
NAME_CASES = [(q, g) for q, g in zip(QUESTIONS, GOLD, strict=True) if g["category"] == "f2"]
PREVIEW_CASES = [(q, g) for q, g in zip(QUESTIONS, GOLD, strict=True) if g["category"] == "f3"]


@pytest.fixture(scope="module")
def answerer():
    return get_hus_answerer()


@pytest.mark.parametrize("question,case", list(zip(QUESTIONS, CASES, strict=True)),
                         ids=[q["question_id"] for q in QUESTIONS])
def test_exposed_requests_select_the_requested_dataset_and_field(question, case):
    assert question_intent(question["request"]["question"]) == tuple(case["expected_route"])


@pytest.mark.parametrize("question,target", NAME_CASES, ids=[q["question_id"] for q, _ in NAME_CASES])
def test_original_name_requests_return_the_exact_scoped_source_name(answerer, question, target):
    answer = chat(HUSQuestion(**question["request"]), answerer).hus_answer
    assert answer.status == "answered" and answer.dataset == "f2"
    assert answer.facts["field"] == "name"
    assert answer.facts["value"] == target["expected_facts"]["course_name"]
    assert answer.citations
    assert all(c.dataset == "f2" and c.review_status == answer.facts["review_status"] for c in answer.citations)


@pytest.mark.parametrize("question,target", PREVIEW_CASES, ids=[q["question_id"] for q, _ in PREVIEW_CASES])
def test_original_content_previews_search_f3_in_the_selected_scope(answerer, monkeypatch, question, target):
    traced = TracedRetriever(answerer.retriever)
    monkeypatch.setattr(answerer, "retriever", traced)
    answer = chat(HUSQuestion(**question["request"]), answerer).hus_answer
    assert len(traced.calls) == 1
    parameters = traced.calls[0]["parameters"]
    assert (parameters["dataset"], parameters["field"]) == ("f3", "content")
    assert parameters["major"] == question["request"]["major"]
    assert parameters["version"] == question["request"]["version"]
    assert parameters["allow_generated"] is True
    assert traced.calls[0]["hits"]
    assert answer.dataset == "f3" and not answer.facts
    # This task fixes routing; the original wording may still fail the support gate.
    assert answer.status in {"answered", "no_information"}


@pytest.mark.parametrize("question,expected", [
    ("Cho biết nguyên tên của mã MAT3533.", ("f2", "name")),
    ("Tên của mã MAT3533 là gì?", ("f2", "name")),
    ("Mình muốn tên của học phần MAT3533.", ("f2", "name")),
    ("Giúp mình tên của môn MAT3533.", ("f2", "name")),
    ("Hình dung trước môn MAT3533: nội dung?", ("f3", "content")),
    ("Tìm hiểu trước môn MAT3533: nội dung?", ("f3", "content")),
    ("Xem trước môn MAT3533: các chủ đề?", ("f3", "content")),
    ("Hinh dung truoc mon MAT3533, noi dung hoc gi?", ("f3", "content")),
    ("Để hình dung trước môn MAT3533, chuẩn đầu ra AI là gì?", ("f3", "objectives")),
    ("Hình dung trước môn MAT3533 học gì?", ("f3", "content")),
    ("Tìm hiểu trước môn MAT3533: gợi ý đánh giá AI?", ("f3", "suggested_assessment")),
])
def test_natural_name_and_preview_variants(question, expected):
    assert question_intent(question) == expected


@pytest.mark.parametrize("question", [
    "Trước môn MAT3533 cần học những môn nào?",
    "Để hình dung trước môn MAT3533, hãy chép các mã học trước.",
    "Tìm hiểu trước môn MAT3533: điều kiện tiên quyết là gì?",
    "Xem trước môn MAT3533, cần học trước học phần nào?",
    "Nội dung học trước môn MAT3533 theo bảng nguồn?",
    "Hình dung trước môn MAT3533: trước môn này cần học gì?",
    "Trước môn MAT3533 cần biết tên môn nào đã học?",
    "Tôi muốn tìm hiểu: trước môn MAT3533 cần học những học phần nào?",
    "Xem: trước môn MAT3533 cần học những môn nào?",
    "Hình dung; trước môn MAT3533 cần học gì?",
    "Tôi muốn hình dung, trước môn MAT3533 cần học gì?",
    "Tôi muốn hình dung nhưng trước môn MAT3533 cần học gì?",
    "Tôi muốn xem. Trước môn MAT3533 cần học gì?",
    "Tôi muốn tìm hiểu trước môn MAT3533 cần học những môn nào?",
    "Xem trước môn MAT3533 cần học những môn nào?",
    "Hình dung trước môn MAT3533, cần học những học phần nào?",
    "Tìm hiểu trước môn MAT3533 phải hoàn thành các học phần nào?",
    "Xem trước môn MAT3533 các môn học nào là bắt buộc?",
    "Xem trước môn MAT3533 các chủ đề của các môn cần học là gì?",
    "Tôi muốn hình dung trước môn MAT3533 học những môn nào?",
])
def test_real_prerequisite_requests_keep_their_priority(question):
    assert question_intent(question) == ("f2", "prerequisites")


@pytest.mark.parametrize("question", [
    "Tên tác giả tài liệu MAT3533 là ai?",
    "Tên của công ty dạy MAT3533 là gì?",
])
def test_generic_names_do_not_become_course_name_lookups(question):
    assert question_intent(question) != ("f2", "name")


@pytest.mark.parametrize("question,overrides,status", [
    ("Nguyên tên của mã MAT9999?", {}, "no_information"),
    ("Tên của mã MAT3533 của ngành Toán tin?", {}, "no_information"),
    ("Nguyên tên của mã MAT3533 hay MAT3507?", {}, "needs_clarification"),
    ("Tên của mã MAT3533 (Cơ sở dữ liệu)?", {}, "needs_clarification"),
    ("Tên của mã MAT3533 theo xác nhận hiện hành của trường?", {}, "no_information"),
    ("Nguyên tên của mã MAT3533 và nên đăng ký môn nào?", {}, "no_information"),
    ("Nguyên tên của mã MAT3533 theo QD3569-2023?", {"version": "QD3565-2023"}, "no_information"),
])
def test_new_name_phrasing_does_not_bypass_identity_scope_or_review(answerer, question, overrides, status):
    request = {"question": question, "major": "data_science", "version": "QD3569-2023", **overrides}
    answer = chat(HUSQuestion(**request), answerer).hus_answer
    assert answer.status == status
    assert not answer.facts and not answer.citations


@pytest.mark.parametrize("allow_ai", [False, True])
def test_preview_content_obeys_actual_opt_in_and_keeps_ai_citations(answerer, allow_ai):
    answer = chat(HUSQuestion(question="Hình dung trước môn MAT3533: nội dung?",
                              major="data_science", version="QD3569-2023",
                              allow_generated_reference=allow_ai), answerer).hus_answer
    if not allow_ai:
        assert answer.status == "needs_clarification"
        assert not answer.facts and not answer.citations
    else:
        assert answer.status == "answered" and answer.dataset == "f3"
        assert answer.citations
        assert all(c.evidence_kind == "ai" and c.display_label == "kiến thức AI" and c.open_url is None
                   for c in answer.citations)


def test_preview_wording_does_not_make_official_syllabus_available(answerer):
    answer = chat(HUSQuestion(question="Hình dung trước môn MAT3533: nội dung đề cương chính thức?",
                              major="data_science", version="QD3569-2023",
                              allow_generated_reference=True), answerer).hus_answer
    assert answer.status == "no_information" and not answer.facts and not answer.citations


@pytest.mark.parametrize("question", [
    "Tôi muốn tìm hiểu: trước môn MAT3533 cần học những học phần nào?",
    "Tôi muốn tìm hiểu trước môn MAT3533 cần học những môn nào?",
    "Hình dung trước môn MAT3533, cần học những học phần nào?",
])
def test_actual_prerequisite_request_does_not_ask_for_ai_consent(answerer, question):
    answer = chat(HUSQuestion(question=question,
                              major="data_science", version="QD3569-2023"), answerer).hus_answer
    assert answer.status == "answered" and answer.dataset == "f2"
    assert answer.facts["field"] == "prerequisites"
    assert answer.facts["value"] == ["MAT2406/\nMAT2323"]
    assert answer.citations and all(c.dataset == "f2" for c in answer.citations)
