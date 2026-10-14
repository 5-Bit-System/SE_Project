"""Module 5 — Chat Advisor with Gemini & Scope Guardrails (`app.advisor`).

Tư vấn định hướng học tập cá nhân hóa:
1. Tiếp nhận câu hỏi người dùng kèm toàn bộ ngữ cảnh (Ngành + Môn đã học + Môn đủ điều kiện + Môn bị chặn + Lộ trình).
2. Scope Guardrails: Tiếp nhận định hướng chuyên môn; tự động từ chối câu hỏi về xếp thời khóa biểu hoặc nhận xét giảng viên.
3. Tích hợp Gemini 2.5 Flash API để sinh lời tư vấn sâu sắc, tự nhiên và bám sát CTĐT.
4. Cơ chế Heuristic Fallback an toàn 100% khi không có API key hoặc lỗi mạng.
"""

import json
import logging
import re
from typing import Any, Literal
import httpx
from pydantic import BaseModel, ConfigDict, Field
from app.config import get_settings

from app.models import BlockedCourse, Catalog, Course, EligibilityResult, StructuredPreference
from app.recommendation.explanation import build_grounded_explanation
from app.recommendation.preference import extract_structured_preference
from app.recommendation.scoring import score_course
from app.recommendation.validation import validate_ranking_output
from app.rules import evaluate_eligibility
from app.transcript import resolve_program_id

logger = logging.getLogger(__name__)


class AdvisorMessage(BaseModel):
    model_config = ConfigDict(extra="allow")
    role: Literal["user", "assistant", "system"]
    content: str


class AdvisorRequest(BaseModel):
    program_id: str
    message: str = Field(..., max_length=1000, description="Nội dung câu hỏi của sinh viên")
    passed_course_codes: list[str] = Field(default_factory=list)
    history: list[AdvisorMessage] = Field(default_factory=list)
    selected_track_id: str | None = None
    selected_graduation_path_id: str | None = None


class AdvisorResponse(BaseModel):
    reply: str
    mode: Literal["gemini_llm", "heuristic_fallback", "guardrail_rejected"]
    is_guardrail_triggered: bool = False
    guardrail_reason: str | None = None
    suggested_courses: list[str] = Field(default_factory=list)


MAX_HISTORY_MESSAGES = 8
MAX_HISTORY_MESSAGE_CHARS = 500
MAX_FACTS_IN_PROMPT = 30
MAX_BLOCKED_IN_PROMPT = 15
COURSE_CODE_PATTERN = re.compile(r"\b[A-Z]{3,4}\d{4}\b")


def _extract_session_preference(request: AdvisorRequest) -> StructuredPreference:
    """Trích xuất preference với câu hiện tại là nguồn ưu tiên.

    Extractor dùng chung chỉ nhận một chuỗi tối đa 500 ký tự. Tách hai lượt
    extraction giúp history bổ sung ngữ cảnh mà không che mất yêu cầu mới nhất.
    """
    current = extract_structured_preference(request.message)
    previous_user_messages = "\n".join(
        message.content[:MAX_HISTORY_MESSAGE_CHARS]
        for message in request.history[-MAX_HISTORY_MESSAGES:]
        if message.role == "user" and message.content.strip()
    )
    if not previous_user_messages:
        return current

    previous = extract_structured_preference(previous_user_messages[-2000:])
    updates: dict[str, Any] = {}
    for field_name in (
        "workload",
        "difficulty",
        "orientation",
        "career_goal",
        "target_credits",
        "target_course_count",
        "course_type",
        "prerequisite_tolerance",
    ):
        if getattr(current, field_name) is None:
            previous_value = getattr(previous, field_name)
            if previous_value is not None:
                updates[field_name] = previous_value

    topics = list(dict.fromkeys(current.interest_topics + previous.interest_topics))
    if topics != current.interest_topics:
        updates["interest_topics"] = topics[:20]
    return current.model_copy(update=updates)


