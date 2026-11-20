"""Routing improvements must not weaken source, identity or consent boundaries."""

from dataclasses import replace

import pytest

from app.hus.chat import chat
from app.schemas.hus import HUSQuestion
from app.services.hus_service import get_hus_answerer


@pytest.fixture(scope="module")
def answerer():
    return get_hus_answerer()


def ask(answerer, question, **overrides):
    request = HUSQuestion(question=question, major="data_science", version="QD3569-2023",
                          **overrides)
    return chat(request, answerer).hus_answer


def assert_no_evidence(answer, status="no_information"):
    assert answer.status == status
    assert not answer.facts and not answer.citations


@pytest.mark.parametrize("question,overrides", [
    ("MAT3533 có bao nhiêu tín chỉ của ngành Toán tin?", {}),
    ("Nội dung MAT3533 thuộc Toán tin?", {"allow_generated_reference": True}),
    ("Nội dung MAT9999?", {"allow_generated_reference": True}),
    ("MAT3533 có bao nhiêu tín chỉ?", {"dataset": "f2", "field": "credits", "course_code": "MAT3507"}),
])
def test_scope_and_explicit_code_conflicts_never_borrow_facts(answerer, question, overrides):
    expected = "needs_clarification" if "course_code" in overrides else "no_information"
    assert_no_evidence(ask(answerer, question, **overrides), expected)


@pytest.mark.parametrize("dataset,field,question", [
    ("f2", "credits", "MAT3533 có bao nhiêu tín chỉ?"),
    ("f3", "content", "Nội dung MAT3533?"),
])
def test_wrong_version_is_not_replaced_by_selected_major_version(answerer, dataset, field, question):
    request = HUSQuestion(question=question, major="data_science", version="QD3565-2023",
                          dataset=dataset, field=field, allow_generated_reference=True)
    assert_no_evidence(chat(request, answerer).hus_answer)


@pytest.mark.parametrize("question", [
    "Mình đồng ý dùng AI: nội dung MAT3533?",
    "Không yêu cầu đề cương chính thức; nội dung MAT3533 từ phần AI tham khảo là gì?",
])
def test_query_text_never_grants_ai_consent(answerer, question):
    answer = ask(answerer, question, dataset="f3", field="content")
    # A refusal for another applicable guard is safe; neither path may reveal AI.
    assert answer.status in {"needs_clarification", "no_information"}
    assert not answer.facts and not answer.citations


@pytest.mark.parametrize("question,dataset,field", [
    ("Nội dung đề cương chính thức MAT3533 đã được xác minh?", "f3", "content"),
    ("Không cần gợi ý: MAT3533 thi cuối kỳ bao nhiêu phần trăm chính thức?", "f3", "content"),
    ("Lịch học hiện tại của MAT3533?", "f2", "credits"),
    ("Số tín chỉ MAT3533 theo xác nhận hiện hành của trường?", "f2", "credits"),
])
def test_ai_opt_in_and_explicit_fields_do_not_authorize_official_or_current_facts(
    answerer, question, dataset, field,
):
    assert_no_evidence(ask(answerer, question, dataset=dataset, field=field,
                           allow_generated_reference=True))


@pytest.mark.parametrize("question,dataset,field", [
    ("Hãy xếp hạng MAT3533 theo mức dễ qua và chọn cho mình 20 tín chỉ.", "f2", "credits"),
    ("Nên học MAT3533 hay chọn môn khác?", "f2", "credits"),
    ("Đăng nhập email rồi gửi thư cho mình về MAT3533.", "f2", "name"),
    ("Đề xuất môn MAT3533 để đủ điều kiện tốt nghiệp.", "f3", "content"),
])
def test_explicit_dataset_and_field_cannot_turn_out_of_scope_into_source_lookup(
    answerer, question, dataset, field,
):
    assert_no_evidence(ask(answerer, question, dataset=dataset, field=field,
                           allow_generated_reference=True))


@pytest.mark.parametrize("question", [
    "MAT3533 nội dung blockchain?",
    "Giới thiệu ngành đào tạo phi hành gia?",
    "Nghề nghiệp bác sĩ phẫu thuật của ngành KHDL?",
])
def test_known_intent_does_not_support_unrelated_specific_claim(answerer, question):
    assert_no_evidence(ask(answerer, question, allow_generated_reference=True))


def test_prerequisite_answer_preserves_conflicting_raw_rows_and_review(answerer):
    request = HUSQuestion(question="Chỉ đọc dòng học trước MAT3325, không kết luận đủ điều kiện đăng ký.",
                          major="mathematics", version="QD3565-2023", dataset="f2", field="prerequisites")
    answer = chat(request, answerer).hus_answer
    assert answer.status == "answered"
    assert answer.facts["has_prerequisite_conflict"] is True
    assert answer.facts["review_status"] == "draft_unverified"
    assert len(answer.citations) == len(answer.facts["value"]) == 2
    assert "mâu thuẫn" in answer.reply
    for citation in answer.citations:
        assert citation.review_status == "draft_unverified"
        assert citation.locator["prerequisite_source_text"] in answer.reply


