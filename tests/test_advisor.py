import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.advisor import (
    AdvisorRequest,
    check_scope_guardrails,
    chat_advisor,
    call_gemini_api,
)
from app.catalog import load_catalog
from app.main import app


def test_guardrails_schedule_requests():
    schedule_questions = [
        "Xếp cho em thời khóa biểu học kỳ tới với",
        "Có thể xếp lịch học đẹp không trùng kíp học không?",
        "Em muốn lịch học buổi sáng để chiều đi làm",
        "Tránh tiết 1 và không học thứ 7 nhé",
    ]
    for q in schedule_questions:
        is_trig, reason, msg = check_scope_guardrails(q)
        assert is_trig is True
        assert reason == "schedule_request"
        assert msg is not None
        assert "thời khóa biểu" in msg


def test_guardrails_instructor_evaluations():
    instructor_questions = [
        "Thầy nào dễ tính hơn để em đăng ký?",
        "Cô nào chấm điểm cao môn Đại số tuyến tính?",
        "Review giảng viên dạy môn Giải tích với ạ",
        "Nên học ai để dễ qua môn hơn?",
    ]
    for q in instructor_questions:
        is_trig, reason, msg = check_scope_guardrails(q)
        assert is_trig is True
        assert reason == "instructor_evaluation"
        assert msg is not None
        assert "giảng viên" in msg or "công bằng" in msg


def test_valid_academic_question_passes_guardrails():
    valid_questions = [
        "Em muốn theo hướng AI Engineer thì kỳ tới nên ưu tiên môn nào?",
        "Môn Khai phá dữ liệu cần học những môn tiên quyết nào trước?",
        "Kỳ 3 em nên đăng ký những môn gì để hoàn thành khối ngành?",
        "Sự khác nhau giữa track Khoa học dữ liệu và Toán tin là gì?",
    ]
    for q in valid_questions:
        is_trig, reason, msg = check_scope_guardrails(q)
        assert is_trig is False
        assert reason is None
        assert msg is None


def test_heuristic_fallback_advisor_generates_valid_eligible_advice():
    cat = load_catalog("khdl")
    req = AdvisorRequest(
        program_id="khdl",
        message="Em muốn định hướng làm về Khoa học dữ liệu và Trí tuệ nhân tạo (AI), kỳ tới nên học gì?",
        passed_course_codes=["PHI1006", "MAT2505"],
    )
    # Không truyền API key -> kích hoạt Heuristic Fallback
    resp = chat_advisor(cat, req, api_key="")
    assert resp.is_guardrail_triggered is False
    assert resp.mode == "heuristic_fallback"
    assert "ĐỦ ĐIỀU KIỆN" in resp.reply
    assert len(resp.suggested_courses) > 0

    # Tất cả các môn được gợi ý phải là môn chưa học
    for code in resp.suggested_courses:
        assert code not in req.passed_course_codes


def test_gemini_api_integration_with_mock():
    cat = load_catalog("khdl")
    req = AdvisorRequest(
        program_id="khdl",
        message="Em thích lập trình và phần mềm, nên học gì?",
        passed_course_codes=["PHI1006"],
    )

    mock_gemini_response = (
        "Chào bạn, với định hướng phần mềm, bạn nên học môn MAT2400 (Lập trình cơ sở). "
        "Ngoài ra tôi cũng gợi ý mã ảo FAKE9999 không có trong CTĐT."
    )

    with patch("app.advisor.call_gemini_api", return_value=mock_gemini_response):
        resp = chat_advisor(cat, req, api_key="fake-test-key")
        assert resp.mode == "gemini_llm"
        assert resp.is_guardrail_triggered is False
        assert "MAT2400" in resp.suggested_courses
        # Mã ảo FAKE9999 phải bị lọc bỏ khỏi suggested_courses
        assert "FAKE9999" not in resp.suggested_courses


def test_advisor_http_endpoint():
    client = TestClient(app)

    # 1. Câu hỏi bị Guardrail chặn
    resp_block = client.post(
        "/advisor/chat",
        json={
            "program_id": "khdl",
            "message": "Xếp cho em thời khóa biểu không học thứ 7 và thầy nào dễ tính",
            "passed_course_codes": [],
        },
    )
    assert resp_block.status_code == 200
    data_b = resp_block.json()
    assert data_b["is_guardrail_triggered"] is True
    assert data_b["mode"] == "guardrail_rejected"

    # 2. Câu hỏi hợp lệ (Mock để không tiêu tốn API key/tiền khi chạy test)
    with patch("app.advisor.call_gemini_api", return_value="Gợi ý bạn học môn MAT2400."):
        resp_ok = client.post(
            "/advisor/chat",
            json={
                "program_id": "khdl",
                "message": "Em muốn theo hướng phân tích dữ liệu (Data Analyst), nên bắt đầu từ môn nào?",
                "passed_course_codes": ["PHI1006"],
            },
        )
        assert resp_ok.status_code == 200
        data_ok = resp_ok.json()
        assert data_ok["is_guardrail_triggered"] is False
        assert len(data_ok["reply"]) > 0


def test_call_gemini_api_beeknoee_format(monkeypatch: pytest.MonkeyPatch):

    monkeypatch.setenv("GEMINI_BASE_URL", "https://platform.beeknoee.com/api/v1")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.8-flash")

    mock_resp = {
        "choices": [
            {
                "message": {"content": "Khuyên bạn nên học MAT2400."}
            }
        ]
    }
    with patch("httpx.Client.post") as mock_post:
        mock_post.return_value.json.return_value = mock_resp
        mock_post.return_value.raise_for_status = lambda: None
        result = call_gemini_api("Xin chào", "fake-api-key")
        assert result == "Khuyên bạn nên học MAT2400."
        assert mock_post.called
        call_url = mock_post.call_args[0][0]
        assert "chat/completions" in call_url