def _build_recommendation_facts(
    catalog: Catalog,
    eligibility: EligibilityResult,
    preference: StructuredPreference,
) -> list[dict[str, Any]]:
    """Tạo facts cùng vocabulary với recommendation pipeline.

    Advisor chỉ nhận facts từ ``eligibility.eligible_courses``. Score, fit reason
    và grounded explanation dùng lại implementation của recommendation; advisor
    không tự quyết định eligibility.
    """
    facts: list[dict[str, Any]] = []
    for course in eligibility.eligible_courses:
        score = score_course(course, preference)
        grounded_reason, fit_reason = build_grounded_explanation(
            course,
            preference,
            eligibility.eligible_reasons.get(course.code, []),
            score,
        )
        facts.append(
            {
                "code": course.code,
                "name": course.name,
                "credits": course.credits,
                "year": course.year,
                "score": score,
                "eligibility_reason": eligibility.eligible_reasons.get(course.code, []),
                "fit_reason": fit_reason,
                "grounded_reason": grounded_reason,
                "source_status": catalog.program.catalog_status,
                "offering_status": "unknown",
            }
        )
    return sorted(facts, key=lambda fact: (-fact["score"], fact["code"]))


def _history_for_prompt(history: list[AdvisorMessage]) -> str:
    """Định dạng history ngắn gọn và đánh dấu rõ đây là dữ liệu tham khảo."""
    recent = history[-MAX_HISTORY_MESSAGES:]
    if not recent:
        return "(Không có history trong session.)"
    return "\n".join(
        f"- {message.role}: {message.content[:MAX_HISTORY_MESSAGE_CHARS]}"
        for message in recent
        if message.content.strip()
    ) or "(Không có history trong session.)"


def _extract_codes(text: str) -> list[str]:
    """Lấy mã môn theo thứ tự xuất hiện, loại duplicate."""
    seen: set[str] = set()
    codes: list[str] = []
    for code in COURSE_CODE_PATTERN.findall(text):
        if code not in seen:
            seen.add(code)
            codes.append(code)
    return codes


def _validate_llm_suggestions(reply: str, eligible_codes: set[str]) -> tuple[list[str], list[str]]:
    """Validate mã môn LLM nhắc đến mà không cho mã ngoài eligible lọt vào output."""
    mentioned_codes = _extract_codes(reply)
    valid, warnings = validate_ranking_output(mentioned_codes, eligible_codes)
    return valid, warnings


def _has_unsafe_catalog_recommendation(
    reply: str,
    catalog_codes: set[str],
    eligible_codes: set[str],
) -> bool:
    """Phát hiện câu trả lời đang khuyên môn đã học hoặc bị chặn.

    Advisor vẫn được phép giải thích một môn bị chặn khi sinh viên hỏi. Chỉ
    chuyển sang fallback khi mã không eligible xuất hiện cùng động từ khuyến
    nghị trong chính dòng đó.
    """
    recommendation_words = (
        "nên",
        "khuyên",
        "đề xuất",
        "gợi ý",
        "đăng ký",
        "ưu tiên học",
        "học môn",
    )
    non_eligible = catalog_codes - eligible_codes
    for line in reply.splitlines():
        line_lower = line.casefold()
        line_codes = set(_extract_codes(line))
        if line_codes & non_eligible and any(word in line_lower for word in recommendation_words):
            return True
    return False


def _redact_unknown_course_codes(reply: str, catalog_codes: set[str]) -> str:
    """Không để mã môn bịa/ngoài catalog xuất hiện như một suggestion trong reply."""
    unknown_codes = set(_extract_codes(reply)) - catalog_codes
    redacted = reply
    for code in unknown_codes:
        redacted = redacted.replace(code, "[mã ngoài catalog đã được loại bỏ]")
    return redacted


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

