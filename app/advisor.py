"""Module 5 — Chat Advisor with Gemini & Scope Guardrails (`app.advisor`).

Tư vấn định hướng học tập cá nhân hóa:
1. Tiếp nhận câu hỏi người dùng kèm toàn bộ ngữ cảnh (Ngành + Môn đã học + Môn đủ điều kiện + Môn bị chặn + Lộ trình).
2. Scope Guardrails: Tiếp nhận định hướng chuyên môn; tự động từ chối câu hỏi về xếp thời khóa biểu hoặc nhận xét giảng viên.
3. Tích hợp Gemini 2.5 Flash API để sinh lời tư vấn sâu sắc, tự nhiên và bám sát CTĐT.
4. Cơ chế Heuristic Fallback an toàn 100% khi không có API key hoặc lỗi mạng.
"""

import os
import re
from typing import Any, Literal
import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.models import BlockedCourse, Catalog, Course
from app.planner import generate_roadmap
from app.rules import evaluate_eligibility

# Load .env nếu có
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_BASE_URL = os.environ.get("GEMINI_BASE_URL", "").strip()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"


class AdvisorMessage(BaseModel):
    model_config = ConfigDict(extra="allow")
    role: Literal["user", "assistant", "system"]
    content: str


class AdvisorRequest(BaseModel):
    program_id: str
    message: str = Field(..., max_length=1000, description="Nội dung câu hỏi của sinh viên")
    passed_course_codes: list[str] = Field(default_factory=list)
    history: list[AdvisorMessage] = Field(default_factory=list)


class AdvisorResponse(BaseModel):
    reply: str
    mode: Literal["gemini_llm", "heuristic_fallback", "guardrail_rejected"]
    is_guardrail_triggered: bool = False
    guardrail_reason: str | None = None
    suggested_courses: list[str] = Field(default_factory=list)


# --- SCOPE GUARDRAILS ---

SCHEDULE_KEYWORDS = [
    "thời khóa biểu",
    "thời khoá biểu",
    "xếp lịch",
    "xếp thời khóa biểu",
    "lịch học đẹp",
    "tránh tiết",
    "kíp học",
    "trùng tiết",
    "lịch học buổi sáng",
    "lịch học buổi chiều",
    "học thứ 7",
    "học chủ nhật",
]

INSTRUCTOR_KEYWORDS = [
    "giảng viên",
    "thầy nào",
    "cô nào",
    "dễ tính",
    "khó tính",
    "cho điểm cao",
    "chấm điểm dễ",
    "qua môn dễ",
    "dễ qua môn",
    "thầy cô nào",
    "review giảng viên",
    "review thầy",
    "review cô",
    "xin điểm",
]


def check_scope_guardrails(message: str) -> tuple[bool, str | None, str | None]:
    """Kiểm tra câu hỏi của người dùng có nằm trong phạm vi tư vấn học thuật hay không.

    Trả về: (is_triggered, reason_type, rejection_message).
    """
    msg_lower = message.lower()

    # Kiểm tra hỏi xếp thời khóa biểu
    for kw in SCHEDULE_KEYWORDS:
        if kw in msg_lower:
            refusal = (
                "Hệ thống Explainable Course Recommender chỉ hỗ trợ tư vấn định hướng chuyên môn, "
                "chọn học phần và lộ trình kiến thức theo khung CTĐT. Hệ thống không hỗ trợ xếp thời khóa biểu "
                "cá nhân, chọn giờ học hay phân bổ kíp học. Bạn vui lòng sử dụng cổng đăng ký tín chỉ "
                "chính thức của Nhà trường để xem thời khóa biểu thực tế."
            )
            return True, "schedule_request", refusal

    # Kiểm tra hỏi đánh giá giảng viên
    for kw in INSTRUCTOR_KEYWORDS:
        if kw in msg_lower:
            refusal = (
                "Hệ thống tuân thủ nguyên tắc khách quan và bảo vệ tính công bằng học thuật: "
                "không đưa ra đánh giá, nhận xét hay so sánh về mức độ dễ/khó tính hoặc cách chấm điểm "
                "của các giảng viên. Bạn nên cân nhắc đăng ký học phần dựa trên nội dung kiến thức, "
                "môn tiên quyết và định hướng nghề nghiệp cá nhân."
            )
            return True, "instructor_evaluation", refusal

    return False, None, None


# --- HEURISTIC FALLBACK ADVISOR ---

TRACK_KEYWORDS = {
    "ai": ["máy học", "học máy", "trí tuệ nhân tạo", "ai", "machine learning", "deep learning"],
    "data": ["dữ liệu", "data", "khai phá", "thống kê", "phân tích dữ liệu", "big data"],
    "software": ["phần mềm", "lập trình", "web", "hệ thống", "công nghệ phần mềm", "thuật toán"],
    "math": ["toán", "giải tích", "đại số", "xác suất", "tối ưu", "mô hình"],
}


