"""Grounded answers and HTTP routing; no provider, product DB or academic verification."""

import json

from fastapi.testclient import TestClient
import pytest

from app.advisor import AdvisorResponse
from app.hus.answering import HUSAnswerer
from app.hus.rag_loader import HUSRAGData, RAGDataError
from app.main import app
from app.schemas.hus import HUSQuestion


@pytest.fixture(scope="module")
def answerer():
    return HUSAnswerer(HUSRAGData.load())


@pytest.mark.parametrize("major", ["mathematics", "mathematics_informatics", "computer_science", "data_science"])
def test_f1_reply_contains_exact_source_excerpts_urls_locators_and_review(answerer, major):
    answer = answerer.answer(HUSQuestion(question="Giới thiệu ngành", major=major))
    assert answer.status == "answered" and answer.dataset == "f1"
    assert answer.citations
    for c in answer.citations:
        assert c.quote in answer.reply
        assert c.open_url in answer.reply if c.open_url else c.availability in {"missing", "unavailable"}
        assert c.locator and c.review_status in {"include", "include_markdown"}
        assert c.metadata["major"] == major
        assert c.quote == c.metadata["source_quote"]
    assert "chưa xác minh hiệu lực" in answer.reply


def test_markdown_only_f1_does_not_claim_original_pdf_verified(answerer):
    request = HUSQuestion(question="Mục tiêu đào tạo", major="computer_science", dataset="f1",
                          field="objectives", version="2023", program_variant="standard")
    answer = answerer.answer(request)
    assert answer.status == "answered"
    assert all(c.review_status == "include_markdown" and not c.metadata["raw_original_verified"]
               for c in answer.citations)
    assert "chưa đối chiếu PDF/DOCX gốc" in answer.reply


@pytest.mark.parametrize("question,field", [("MAT3533 học nội dung gì?", "content"),
                                           ("Mục tiêu học phần MAT3533?", "objectives"),
                                           ("Gợi ý đánh giá MAT3533?", "suggested_assessment")])
def test_f3_reply_is_explicitly_generated_and_never_official(answerer, question, field):
    answer = answerer.answer(HUSQuestion(question=question, major="data_science", version="QD3569-2023", allow_generated_reference=True))
    assert answer.status == "answered" and answer.dataset == "f3"
    assert "kiến thức AI" in answer.reply
    for c in answer.citations:
        assert c.metadata["field"] == field and c.metadata["course_code"] == "MAT3533"
        assert c.review_status == "needs_review" and c.content_origin == "generated"
        assert c.metadata["warning"] in answer.reply
        assert not c.metadata["academic_verified"]
        assert c.source_url is None  # F2 identity URL is not an official syllabus citation.


def test_f2_credit_fact_has_transcription_status_and_pdf_json_locators(answerer):
    answer = answerer.answer(HUSQuestion(question="MAT3533 có bao nhiêu tín chỉ?", major="data_science",
                                         version="QD3569-2023"))
    assert answer.status == "answered" and answer.dataset == "f2"
    assert answer.facts["value"] == 3 and answer.facts["review_status"] == "draft_unverified"
    assert "Số tín chỉ: 3" in answer.reply and "draft_unverified" in answer.reply
    for c in answer.citations:
        row = json.loads(c.quote)
        assert row["course_code"] == "MAT3533" and row["curriculum_id"] == 4
        assert c.locator["pdf_page"] and c.metadata["source_row_pointer"]
        assert c.evidence_kind == "pdf" and c.source_url is None
        assert c.open_url is None and c.availability == "missing"  # Explicit legacy audit has no registered binaries.


def test_f2_conflicting_source_rows_are_reported_separately(answerer):
    answer = answerer.answer(HUSQuestion(question="Tiên quyết MAT3325?", major="mathematics",
                                         version="QD3565-2023"))
    assert answer.status == "answered" and len(answer.citations) == 2
    assert answer.facts["has_prerequisite_conflict"]
    assert "mâu thuẫn" in answer.reply
    assert len(answer.facts["value"]) == 2
    for c in answer.citations:
        assert c.locator["prerequisite_source_text"] in answer.reply