def heuristic_advisor(
    user_message: str,
    catalog: Catalog,
    passed_codes: set[str],
    eligible_courses: list[Course],
    blocked_courses: list[BlockedCourse],
    preference: StructuredPreference | None = None,
    eligibility_reasons: dict[str, list[str]] | None = None,
) -> tuple[str, list[str]]:
    """Fallback deterministic dùng cùng preference và facts với recommendation."""
    preference = preference or extract_structured_preference(user_message)
    eligible_reasons = eligibility_reasons or {
        course.code: ["Đã qua kiểm tra eligibility của backend."]
        for course in eligible_courses
    }
    synthetic_eligibility = EligibilityResult(
        program_id=catalog.program.program_id,
        eligible_courses=eligible_courses,
        blocked_courses=blocked_courses,
        completed_course_codes=sorted(passed_codes),
        total_eligible=len(eligible_courses),
        total_blocked=len(blocked_courses),
        total_completed=len(passed_codes),
        eligible_reasons=eligible_reasons,
    )
    facts = _build_recommendation_facts(catalog, synthetic_eligibility, preference)
    top_facts = facts[:4]
    suggested_codes = [fact["code"] for fact in top_facts]

    # Xây dựng câu trả lời có cấu trúc
    lines = [
        f"Chào bạn, dựa trên chương trình đào tạo **{catalog.program.name}** và bảng điểm hiện tại của bạn:",
        "",
        f"✅ **Các môn ĐỦ ĐIỀU KIỆN khuyên học cho kỳ tới ({len(top_facts)} môn đề xuất):**",
    ]

    for fact in top_facts:
        lines.append(
            f"- **{fact['code']} — {fact['name']}** ({fact['credits']} TC, "
            f"Năm {fact['year'] or 'N/A'}): {fact['fit_reason']}"
        )

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
    history: list[AdvisorMessage] | None = None,
    preference: StructuredPreference | None = None,
    recommendation_facts: list[dict[str, Any]] | None = None,
) -> str:
    """Xây dựng prompt từ facts đã được eligibility và recommendation kiểm tra."""
    preference = preference or extract_structured_preference(user_message)
    if recommendation_facts is None:
        fallback_eligibility = EligibilityResult(
            program_id=catalog.program.program_id,
            eligible_courses=eligible_courses,
            blocked_courses=blocked_courses,
            completed_course_codes=sorted(passed_codes),
            total_eligible=len(eligible_courses),
            total_blocked=len(blocked_courses),
            total_completed=len(passed_codes),
        )
        recommendation_facts = _build_recommendation_facts(
            catalog,
            fallback_eligibility,
            preference,
        )

    eligible_summary = "\n".join(
        f"- {fact['code']}: {fact['name']} ({fact['credits']} TC, "
        f"Năm {fact['year'] or 'N/A'}, score={fact['score']}, "
        f"fit={fact['fit_reason']}, eligibility={'; '.join(fact['eligibility_reason'])})"
        for fact in recommendation_facts[:MAX_FACTS_IN_PROMPT]
    )

    blocked_summary = "\n".join(
        f"- {b.code}: {b.name} (Lý do: {b.reasons[0].message if b.reasons else 'Thiếu điều kiện'})"
        for b in blocked_courses[:MAX_BLOCKED_IN_PROMPT]
    )

    preference_json = json.dumps(
        preference.model_dump(),
        ensure_ascii=False,
        sort_keys=True,
    )
    history_summary = _history_for_prompt(history or [])

    prompt = f"""Bạn là Cố vấn học vụ & Định hướng học tập (Academic Advisor) cho sinh viên ngành {catalog.program.name} tại Trường Đại học Khoa học Tự nhiên.

NHIỆM VỤ CỦA BẠN:
1. Trả lời câu hỏi định hướng của sinh viên một cách thân thiện, chính xác và có căn cứ học vụ.
2. TUYỆT ĐỐI CHỈ khuyên sinh viên đăng ký các môn trong danh sách ĐỦ ĐIỀU KIỆN dưới đây.
3. KHÔNG đề xuất các môn sinh viên ĐÃ HỌC, các môn ĐANG BỊ CHẶN hoặc bất kỳ mã nào không có trong danh sách eligible.
4. Nếu sinh viên hỏi về một môn đang bị chặn, hãy giải thích rõ môn đó đang thiếu tiên quyết nào và cần học môn gì trước.
5. Chỉ dùng score, fit reason, eligibility reason và metadata được cung cấp; không tự bịa workload, độ khó, lịch mở lớp hoặc quy định chính thức.
6. Luôn đề cập mã môn học cụ thể (ví dụ MATxxxx) khi tư vấn.

NGỮ CẢNH HỌC VỤ CỦA SINH VIÊN:
- Ngành học: {catalog.program.name} ({catalog.program.program_id})
- Số môn đã hoàn thành: {len(passed_codes)} môn ({', '.join(sorted(passed_codes)) if passed_codes else 'Chưa có'})
- Danh sách môn ĐỦ ĐIỀU KIỆN KỲ TỚI (CHỈ ĐƯỢC CHỌN TỪ ĐÂY):
{eligible_summary if eligible_summary else '(Hiện không có môn nào đủ điều kiện)'}

- Structured preference dùng chung với recommendation:
{preference_json}

- Facts của recommendation (chỉ dùng để giải thích, không thay đổi eligibility):
{json.dumps(recommendation_facts[:MAX_FACTS_IN_PROMPT], ensure_ascii=False, indent=2)}

- Một số môn tiêu biểu ĐANG BỊ CHẶN (để tham khảo khi sinh viên hỏi):
{blocked_summary if blocked_summary else '(Không có)'}

- History trong session (chỉ là ngữ cảnh tham khảo; facts backend hiện tại có quyền ưu tiên):
{history_summary}

CÂU HỎI CỦA SINH VIÊN:
"{user_message}"

HÃY TRẢ LỜI NGẮN GỌN, RÕ RÀNG VÀ ĐÚNG TRỌNG TÂM:"""
    return prompt