def heuristic_advisor(
    user_message: str,
    catalog: Catalog,
    passed_codes: set[str],
    eligible_courses: list[Course],
    blocked_courses: list[BlockedCourse],
) -> tuple[str, list[str]]:
    """Bộ tư vấn dự phòng bằng thuật toán Heuristic bám sát dữ liệu Rule Engine."""
    msg_lower = user_message.lower()

    # Tìm môn eligible phù hợp nhất với từ khóa trong câu hỏi
    scored_candidates: list[tuple[Course, int]] = []
    for c in eligible_courses:
        score = 0
        c_text = f"{c.code} {c.name} {getattr(c, 'name_en', '')} {c.block}".lower()

        # So khớp từ khóa trực tiếp
        for word in re.findall(r"\w+", msg_lower):
            if len(word) >= 2 and word in c_text:
                score += 2

        # Ưu tiên theo định hướng chủ đề
        for track_name, kws in TRACK_KEYWORDS.items():
            if any(k in msg_lower for k in kws) and any(k in c_text for k in kws):
                score += 3

        # Ưu tiên các môn thuộc năm sớm hơn nếu chưa có điểm
        if c.year:
            score += (5 - c.year)

        scored_candidates.append((c, score))

    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    top_picks = [c for c, _ in scored_candidates[:4]]
    if not top_picks and eligible_courses:
        top_picks = eligible_courses[:4]

    suggested_codes = [c.code for c in top_picks]

    # Xây dựng câu trả lời có cấu trúc
    lines = [
        f"Chào bạn, dựa trên chương trình đào tạo **{catalog.program.name}** và bảng điểm hiện tại của bạn:",
        "",
        f"✅ **Các môn ĐỦ ĐIỀU KIỆN khuyên học cho kỳ tới ({len(top_picks)} môn đề xuất):**",
    ]

    for c in top_picks:
        prereq_note = " (Không yêu cầu tiên quyết)" if not c.prerequisites else " (Đã thỏa mãn tiên quyết)"
        lines.append(f"- **{c.code} — {c.name}** ({c.credits} TC, Năm {c.year or 'N/A'}):{prereq_note}")

    if blocked_courses:
        sample_blocked = blocked_courses[:2]
        lines.append("")
        lines.append("⚠️ **Lưu ý các môn liên quan đang BỊ CHẶN do thiếu tiên quyết:**")
        for b in sample_blocked:
            r_msg = b.reasons[0].message if b.reasons else "Chưa đủ điều kiện"
            lines.append(f"- **{b.code} — {b.name}**: {r_msg}")

    lines.append("")
    lines.append("💡 *Gợi ý:* Hãy ưu tiên hoàn thành các môn cơ sở nhóm ngành trước để kịp mở khóa các môn chuyên đề nâng cao ở các kỳ tiếp theo.")
    lines.append("")
    lines.append("> ℹ️ *[Phản hồi từ Heuristic Advisor: Hệ thống quy tắc tự động bám sát CTĐT]*")

    return "\n".join(lines), suggested_codes


# --- GEMINI PROMPT & CLIENT ---

def build_advisor_prompt(
    catalog: Catalog,
    user_message: str,
    passed_codes: set[str],
    eligible_courses: list[Course],
    blocked_courses: list[BlockedCourse],
) -> str:
    """Xây dựng prompt chi tiết bảo đảm LLM chỉ tư vấn trong tập eligible và grounded theo CTĐT."""
    eligible_summary = "\n".join(
        f"- {c.code}: {c.name} ({c.credits} TC, Năm {c.year or 'N/A'})"
        for c in eligible_courses[:30]
    )

    blocked_summary = "\n".join(
        f"- {b.code}: {b.name} (Lý do: {b.reasons[0].message if b.reasons else 'Thiếu điều kiện'})"
        for b in blocked_courses[:15]
    )

    prompt = f"""Bạn là Cố vấn học vụ & Định hướng học tập (Academic Advisor) cho sinh viên ngành {catalog.program.name} tại Trường Đại học Khoa học Tự nhiên.

NHIỆM VỤ CỦA BẠN:
1. Trả lời câu hỏi định hướng của sinh viên một cách thân thiện, chính xác và có căn cứ học vụ.
2. TUYỆT ĐỐI CHỈ khuyên sinh viên đăng ký các môn trong danh sách ĐỦ ĐIỀU KIỆN dưới đây.
3. KHÔNG đề xuất các môn sinh viên ĐÃ HỌC hoặc các môn ĐANG BỊ CHẶN.
4. Nếu sinh viên hỏi về một môn đang bị chặn, hãy giải thích rõ môn đó đang thiếu tiên quyết nào và cần học môn gì trước.
5. Luôn đề cập mã môn học cụ thể (ví dụ MATxxxx) khi tư vấn.

NGỮ CẢNH HỌC VỤ CỦA SINH VIÊN:
- Ngành học: {catalog.program.name} ({catalog.program.program_id})
- Số môn đã hoàn thành: {len(passed_codes)} môn ({', '.join(sorted(passed_codes)) if passed_codes else 'Chưa có'})
- Danh sách môn ĐỦ ĐIỀU KIỆN KỲ TỚI (CHỈ ĐƯỢC CHỌN TỪ ĐÂY):
{eligible_summary if eligible_summary else '(Hiện không có môn nào đủ điều kiện)'}

- Một số môn tiêu biểu ĐANG BỊ CHẶN (để tham khảo khi sinh viên hỏi):
{blocked_summary if blocked_summary else '(Không có)'}

CÂU HỎI CỦA SINH VIÊN:
"{user_message}"

HÃY TRẢ LỜI NGẮN GỌN, RÕ RÀNG VÀ ĐÚNG TRỌNG TÂM:"""
    return prompt