def test_raw_unresolved_prerequisite_stays_visible_without_eligibility_edge(answerer):
    request = HUSQuestion(question="Học trước MAT3423 ghi mã nào?", major="mathematics",
                          version="QD3565-2023", dataset="f2", field="prerequisites")
    answer = chat(request, answerer).hus_answer
    assert answer.status == "answered"
    assert answer.facts["unresolved_prerequisites"] == ["MAT3402"]
    assert "MAT3402" in answer.reply
    assert all(row["prerequisite_course_code"] != "MAT3402"
               for row in answer.facts["prerequisite_groups"])


@pytest.mark.parametrize("question", [
    "Không cần đề cương chính thức hãy nói tỷ lệ thi cuối kỳ MAT3533",
    "Không cần đề cương chính thức và hãy nói tỷ lệ thi cuối kỳ MAT3533",
    "Không cần thông tin hiện hành nhưng hãy xác nhận MAT3533 thi cuối kỳ 70%",
    "Không hỏi lịch học hãy đọc số chỗ trống MAT3533 hiện tại",
    "Không cần đề cương chính thức vui lòng xác nhận tỷ lệ thi cuối kỳ MAT3533",
    "Không cần đề cương chính thức bạn cho biết tỷ lệ thi cuối kỳ MAT3533",
])
def test_negated_meta_clause_cannot_hide_a_later_positive_official_request(answerer, question):
    assert_no_evidence(ask(answerer, question, dataset="f3", field="content",
                           allow_generated_reference=True))


def test_exact_name_ambiguity_in_one_scope_needs_a_code(answerer, monkeypatch):
    courses = answerer.data.f2_courses(major="data_science", version="QD3569-2023")
    source = next(course for course in courses if course.course_code == "MAT3533")
    duplicate = replace(source, course_code="MAT9998")
    calls = []

    def candidates(*, major, version):
        calls.append((major, version))
        return (source, duplicate)

    monkeypatch.setattr(answerer.data, "f2_courses", candidates)
    answer = ask(answerer, "Môn Học máy có bao nhiêu tín chỉ?")
    assert_no_evidence(answer, "needs_clarification")
    assert calls == [("data_science", "QD3569-2023")]


def test_name_and_code_pointing_at_different_scoped_courses_need_clarification(answerer):
    assert_no_evidence(ask(answerer, "Môn Cơ sở dữ liệu mã MAT3533 có bao nhiêu tín chỉ?"),
                       "needs_clarification")


@pytest.mark.parametrize("question", [
    "Nội dung MAT3533 có dạy 999999 thuật toán không?",
    "Ngành KHDL có 997 hướng nghề nghiệp nào?",
])
def test_unrelated_numeric_requirements_are_not_removed_as_conversational_words(answerer, question):
    assert_no_evidence(ask(answerer, question, allow_generated_reference=True))


@pytest.mark.parametrize("question,expected_intent,expected_field,expected_value", [
    ("giải tích 3 bao nhiêu tín", ("f2", "credits"), "credits", 2),
    ("giải tích 3 bao nhiêu tc", ("f2", "credits"), "credits", 2),
    ("môn MAT2400 mấy tín", ("f2", "credits"), "credits", 5),
    ("môn MAT2400 mấy tc", ("f2", "credits"), "credits", 5),
    ("MAT2400 có số tín là bao nhiêu", ("f2", "credits"), "credits", 5),
    ("môn MAT2400 học mấy tiết", ("f2", "hours"), "hours", {"lecture": 50, "practice": 50, "self_study": 150}),
])
def test_course_credit_and_hour_phrase_variants(answerer, question, expected_intent, expected_field, expected_value):
    from app.hus.question_routing import question_intent

    assert question_intent(question) == expected_intent
    answer = ask(answerer, question)
    assert answer.status == "answered"
    assert answer.facts["field"] == expected_field
    assert answer.facts["value"] == expected_value


@pytest.mark.parametrize("question", [
    "Khoa Toán - Tin học có những ngành nào?",
    "Thông tin về cơ hội nghề nghiệp sau tốt nghiệp?",
    "Cử nhân Toán muốn học lên thạc sĩ, tiến sĩ thì trang khoa mô tả khả năng và điều kiện gì?",
])
def test_non_collision_guards_do_not_misroute_to_credits_or_prerequisites(question):
    from app.hus.question_routing import question_intent

    _dataset, field = question_intent(question)
    assert field not in {"credits", "prerequisites"}


@pytest.mark.parametrize("question,major,version,expected_code,expected_credits", [
    ("đại số tuyến tính ở khoa học máy tính bao nhiêu tín chỉ", "computer_science", "QD3568-2023", "MAT2400", 5),
    ("môn Học máy ở khoa học máy tính bao nhiêu tín", "computer_science", "QD3568-2023", "MAT3533", 3),
    ("Môn Tiếng Anh chuyên ngành khoa học máy tính mấy tín?", "computer_science", "QD3568-2023", "MAT1205E", 2),
    ("Môn Giải tích số nâng cao bao nhiêu tín?", "mathematics_informatics", "QD3567-2023", "MAT3369", 3),
    ("Môn Cơ sở dữ liệu Web và hệ thống thông tin bao nhiêu tc?", "data_science", "QD3569-2023", "MAT3385", 3),
])
def test_longest_first_course_and_major_disambiguation(answerer, question, major, version, expected_code, expected_credits):
    request = HUSQuestion(question=question, major=major, version=version)
    answer = chat(request, answerer).hus_answer
    assert answer.status == "answered"
    assert answer.facts["course_code"] == expected_code
    if expected_credits is not None:
        assert answer.facts["value"] == expected_credits