def test_unparsed_unresolved_prerequisite_is_not_silently_lost_or_used_as_edge(answerer):
    answer = answerer.answer(HUSQuestion(question="Tiên quyết MAT3423?", major="mathematics",
                                         version="QD3565-2023"))
    assert answer.facts["unresolved_prerequisites"] == ["MAT3402"]
    assert "Mã tiên quyết chưa giải quyết: MAT3402" in answer.reply
    assert all(p["prerequisite_course_code"] != "MAT3402" for p in answer.facts["prerequisite_groups"])


@pytest.mark.parametrize("question,major,version", [
    ("MAT3533 thi cuối kỳ bao nhiêu phần trăm?", "data_science", "QD3569-2023"),
    ("Đề cương chính thức MAT3533?", "data_science", "QD3569-2023"),
    ("MAT3533 nội dung blockchain?", "data_science", "QD3569-2023"),
    ("Nội dung MAT9999 học gì?", "data_science", "QD3569-2023"),
    ("MAT3533 bao nhiêu tín chỉ?", "data_science", "QD3565-2023"),
    ("Giới thiệu ngành Toán học", "data_science", None),
    ("Cơ hội nghề nghiệp phi hành gia?", "data_science", None),
    ("Học phí HUS năm 2026?", "data_science", None),
    ("Giới thiệu ngành hiện nay", "data_science", None),
    ("CME1000 có bao nhiêu số giờ?", "data_science", "QD3569-2023"),
    ("Số tín chỉ chính thức MAT3533?", "data_science", "QD3569-2023"),
])
def test_missing_or_unsupported_evidence_is_not_filled_in(answerer, question, major, version):
    answer = answerer.answer(HUSQuestion(question=question, major=major, version=version, allow_generated_reference=True))
    assert answer.status == "no_information"
    assert "Chưa có thông tin" in answer.reply
    assert not answer.citations and not answer.facts


@pytest.mark.parametrize("question,version", [("Số tín chỉ MAT3533?", None),
                                             ("Nội dung học phần là gì?", "QD3569-2023"),
                                             ("Số tín chỉ MAT3533 và MAT3507?", "QD3569-2023")])
def test_ambiguous_identity_requests_clarification_without_guessing(answerer, question, version):
    answer = answerer.answer(HUSQuestion(question=question, major="data_science", version=version))
    assert answer.status == "needs_clarification" and not answer.citations


