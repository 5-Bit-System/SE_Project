"""Unit, integration, and security mock tests for HUS RAG LLM grounded answering."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from app.hus.chat import chat
from app.hus.llm_answerer import _redact_key, call_gemini_llm, generate_grounded_answer
from app.schemas.hus import HUSCitation, HUSQuestion
from app.services.hus_service import get_hus_answerer


@pytest.fixture(scope="module")
def answerer():
    return get_hus_answerer()


def _mock_gemini_success_response(text: str = "Nội dung phản hồi chuẩn từ Gemini [1].") -> dict[str, Any]:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": text}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ]
    }


def _mock_openai_success_response(text: str = "Nội dung phản hồi từ OpenAI proxy.") -> dict[str, Any]:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": text,
                }
            }
        ]
    }


# ============================================================================
# Kịch bản 1: call_gemini_llm thành công với Google Generative Language API
# ============================================================================


def test_call_gemini_llm_success_direct_api(monkeypatch):
    """Kịch bản 1A: Gọi Google Generative Language API thành công, kiểm tra request và response."""
    captured_requests: list[dict[str, Any]] = []

    def mock_post(client_self, url, *args, **kwargs):
        captured_requests.append({
            "url": str(url),
            "headers": dict(kwargs.get("headers") or {}),
            "json": kwargs.get("json"),
        })
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json=_mock_gemini_success_response("Phản hồi thành công từ Gemini 3.5"), request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    prompt = "Môn CSDL học gì?"
    reply = call_gemini_llm(
        prompt,
        api_key="test-gemini-key-123",
        model="gemini-3.5-flash-lite",
    )

    assert reply == "Phản hồi thành công từ Gemini 3.5"
    assert len(captured_requests) == 1
    req_info = captured_requests[0]

    # Verify endpoint URL
    assert "generativelanguage.googleapis.com" in req_info["url"]
    assert "models/gemini-3.5-flash-lite:generateContent" in req_info["url"]

    # Verify header
    assert req_info["headers"].get("x-goog-api-key") == "test-gemini-key-123"

    # Verify payload structure
    payload = req_info["json"]
    assert "contents" in payload
    assert payload["contents"][0]["parts"][0]["text"] == prompt
    assert payload["generationConfig"]["temperature"] == 0.4
    assert payload["generationConfig"]["maxOutputTokens"] == 4000


def test_call_gemini_llm_success_openai_compatible_proxy(monkeypatch):
    """Kịch bản 1B: Gọi qua OpenAI-compatible proxy endpoint khi base_url được cung cấp."""
    captured_requests: list[dict[str, Any]] = []

    def mock_post(client_self, url, *args, **kwargs):
        captured_requests.append({
            "url": str(url),
            "headers": dict(kwargs.get("headers") or {}),
            "json": kwargs.get("json"),
        })
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json=_mock_openai_success_response("Phản hồi qua proxy"), request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    prompt = "Môn Giải tích 1 có khó không?"
    reply = call_gemini_llm(
        prompt,
        api_key="proxy-secret-key-456",
        base_url="https://proxy.example.edu.vn/v1",
        model="gemini-3.5-flash-lite",
    )

    assert reply == "Phản hồi qua proxy"
    assert len(captured_requests) == 1
    req_info = captured_requests[0]
    assert req_info["url"] == "https://proxy.example.edu.vn/v1/chat/completions"
    assert req_info["headers"].get("Authorization") == "Bearer proxy-secret-key-456"
    assert req_info["json"]["model"] == "gemini-3.5-flash-lite"
    assert req_info["json"]["messages"][-1]["content"] == prompt


# ============================================================================
# Kịch bản 2: call_gemini_llm chuỗi fallback model
# ============================================================================


def test_call_gemini_llm_fallback_on_503(monkeypatch):
    """Kịch bản 2A: Model đầu tiên trả về HTTP 503 -> tự động fallback sang model kế tiếp."""
    called_models: list[str] = []

    def mock_post(client_self, url, *args, **kwargs):
        req = httpx.Request("POST", str(url))
        # Extract model from URL
        url_str = str(url)
        for m in ["gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]:
            if m in url_str:
                called_models.append(m)
                break

        if len(called_models) == 1:
            # Model đầu tiên gặp 503 high demand
            return httpx.Response(503, json={"error": "Service Unavailable"}, request=req)

        # Model thứ hai thành công
        return httpx.Response(200, json=_mock_gemini_success_response("Nội dung từ model fallback 3.5"), request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    reply = call_gemini_llm(
        "Môn CSDL bao nhiêu tín?",
        api_key="mock-api-key",
        model="gemini-flash-lite-latest",
    )

    assert reply == "Nội dung từ model fallback 3.5"
    assert len(called_models) == 2
    assert called_models[0] == "gemini-flash-lite-latest"
    assert called_models[1] == "gemini-3.5-flash-lite"


def test_call_gemini_llm_fallback_on_timeout(monkeypatch):
    """Kịch bản 2B: Model đầu tiên bị Timeout -> tự động fallback sang model tiếp theo thành công."""
    attempts = 0

    def mock_post(client_self, url, *args, **kwargs):
        nonlocal attempts
        attempts += 1
        req = httpx.Request("POST", str(url))
        if attempts == 1:
            raise httpx.TimeoutException("Connection timed out", request=req)
        return httpx.Response(200, json=_mock_gemini_success_response("Phục hồi sau timeout"), request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    reply = call_gemini_llm(
        "Giới thiệu môn học",
        api_key="mock-key",
        model="gemini-flash-lite-latest",
    )

    assert reply == "Phục hồi sau timeout"
    assert attempts == 2


def test_call_gemini_llm_fallback_on_http_error(monkeypatch):
    """Kịch bản 2C: Model đầu tiên gặp HTTPStatusError -> tự động fallback sang model kế tiếp."""
    attempts = 0

    def mock_post(client_self, url, *args, **kwargs):
        nonlocal attempts
        attempts += 1
        req = httpx.Request("POST", str(url))
        if attempts == 1:
            return httpx.Response(500, json={"error": "Internal Server Error"}, request=req)
        return httpx.Response(200, json=_mock_gemini_success_response("Phục hồi sau 500"), request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    reply = call_gemini_llm(
        "Môn học tiên quyết",
        api_key="mock-key",
        model="gemini-flash-lite-latest",
    )

    assert reply == "Phục hồi sau 500"
    assert attempts == 2


# ============================================================================
# Kịch bản 3: call_gemini_llm khi tất cả các model đều lỗi
# ============================================================================


def test_call_gemini_llm_all_models_fail_raises_exception(monkeypatch):
    """Kịch bản 3A: Tất cả các model trong chuỗi fallback đều trả về lỗi -> ném ngoại lệ."""
    call_count = 0

    def mock_post(client_self, url, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        req = httpx.Request("POST", str(url))
        return httpx.Response(500, json={"error": "All clusters busy"}, request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post)

    with pytest.raises(Exception) as exc_info:
        call_gemini_llm(
            "Câu hỏi test lỗi",
            api_key="test-fail-key",
            model="gemini-flash-lite-latest",
        )

    assert call_count >= 2
    # Verify exception was caught and raised
    assert exc_info.value is not None


def test_call_gemini_llm_empty_response_raises_value_error(monkeypatch):
    """Kịch bản 3B: API trả về 200 nhưng rỗng candidates hoặc content rỗng -> ném ValueError an toàn."""
    def mock_post_empty_candidates(client_self, url, *args, **kwargs):
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json={"candidates": []}, request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post_empty_candidates)

    with pytest.raises(ValueError, match="không trả về candidate nào"):
        call_gemini_llm(
            "Câu hỏi test",
            api_key="test-empty-key",
            model="gemini-3.5-flash-lite",
        )

    def mock_post_empty_text(client_self, url, *args, **kwargs):
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": "   "}]}}]}, request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post_empty_text)

    with pytest.raises(ValueError, match="rỗng"):
        call_gemini_llm(
            "Câu hỏi test",
            api_key="test-empty-key",
            model="gemini-3.5-flash-lite",
        )


# ============================================================================
# Kịch bản 4: generate_grounded_answer với cấu hình hợp lệ
# ============================================================================


def test_generate_grounded_answer_success(answerer, monkeypatch):
    """Kịch bản 4: generate_grounded_answer sinh câu trả lời có trích dẫn và cấu trúc prompt chuẩn."""
    captured_prompt: list[str] = []

    def mock_post(client_self, url, *args, **kwargs):
        json_body = kwargs.get("json", {})
        parts = json_body.get("contents", [{}])[0].get("parts", [{}])
        if parts:
            captured_prompt.append(parts[0].get("text", ""))
        req = httpx.Request("POST", str(url))
        return httpx.Response(
            200,
            json=_mock_gemini_success_response(
                "Phần 1: Thông tin học phần:\n- Mã học phần: MAT3507 [1]\n"
                "- Tên học phần: Cơ sở dữ liệu\n- Số tín chỉ: 4 tín chỉ [1]\n"
                "Phần 2: Môn học trang bị kiến thức nền tảng về hệ quản trị cơ sở dữ liệu [2]."
            ),
            request=req,
        )

    monkeypatch.setattr(httpx.Client, "post", mock_post)
    monkeypatch.setattr(
        "app.hus.llm_answerer.get_settings",
        lambda: SimpleNamespace(
            hus_rag_llm_enabled=True,
            gemini_api_key="mock-valid-key",
            hus_rag_llm_model="gemini-3.5-flash-lite",
            gemini_base_url="",
            gemini_model="gemini-3.5-flash-lite",
            recommendation_llm_enabled=True,
        ),
    )

    req = HUSQuestion(
        question="Môn CSDL bao nhiêu tín?",
        major="computer_science",
        version="QD3568-2023",
        allow_generated_reference=True,
    )
    base_answer = answerer.answer(req)
    result = generate_grounded_answer(req, answerer, answer=base_answer)

    assert result is not None
    reply_text, llm_citations = result

    # 1. Check return format
    assert isinstance(reply_text, str)
    assert "MAT3507" in reply_text
    assert "[1]" in reply_text
    assert isinstance(llm_citations, list)
    assert len(llm_citations) >= 1
    assert all(isinstance(c, HUSCitation) for c in llm_citations)

    # 2. Sequential citation IDs starting from 1
    citation_ids = [c.citation_id for c in llm_citations]
    assert citation_ids[0] == "1"
    assert citation_ids == [str(i) for i in range(1, len(llm_citations) + 1)]

    # 3. Check prompt structure
    assert len(captured_prompt) == 1
    prompt_str = captured_prompt[0]
    assert "### Dữ kiện học phần chính thức (F2)" in prompt_str
    assert "MAT3507" in prompt_str
    assert "Cơ sở dữ liệu" in prompt_str
    assert "4" in prompt_str
    assert "[1], [2]" in prompt_str
    assert "Answer-first" in prompt_str
    assert "TUYỆT ĐỐI KHÔNG chia mục theo khuôn mẫu cứng nhắc" in prompt_str


# ============================================================================
# Kịch bản 5: generate_grounded_answer bypass khi cấu hình tắt/thiếu API key
# ============================================================================


def test_generate_grounded_answer_bypass_when_disabled(answerer, monkeypatch):
    """Kịch bản 5A: Khi hus_rag_llm_enabled=False -> trả về None ngay, không gọi HTTP."""
    http_called = False

    def mock_post(client_self, url, *args, **kwargs):
        nonlocal http_called
        http_called = True
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json={}, request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post)
    monkeypatch.setattr(
        "app.hus.llm_answerer.get_settings",
        lambda: SimpleNamespace(
            hus_rag_llm_enabled=False,
            gemini_api_key="valid-key-but-disabled",
            hus_rag_llm_model="gemini-3.5-flash-lite",
            gemini_base_url="",
            gemini_model="gemini-3.5-flash-lite",
            recommendation_llm_enabled=False,
        ),
    )

    req = HUSQuestion(
        question="Môn CSDL học gì?",
        major="computer_science",
        version="QD3568-2023",
    )
    result = generate_grounded_answer(req, answerer)
    assert result is None
    assert not http_called


def test_generate_grounded_answer_bypass_when_empty_api_key(answerer, monkeypatch):
    """Kịch bản 5B: Khi gemini_api_key rỗng -> trả về None ngay lập tức, không gọi HTTP."""
    http_called = False

    def mock_post(client_self, url, *args, **kwargs):
        nonlocal http_called
        http_called = True
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json={}, request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post)
    monkeypatch.setattr(
        "app.hus.llm_answerer.get_settings",
        lambda: SimpleNamespace(
            hus_rag_llm_enabled=True,
            gemini_api_key="   ",  # whitespace only
            hus_rag_llm_model="gemini-3.5-flash-lite",
            gemini_base_url="",
            gemini_model="gemini-3.5-flash-lite",
            recommendation_llm_enabled=True,
        ),
    )

    req = HUSQuestion(
        question="Môn CSDL học gì?",
        major="computer_science",
        version="QD3568-2023",
    )
    result = generate_grounded_answer(req, answerer)
    assert result is None
    assert not http_called


def test_generate_grounded_answer_bypass_when_unparseable_query(answerer, monkeypatch):
    """Kịch bản 5C: Câu hỏi không phân tích được hoặc ngoài phạm vi (zero context) -> trả về None."""
    http_called = False

    def mock_post(client_self, url, *args, **kwargs):
        nonlocal http_called
        http_called = True
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json={}, request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post)
    monkeypatch.setattr(
        "app.hus.llm_answerer.get_settings",
        lambda: SimpleNamespace(
            hus_rag_llm_enabled=True,
            gemini_api_key="test-key-mock",
            hus_rag_llm_model="gemini-3.5-flash-lite",
            gemini_base_url="",
            gemini_model="gemini-3.5-flash-lite",
            recommendation_llm_enabled=True,
        ),
    )

    req = HUSQuestion(
        question="Hôm nay thời tiết thế nào ở Hà Nội?",
        major="computer_science",
        version="QD3568-2023",
    )
    result = generate_grounded_answer(req, answerer)
    assert result is None
    assert not http_called


# ============================================================================
# Kịch bản 6: Kiểm tra bảo mật (Security & Redaction)
# ============================================================================


def test_security_redaction_api_key_not_in_exception(monkeypatch):
    """Kịch bản 6A: Khi xảy ra lỗi mạng/API, chuỗi GEMINI_API_KEY không bao giờ xuất hiện trong exception."""
    sensitive_api_key = "AIzaSySUPER_SECRET_TOKEN_DO_NOT_LEAK_987654321"

    def mock_post_fail(client_self, url, *args, **kwargs):
        # Giả lập httpx ném lỗi chứa URL hoặc thông tin chi tiết
        req = httpx.Request("POST", f"{url}?key={sensitive_api_key}")
        raise httpx.HTTPStatusError("500 Internal Error", request=req, response=httpx.Response(500, request=req))

    monkeypatch.setattr(httpx.Client, "post", mock_post_fail)

    with pytest.raises(Exception) as exc_info:
        call_gemini_llm(
            "Câu hỏi bảo mật",
            api_key=sensitive_api_key,
            model="gemini-3.5-flash-lite",
        )

    # Đảm bảo exception string tuyệt đối không chứa sensitive_api_key
    err_str = str(exc_info.value)
    assert sensitive_api_key not in err_str


def test_security_redaction_api_key_not_in_logs(monkeypatch, caplog):
    """Kịch bản 6B: Khi gọi API thất bại, chuỗi GEMINI_API_KEY không được ghi vào logs."""
    sensitive_api_key = "AIzaSyLOGGER_SECRET_KEY_CHECK_STRICT_12345678"

    def mock_post_fail(client_self, url, *args, **kwargs):
        req = httpx.Request("POST", str(url))
        # Giả lập error message cố tình chứa api key
        raise httpx.RequestError(f"Connection failed for key {sensitive_api_key}", request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post_fail)

    with caplog.at_level(logging.WARNING, logger="app.hus.llm_answerer"):
        try:
            call_gemini_llm(
                "Câu hỏi kiểm tra logs",
                api_key=sensitive_api_key,
                model="gemini-3.5-flash-lite",
            )
        except Exception:
            pass

    # Kiểm tra toàn bộ log text
    assert sensitive_api_key not in caplog.text
    assert "[REDACTED_API_KEY]" in caplog.text or len(caplog.records) > 0


def test_security_redaction_helper_unit():
    """Kịch bản 6C: Đơn vị kiểm tra hàm _redact_key."""
    key = "secret_key_123"
    raw_text = f"Lỗi kết nối tại https://api.google.com?key={key} với trạng thái 403"
    sanitized = _redact_key(raw_text, key)
    assert key not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized

    # Case empty key
    assert _redact_key("No change", "") == "No change"


# ============================================================================
# Kịch bản 7: Tích hợp với chat()
# ============================================================================


def test_chat_integration_grounded_llm_mode(answerer, monkeypatch):
    """Kịch bản 7A: Khi LLM thành công -> result.generation_mode == 'grounded_llm' và cập nhật citations."""
    mock_llm_reply = (
        "Phần 1: Thông tin học phần:\n- Mã học phần: MAT3507 [1]\n"
        "- Tên học phần: Cơ sở dữ liệu\n- Số tín chỉ: 4 tín chỉ [1]\n"
        "Phần 2: Môn học cung cấp kiến thức nền tảng về CSDL quan hệ [2]."
    )

    def fake_generate_grounded_answer(request, answerer, answer=None):
        citations = []
        if answer and answer.citations:
            citations.extend(answer.citations)
        return (mock_llm_reply, citations)

    monkeypatch.setattr("app.hus.chat.generate_grounded_answer", fake_generate_grounded_answer)

    req = HUSQuestion(
        question="Môn CSDL bao nhiêu tín?",
        major="computer_science",
        version="QD3568-2023",
    )
    result = chat(req, answerer)

    assert result.mode == "hus_rag"
    assert result.generation_mode == "grounded_llm"
    assert result.reply == mock_llm_reply
    assert result.hus_answer is not None
    assert result.hus_answer.status == "answered"
    assert result.hus_answer.citations == answerer.answer(req).citations


def test_chat_integration_extractive_mode_when_llm_none(answerer, monkeypatch):
    """Kịch bản 7B: Khi LLM trả về None (tắt/lỗi) -> result.generation_mode == 'extractive' và reply gốc."""
    monkeypatch.setattr("app.hus.chat.generate_grounded_answer", lambda *args, **kwargs: None)

    req = HUSQuestion(
        question="Môn CSDL bao nhiêu tín?",
        major="computer_science",
        version="QD3568-2023",
    )
    result = chat(req, answerer)

    assert result.mode == "hus_rag"
    assert result.generation_mode == "extractive"
    assert result.hus_answer is not None
    assert result.reply == result.hus_answer.reply


# ============================================================================
# Kịch bản 8: Kiểm tra điều kiện tiên quyết (Prerequisites Enrichment)
# ============================================================================


def test_prerequisite_enrichment_no_prerequisites(answerer, monkeypatch):
    """Kịch bản 8A: Môn học không có tiên quyết (MAT2400) -> Prompt ghi rõ 'Không' và liệt kê môn tiếp theo."""
    captured_prompts: list[str] = []

    def mock_post(client_self, url, *args, **kwargs):
        json_body = kwargs.get("json", {})
        parts = json_body.get("contents", [{}])[0].get("parts", [{}])
        if parts:
            captured_prompts.append(parts[0].get("text", ""))
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json=_mock_gemini_success_response("Phản hồi mock"), request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post)
    monkeypatch.setattr(
        "app.hus.llm_answerer.get_settings",
        lambda: SimpleNamespace(
            hus_rag_llm_enabled=True,
            gemini_api_key="mock-valid-key",
            hus_rag_llm_model="gemini-3.5-flash-lite",
            gemini_base_url="",
            gemini_model="gemini-3.5-flash-lite",
            recommendation_llm_enabled=True,
        ),
    )

    req = HUSQuestion(
        question="nội dung của đại số tuyến tính",
        major="data_science",
        version="QD3569-2023",
        allow_generated_reference=True,
    )
    result = generate_grounded_answer(req, answerer)
    assert result is not None
    assert len(captured_prompts) == 1
    prompt_str = captured_prompts[0]

    assert "- Điều kiện tiên quyết: Không (môn học không yêu cầu môn tiên quyết)" in prompt_str
    assert "- Là học phần tiên quyết cho các môn: MAT2403" in prompt_str


def test_prerequisite_enrichment_with_prerequisites(answerer, monkeypatch):
    """Kịch bản 8B: Môn học có tiên quyết (MAT3507) -> Prompt ghi rõ mã môn và tên môn tiên quyết."""
    captured_prompts: list[str] = []

    def mock_post(client_self, url, *args, **kwargs):
        json_body = kwargs.get("json", {})
        parts = json_body.get("contents", [{}])[0].get("parts", [{}])
        if parts:
            captured_prompts.append(parts[0].get("text", ""))
        req = httpx.Request("POST", str(url))
        return httpx.Response(200, json=_mock_gemini_success_response("Phản hồi mock"), request=req)

    monkeypatch.setattr(httpx.Client, "post", mock_post)
    monkeypatch.setattr(
        "app.hus.llm_answerer.get_settings",
        lambda: SimpleNamespace(
            hus_rag_llm_enabled=True,
            gemini_api_key="mock-valid-key",
            hus_rag_llm_model="gemini-3.5-flash-lite",
            gemini_base_url="",
            gemini_model="gemini-3.5-flash-lite",
            recommendation_llm_enabled=True,
        ),
    )

    req = HUSQuestion(
        question="Môn CSDL bao nhiêu tín?",
        major="computer_science",
        version="QD3568-2023",
    )
    result = generate_grounded_answer(req, answerer)
    assert result is not None
    assert len(captured_prompts) == 1
    prompt_str = captured_prompts[0]

    assert "MAT2505" in prompt_str
    assert "Lập trình cơ bản" in prompt_str