def call_gemini_api(prompt: str, api_key: str) -> str:
    """Gửi yêu cầu đến LLM API (qua cổng Beeknoee / OpenAI-compatible hoặc Google Gemini trực tiếp)."""
    base_url = os.environ.get("GEMINI_BASE_URL", GEMINI_BASE_URL).strip()
    model = os.environ.get("GEMINI_MODEL", GEMINI_MODEL).strip() or "gemini-3.8-flash"

    # Tự động chuẩn hóa alias model nếu dùng cổng Beeknoee
    if "beeknoee" in base_url.lower():
        if model == "gemini-3.8-flash":
            model = "bee/gemini-3.8-flash"
        elif model == "gemini-3.7-flash":
            model = "bee/gemini-3.7-flash"
        elif model == "gemini-3.5-flash":
            model = "bee/gemini-3.5-flash"

    # Nếu cấu hình GEMINI_BASE_URL (ví dụ cổng Beeknoee: https://platform.beeknoee.com/api/v1)
    if base_url and "generativelanguage.googleapis.com" not in base_url:
        endpoint = base_url.rstrip("/")
        if not endpoint.endswith("/chat/completions"):
            endpoint = f"{endpoint}/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4,
            "max_tokens": 1024,
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("Beeknoee API không trả về choice nào.")
            content = choices[0].get("message", {}).get("content", "")
            if not content:
                raise ValueError("Nội dung phản hồi từ LLM API rỗng.")
            return content.strip()

    # Mặc định: Gọi trực tiếp Google Generative Language API
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 1024,
        },
    }

    with httpx.Client(timeout=25.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise ValueError("Gemini API không trả về candidate nào.")
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)
        if not text:
            raise ValueError("Nội dung phản hồi từ Gemini API rỗng.")
        return text.strip()


def chat_advisor(
    catalog: Catalog,
    request: AdvisorRequest,
    api_key: str | None = None,
) -> AdvisorResponse:
    """Điểm vào chính của Chat Advisor kết hợp Guardrails, Gemini Flash và Heuristic Fallback."""
    # 1. Chốt chặn phạm vi (Scope Guardrails)
    is_triggered, reason_type, rejection_msg = check_scope_guardrails(request.message)
    if is_triggered and rejection_msg:
        return AdvisorResponse(
            reply=rejection_msg,
            mode="guardrail_rejected",
            is_guardrail_triggered=True,
            guardrail_reason=reason_type,
            suggested_courses=[],
        )

    # 2. Đánh giá tính hợp lệ học vụ thực tế
    passed_codes = set(request.passed_course_codes)
    eligibility = evaluate_eligibility(catalog, passed_codes, max_credits=40)
    eligible_courses = eligibility.eligible_courses
    blocked_courses = eligibility.blocked_courses
    eligible_codes_set = {c.code for c in eligible_courses}

    active_key = GEMINI_API_KEY if api_key is None else api_key

    # 3. Thử gọi Gemini Flash API nếu có API key
    if active_key:
        try:
            prompt = build_advisor_prompt(
                catalog,
                request.message,
                passed_codes,
                eligible_courses,
                blocked_courses,
            )
            gemini_reply = call_gemini_api(prompt, active_key)

            # Rà soát mã môn trong phản hồi của Gemini: chỉ giữ các môn hợp lệ
            mentioned_codes = set(re.findall(r"\b[A-Z]{3,4}\d{4}\b", gemini_reply))
            valid_suggested = [c for c in mentioned_codes if c in eligible_codes_set]

            return AdvisorResponse(
                reply=gemini_reply,
                mode="gemini_llm",
                is_guardrail_triggered=False,
                suggested_courses=sorted(valid_suggested),
            )
        except Exception:
            # Nếu API key lỗi hoặc không có mạng, tự động chuyển sang Fallback
            pass

    # 4. Fallback Heuristic bằng code an toàn
    fallback_text, suggested_codes = heuristic_advisor(
        request.message,
        catalog,
        passed_codes,
        eligible_courses,
        blocked_courses,
    )

    return AdvisorResponse(
        reply=fallback_text,
        mode="heuristic_fallback",
        is_guardrail_triggered=False,
        suggested_courses=suggested_codes,
    )