def test_direct_hus_http_answer_does_not_require_runtime_catalog_or_provider(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("HUS lookup must not load a runtime catalog or invoke recommendation")
    monkeypatch.setattr("app.api.routes.load_catalog", forbidden)
    monkeypatch.setattr("app.api.routes.chat_advisor", forbidden)
    response = TestClient(app).post("/hus/chat", json={
        "question": "MAT3533 có bao nhiêu tín chỉ?", "major": "data_science", "version": "QD3569-2023"})
    assert response.status_code == 200
    assert response.json()["facts"]["value"] == 3


@pytest.mark.parametrize("question,dataset", [("Giới thiệu ngành", "f1"),
                                            ("MAT3533 có bao nhiêu tín chỉ?", "f2"),
                                            ("Nội dung MAT3533 học gì?", "f3"),
                                            ("MAT3533 thi cuối kỳ bao nhiêu phần trăm?", "f3")])
def test_existing_advisor_routes_hus_without_loading_recommendation_catalog(monkeypatch, question, dataset):
    def forbidden(*args, **kwargs):
        raise AssertionError("HUS branch must not reach recommendation/catalog")
    monkeypatch.setattr("app.api.routes.load_catalog", forbidden)
    monkeypatch.setattr("app.api.routes.chat_advisor", forbidden)
    response = TestClient(app).post("/advisor/chat", json={"program_id": "khdl", "message": question, "allow_generated_reference": True})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "hus_rag" and data["hus_answer"]["dataset"] == dataset
    assert data["reply"] == data["hus_answer"]["reply"] and not data["suggested_courses"]
    if "phần trăm" in question:
        assert data["hus_answer"]["status"] == "no_information"
    else:
        assert data["hus_answer"]["status"] == "answered"


def test_recommendation_question_retains_old_path_without_loading_hus(monkeypatch):
    def forbidden():
        raise AssertionError("Recommendation should not depend on the HUS package")
    monkeypatch.setattr("app.api.routes.get_hus_answerer", forbidden)
    monkeypatch.setattr("app.api.routes.chat_advisor", lambda *args: AdvisorResponse(reply="existing advisor", mode="heuristic_fallback"))
    response = TestClient(app).post("/advisor/chat", json={"program_id": "khdl",
                                    "message": "Kỳ tới nên học môn nào cho đủ 18 tín chỉ?"})
    assert response.status_code == 200 and response.json()["reply"] == "existing advisor"


@pytest.mark.parametrize("path,body", [("/hus/chat", {"question": "Giới thiệu ngành", "major": "data_science"}),
                                      ("/advisor/chat", {"message": "Giới thiệu ngành", "program_id": "khdl"})])
def test_invalid_package_is_service_failure_not_fabricated_no_information(monkeypatch, path, body):
    def broken():
        raise RAGDataError("private local path and bad checksum")
    monkeypatch.setattr("app.api.routes.get_hus_answerer", broken)
    response = TestClient(app).post(path, json=body)
    assert response.status_code == 503
    assert "private local path" not in response.text


@pytest.mark.parametrize("overrides", [{"major": "unknown"}, {"question": " "}, {"version": ""},
                                      {"course_code": "bad"}, {"field": "tuition"}])
def test_hus_request_validation_is_422(overrides):
    payload = {"question": "Giới thiệu ngành", "major": "data_science", **overrides}
    assert TestClient(app).post("/hus/chat", json=payload).status_code == 422


def test_unknown_program_cannot_borrow_another_majors_evidence():
    response = TestClient(app).post("/advisor/chat", json={"program_id": "unknown", "message": "Giới thiệu ngành"})
    assert response.status_code == 404


@pytest.mark.parametrize("message", [
    "Nên học MAT3533 vì thi cuối kỳ 20% đúng không?",
    "Nên đăng ký MAT3533 vì thi chiếm bao nhiêu điểm?",
    "Gợi ý môn nào thi trắc nghiệm?",
    "Nên học MAT3533 vì thi tự luận?",
    "Nên học môn nào mà tỉ lệ thi 10 phần trăm?",
    "Trọng số đánh giá MAT3533 là bao nhiêu?",
])
def test_exam_fact_requests_cannot_bypass_evidence_via_recommendation_intent(monkeypatch, message):
    def forbidden(*args, **kwargs):
        raise AssertionError("Unverified exam facts must not reach a recommendation provider")
    monkeypatch.setattr("app.api.routes.chat_advisor", forbidden)
    monkeypatch.setattr("app.api.routes.load_catalog", forbidden)
    response = TestClient(app).post("/advisor/chat", json={"program_id": "khdl", "message": message})
    assert response.status_code == 200
    answer = response.json()
    assert answer["mode"] == "hus_rag"
    assert answer["hus_answer"]["status"] == "no_information"
    assert not answer["hus_answer"]["citations"] and "%" not in answer["reply"]


@pytest.mark.parametrize("name", ["khmtt", "KHMT-TT", "Toantin", "Toán-Tin", "Toán học và Tin học",
                                 "mathematics informatics"])
def test_major_alias_in_question_cannot_borrow_selected_catalog_fact(answerer, name):
    answer = answerer.answer(HUSQuestion(question=f"MAT3533 của ngành {name} có bao nhiêu tín chỉ?",
                                         major="data_science", version="QD3569-2023"))
    assert answer.status == "no_information" and not answer.citations


@pytest.mark.parametrize("name", ["Toán-Tin", "Toantin", "Toán học và Tin học", "mathematics informatics"])
def test_long_major_alias_is_not_incorrectly_split_into_two_majors(answerer, name):
    answer = answerer.answer(HUSQuestion(question=f"MAT3533 của ngành {name} có bao nhiêu tín chỉ?",
                                         major="mathematics_informatics", version="QD3567-2023"))
    assert answer.status == "answered" and answer.facts["value"] == 3
    assert all(c.locator["curriculum_id"] == 2 for c in answer.citations)