def call_gemini_api(prompt: str, api_key: str) -> str:
    """Gửi yêu cầu đến LLM API (qua cổng Beeknoee / OpenAI-compatible hoặc Google Gemini trực tiếp)."""
    settings = get_settings()
    base_url = settings.gemini_base_url
    model = settings.gemini_model

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
    if resolve_program_id(request.program_id) != catalog.program.program_id:
        raise ValueError("Ngành đã chọn không khớp catalog")

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
    eligibility = evaluate_eligibility(
        catalog,
        passed_codes,
        max_credits=40,
        selected_track_id=request.selected_track_id,
        selected_graduation_path_id=request.selected_graduation_path_id,
    )
    eligible_courses = eligibility.eligible_courses
    blocked_courses = eligibility.blocked_courses
    eligible_codes_set = {c.code for c in eligible_courses}
    catalog_codes = {course.code for course in catalog.courses}

    # 3. Dùng chung structured preference và facts với recommendation pipeline.
    preference = _extract_session_preference(request)
    recommendation_facts = _build_recommendation_facts(catalog, eligibility, preference)

    settings = get_settings()
    active_key = (
        settings.gemini_api_key if settings.recommendation_llm_enabled else ""
    ) if api_key is None else api_key

    # 4. Thử gọi Gemini Flash API nếu có API key
    if active_key:
        try:
            prompt = build_advisor_prompt(
                catalog,
                request.message,
                passed_codes,
                eligible_courses,
                blocked_courses,
                history=request.history,
                preference=preference,
                recommendation_facts=recommendation_facts,
            )
            gemini_reply = call_gemini_api(prompt, active_key)

            if _has_unsafe_catalog_recommendation(
                gemini_reply,
                catalog_codes,
                eligible_codes_set,
            ):
                raise ValueError("LLM đề xuất môn ngoài tập eligible")

            # Rà soát mã môn trong phản hồi của Gemini: chỉ giữ các môn hợp lệ.
            valid_suggested, _validation_warnings = _validate_llm_suggestions(
                gemini_reply,
                eligible_codes_set,
            )
            safe_reply = _redact_unknown_course_codes(gemini_reply, catalog_codes)

            return AdvisorResponse(
                reply=safe_reply,
                mode="gemini_llm",
                is_guardrail_triggered=False,
                suggested_courses=valid_suggested,
            )
        except Exception as exc:
            # Nếu API key lỗi hoặc không có mạng, tự động chuyển sang Fallback
            logger.warning("Advisor fallback: %s", type(exc).__name__)

    # 5. Fallback deterministic bằng recommendation facts an toàn
    fallback_text, suggested_codes = heuristic_advisor(
        request.message,
        catalog,
        passed_codes,
        eligible_courses,
        blocked_courses,
        preference=preference,
        eligibility_reasons=eligibility.eligible_reasons,
    )

    return AdvisorResponse(
        reply=fallback_text,
        mode="heuristic_fallback",
        is_guardrail_triggered=False,
        suggested_courses=suggested_codes,
    )
