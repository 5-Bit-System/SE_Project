"""Direct LLM generation for HUS RAG answers when configured with an API key."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

from app.hus.answering import HUSAnswerer
from app.schemas.hus import HUSAnswer, HUSCitation, HUSQuestion

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class HUSLLMSettings:
    gemini_api_key: str
    gemini_base_url: str
    gemini_model: str
    recommendation_llm_enabled: bool
    hus_rag_llm_enabled: bool
    hus_rag_llm_model: str


def get_hus_llm_settings() -> HUSLLMSettings:
    load_dotenv(PROJECT_ROOT / ".env", override=False)
    rec_enabled = (
        os.getenv("RECOMMENDATION_LLM_ENABLED", "true")
        .strip()
        .casefold()
        not in {"0", "false", "no", "off"}
    )
    hus_enabled = (
        os.getenv("HUS_RAG_LLM_ENABLED", "true")
        .strip()
        .casefold()
        not in {"0", "false", "no", "off"}
    )
    return HUSLLMSettings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_base_url=os.getenv("GEMINI_BASE_URL", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip() or "gemini-3.5-flash-lite",
        recommendation_llm_enabled=rec_enabled,
        hus_rag_llm_enabled=hus_enabled,
        hus_rag_llm_model=os.getenv("HUS_RAG_LLM_MODEL", "gemini-3.5-flash-lite").strip() or "gemini-3.5-flash-lite",
    )


def get_settings() -> Any:
    try:
        from app.config import get_settings as _app_get_settings
        return _app_get_settings()
    except Exception:
        return get_hus_llm_settings()


def _redact_key(text: str, key: str) -> str:
    if not key or not isinstance(text, str):
        return text
    return text.replace(key, "[REDACTED_API_KEY]")


def call_gemini_llm(
    prompt: str,
    *,
    api_key: str,
    base_url: str = "",
    model: str = "gemini-3.8-flash",
) -> str:
    """Call Google Gemini API directly or via an OpenAI-compatible proxy."""
    model_name = model.removeprefix("models/").strip()

    # 1. OpenAI-compatible endpoint (e.g., Beeknoee proxy)
    if base_url and "generativelanguage.googleapis.com" not in base_url:
        endpoint = base_url.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            endpoint = f"{endpoint}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Bạn là trợ lý AI học vụ của Trường Đại học Khoa học Tự nhiên (HUS - ĐHQGHN). "
                        "Hãy trả lời câu hỏi của sinh viên một cách tự nhiên, mạch lạc, chính xác và bám sát thông tin được cung cấp."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 4000,
        }
        with httpx.Client(timeout=30.0) as client:
            try:
                resp = client.post(endpoint, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                choices = data.get("choices", [])
                if not choices:
                    raise ValueError("Proxy API không trả về choice nào.")
                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    raise ValueError("Nội dung phản hồi từ LLM API rỗng.")
                return content.strip()
            except Exception as exc:
                if api_key and api_key in str(exc):
                    clean_msg = _redact_key(str(exc), api_key)
                    raise RuntimeError(f"Lỗi khi gọi Proxy API ({clean_msg})") from None
                raise

    # 2. Google AI Studio / Generative Language API directly
    models_to_try = [model_name]
    if "lite" in model_name.lower():
        fallback_candidates = (
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-2.5-flash-lite",
        )
    else:
        fallback_candidates = (
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
        )

    for alt in fallback_candidates:
        if alt not in models_to_try:
            models_to_try.append(alt)

    last_error: Exception | None = None
    for cur_model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{cur_model}:generateContent"
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 4000,
            },
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 503:
                    LOGGER.warning("Model %s 503 high demand, trying next fallback model...", cur_model)
                    continue
                resp.raise_for_status()
                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise ValueError(f"Google Gemini API ({cur_model}) không trả về candidate nào.")
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts).strip()
                if not text:
                    raise ValueError(f"Nội dung phản hồi từ Gemini API ({cur_model}) rỗng.")
                if cur_model != model_name:
                    LOGGER.info("Successfully used fallback model %s instead of %s", cur_model, model_name)
                return text
        except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
            last_error = exc
            clean_msg = _redact_key(str(exc), api_key)
            LOGGER.warning("Call to %s failed (%s), trying next fallback...", cur_model, clean_msg)
            continue
        except Exception as exc:
            last_error = exc
            clean_msg = _redact_key(str(exc), api_key)
            LOGGER.warning("Call to %s failed unexpectedly (%s)", cur_model, clean_msg)
            break

    if last_error is not None:
        if api_key and api_key in str(last_error):
            clean_msg = _redact_key(str(last_error), api_key)
            raise RuntimeError(f"Lỗi khi gọi Gemini API ({clean_msg})") from None
        raise last_error
    raise RuntimeError("Tất cả các model Gemini đều không phản hồi.")


def generate_grounded_answer(
    request: HUSQuestion,
    answerer: HUSAnswerer,
    answer: HUSAnswer | None = None,
) -> tuple[str, list[HUSCitation]] | None:
    """Retrieve context and generate an intelligent natural language answer using Gemini."""
    try:
        settings = get_settings()
    except Exception:
        settings = get_hus_llm_settings()

    hus_rag_llm_enabled = getattr(
        settings,
        "hus_rag_llm_enabled",
        getattr(settings, "recommendation_llm_enabled", False),
    )
    if not hus_rag_llm_enabled:
        return None
    api_key = getattr(settings, "gemini_api_key", "").strip()
    if not api_key:
        return None

    try:
        bundle = answerer.retrieve_context(request, top_k=5)
    except Exception as exc:
        LOGGER.warning("Context retrieval failed for LLM generation: %s", exc)
        return None

    # Don't invoke LLM for out-of-scope or unparseable queries with zero context
    if bundle.intent_source == "none" or (not bundle.top_k_chunks and not bundle.structured_data):
        return None

    # Collect citations: start with base answer citations so primary authoritative citations are preserved first
    llm_citations: list[HUSCitation] = []
    used_ids: set[str] = set()
    existing_signatures = set()
    if answer is not None and answer.citations:
        for cit in answer.citations:
            llm_citations.append(cit)
            used_ids.add(str(cit.citation_id))
            existing_signatures.add((cit.dataset, cit.source_id, cit.quote))

    # Then append citations from retrieved Top-K chunks (if any)
    for c in bundle.top_k_chunks:
        if c.citation is not None:
            sig = (c.citation.dataset, c.citation.source_id, c.citation.quote)
            if sig not in existing_signatures:
                new_cit = c.citation
                if str(new_cit.citation_id) in used_ids:
                    new_cit = new_cit.model_copy(update={"citation_id": str(len(llm_citations) + 1)})
                llm_citations.append(new_cit)
                used_ids.add(str(new_cit.citation_id))
                existing_signatures.add(sig)

    # Ensure citation IDs are sequential "1", "2", ...
    llm_citations = [
        cit.model_copy(update={"citation_id": str(i)})
        for i, cit in enumerate(llm_citations, 1)
    ]

    # Build prompt context
    context_sections = []

    # A. Structured course/program facts (F2)
    course_fact = bundle.structured_data.get("course")
    if course_fact:
        c_lines = [
            f"- Mã học phần: {course_fact.get('course_code')}",
            f"- Tên học phần: {course_fact.get('course_name')}",
            f"- Số tín chỉ: {course_fact.get('credits')}",
        ]
        if course_fact.get("hours"):
            c_lines.append(f"- Phân bổ giờ học: {json.dumps(course_fact['hours'], ensure_ascii=False)}")
        if course_fact.get("prerequisites_raw"):
            c_lines.append(f"- Điều kiện tiên quyết (theo dòng nguồn): {'; '.join(str(p) for p in course_fact['prerequisites_raw'] if p)}")
        context_sections.append("### Dữ kiện học phần chính thức (F2):\n" + "\n".join(c_lines))

    prog_fact = bundle.structured_data.get("program")
    if prog_fact:
        p_lines = [
            f"- Ngành: {prog_fact.get('major_name')}",
            f"- Phiên bản CTĐT: {prog_fact.get('version')}",
            f"- Tổng tín chỉ yêu cầu toàn khóa: {prog_fact.get('credits_required')}",
        ]
        if prog_fact.get("group_rules"):
            p_lines.append("- Các khối/nhóm kiến thức trong khung chương trình:")
            for grp in prog_fact["group_rules"][:10]:
                p_lines.append(f"  * Nhóm {grp.get('group_key')}: {grp.get('group_title')} (Tối thiểu: {grp.get('min_credits_if_selected')} tín chỉ)")
        context_sections.append("### Dữ kiện chương trình đào tạo (F2):\n" + "\n".join(p_lines))

    # B. Retrieved textual excerpts (Top-K Chunks F1/F3)
    if bundle.top_k_chunks:
        chunk_lines = []
        for c in bundle.top_k_chunks:
            source_tag = f"[{c.rank}] ({c.dataset}/{c.field or 'info'}"
            if c.course_code:
                source_tag += f" - {c.course_code}"
            source_tag += ")"
            chunk_lines.append(f"{source_tag}:\n{c.body.strip()}\n")
        context_sections.append("### Các đoạn trích dẫn tài liệu liên quan:\n" + "\n".join(chunk_lines))

    prompt = (
        "Bạn là trợ lý AI học vụ của Trường Đại học Khoa học Tự nhiên (HUS - ĐHQGHN).\n"
        f"Sinh viên đang hỏi: \"{request.question}\"\n"
        f"Phạm vi: Ngành {request.major}, Phiên bản {bundle.version or 'chính thức'}.\n\n"
        "Dưới đây là các thông tin chính thức và trích đoạn tài liệu đã được đối chiếu từ hệ thống HUS:\n"
        "----------------------------------------\n"
        f"{chr(10).join(context_sections)}\n"
        "----------------------------------------\n\n"
        "HƯỚNG DẪN TRẢ LỜI CHO SINH VIÊN:\n"
        "1. Trả lời đúng trọng tâm trước tiên (Answer-first): Đi thẳng vào nội dung sinh viên hỏi ngay câu đầu tiên. Tuyệt đối không mở bài rườm rà hay chào hỏi thừa thãi.\n"
        "2. Bố cục linh hoạt và tự nhiên theo đúng câu hỏi (TUYỆT ĐỐI KHÔNG chia mục theo khuôn mẫu cứng nhắc 1, 2, 3, 4 hay Phần 1, Phần 2, Phần 3, Phần 4):\n"
        "   - Nếu sinh viên hỏi về học phần/môn học (khi có dữ kiện học phần F2): Mở đầu với thông tin học phần ngắn gọn (dạng '### Thông tin học phần' gồm các gạch đầu dòng: Mã học phần, Tên học phần, Số tín chỉ, Phân bổ thời lượng, Điều kiện tiên quyết nếu có), sau đó giải thích trực tiếp nội dung hoặc yêu cầu của câu hỏi.\n"
        "   - Nếu sinh viên hỏi về chương trình đào tạo, mục tiêu ngành, hoặc cơ hội nghề nghiệp: Trình bày mạch lạc theo các nhóm ý tự nhiên của chủ đề đó (ví dụ: mục tiêu đào tạo, cấu trúc khối kiến thức, hoặc các vị trí việc làm). Không áp đặt bố cục của môn học hay đưa vào lời khuyên học tập không liên quan.\n"
        "   - Nếu là câu hỏi tra cứu dữ kiện ngắn (ví dụ: số tín chỉ, môn tiên quyết, thời lượng môn): Trả lời súc tích, ngắn gọn (1 - 3 câu), đi thẳng vào đáp án.\n"
        "   - Nếu là câu hỏi tìm hiểu nội dung môn học hoặc tổng quan: Giải thích mạch lạc, súc tích (khoảng 200 - 400 từ), sử dụng các đoạn văn ngắn hoặc gạch đầu dòng rõ ràng.\n"
        "3. Tuyệt đối chính xác về số liệu: Giữ nguyên vẹn mã môn, số tín chỉ, phân bổ số tiết và điều kiện tiên quyết theo dữ liệu F2 đã cung cấp. Không tự ý suy diễn hoặc thay đổi số liệu.\n"
        "4. Dẫn nguồn minh bạch: Khi sử dụng thông tin từ các đoạn trích dẫn tài liệu ở trên, hãy gắn số thứ tự trích dẫn dạng [1], [2],... tương ứng vào cuối câu hoặc mệnh đề.\n"
        "5. Giọng điệu cố vấn học vụ: Lịch sự, khách quan và đáng tin cậy. Chỉ trả lời dựa trên dữ liệu đã cung cấp. Nếu dữ liệu trên không đề cập đến thông tin sinh viên hỏi, hãy trung thực thông báo tài liệu chưa có thông tin, tuyệt đối không bịa đặt."
    )

    model = (
        getattr(settings, "hus_rag_llm_model", None)
        or getattr(settings, "gemini_model", "gemini-3.5-flash-lite")
    )
    base_url = getattr(settings, "gemini_base_url", "")

    try:
        reply_text = call_gemini_llm(
            prompt,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        return (reply_text, llm_citations)
    except Exception as exc:
        clean_msg = _redact_key(str(exc), api_key)
        LOGGER.warning("Gemini LLM call failed, falling back to extractive answer: %s", clean_msg)
        return None

