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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{cur_model}:generateContent?key={api_key}"
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
                resp = client.post(url, json=payload)
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
            LOGGER.warning("Call to %s failed (%s), trying next fallback...", cur_model, exc)
            continue
        except Exception as exc:
            last_error = exc
            break

    if last_error is not None:
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
        "HƯỚNG DẪN TRẢ LỜI CHO SINH VIÊN (ĐỘ DÀI VỪA PHẢI, KHOẢNG 500 - 700 TỪ):\n"
        "1. Trả lời với độ dài vừa phải, súc tích, mạch lạc (khoảng 500 - 700 từ), tránh quá dài dòng lê thê nhưng vẫn giải thích rõ ràng, đầy đủ bản chất.\n"
        "2. TUYỆT ĐỐI giữ nguyên tính chính xác của các số liệu cứng: số tín chỉ, mã học phần, số tiết lý thuyết/thực hành, điều kiện tiên quyết (không nhầm lẫn giữa mã học phần hiện tại và mã học phần tiên quyết).\n"
        "3. QUY TẮC BẮT BUỘC VỀ BỐ CỤC: THÔNG TIN HỌC PHẦN LUÔN LUÔN PHẢI HIỂN THỊ NGAY Ở ĐẦU CÂU TRẢ LỜI:\n"
        "   - Phần 1: Thông tin học phần (BẮT BUỘC Ở ĐẦU TIÊN): Trình bày ngắn gọn, rõ ràng thành các gạch đầu dòng: Mã học phần, Tên học phần, Số tín chỉ, Phân bổ thời lượng (Lý thuyết, Thực hành, Tự học), Điều kiện tiên quyết.\n"
        "   - Phần 2: Tổng quan & Vị trí môn học: Tóm lược súc tích (1 đoạn ngắn) về vai trò nền tảng của môn học và ý nghĩa đối với ngành học/thực tiễn.\n"
        "   - Phần 3: Nội dung kiến thức trọng tâm: Trình bày các chủ đề kiến thức cốt lõi, giải thích ngắn gọn, rõ ràng bản chất và ứng dụng của từng chủ đề.\n"
        "   - Phần 4: Lời khuyên học tập & Lưu ý: 2-3 lời khuyên ngắn gọn để học tốt, kèm chú thích nhẹ nhàng về việc tham khảo đề cương chính thức từ Khoa/Bộ môn.\n"
        "4. Khi trích dẫn hoặc sử dụng luận điểm từ các đoạn trích dẫn tài liệu ở mục B, hãy gắn số thứ tự trích dẫn dạng [1], [2],... tương ứng với số thứ tự của đoạn trích dẫn vào cuối câu hoặc mệnh đề.\n"
        "5. Không bịa đặt thêm các quy định học vụ hoặc môn học không có trong dữ liệu trên."
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
        LOGGER.warning("Gemini LLM call failed, falling back to extractive answer: %s", exc)
        return None

