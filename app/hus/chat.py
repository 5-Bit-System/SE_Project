"""F1/F2/F3 and basic conversation, with no course recommendation dependencies."""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from app.hus.answering import HUSAnswerer, question_intent
from app.hus.llm.contracts import HUSGeneration, HUSRewriteHandler
from app.hus.llm.generation import generate_reply
from app.hus.llm_answerer import generate_grounded_answer
from app.hus.retrieval import _tokens
from app.schemas.hus import HUSAnswer, HUSQuestion


class HUSChatReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["basic_chat", "hus_rag"]
    reply: str
    hus_answer: HUSAnswer | None = None
    generation: HUSGeneration | None = Field(default=None, exclude_if=lambda value: value is None)
    interpretation: HUSGeneration | None = Field(default=None, exclude_if=lambda value: value is None)
    _generation_mode: Literal["grounded_llm", "extractive"] | None = PrivateAttr(default=None)

    @property
    def generation_mode(self) -> Literal["grounded_llm", "extractive"] | None:
        return self._generation_mode


def basic_reply(question: str) -> str | None:
    text = " ".join(_tokens(question))
    if text == 'cach doc nguon':
        return ('Với câu trả lời dựa trên dữ liệu, đọc nội dung và phiên bản nguồn kèm theo. '
                'Các thẻ dẫn chứng bên dưới ghi tên nguồn và trạng thái review. '
                'Bấm tên nguồn để mở tài liệu khi có liên kết đã kiểm tra. '
                'Nguồn chưa xác minh hiện hành không xác nhận hiệu lực hiện tại; '
                'nhãn “kiến thức AI” là nội dung tham khảo do AI sinh, không phải nguồn chính thức.')
    if text == 'cach bat noi dung ai':
        return ('Đánh dấu “Cho phép kiến thức AI tham khảo” bên dưới ô nhập câu hỏi, '
                'rồi chọn câu trong mục Tìm hiểu môn học. Bạn tự quyết định quyền này; '
                'đổi ngành sẽ tắt lại. Nội dung AI không phải đề cương hay quy định đánh giá chính thức.')
    if (text in {"chao", "xin chao", "chao ban", "xin chao ban", "hi", "hello", "alo"}
            or re.fullmatch(r'(?:xin )?chao(?: ban)? chuc (?:ban )?(?:mot )?ngay (?:tot lanh|vui ve)', text)):
        return "Chào bạn! Bạn muốn tìm hiểu về ngành học, chương trình đào tạo hay một học phần?"
    if text in {"cam on", "cam on ban", "thanks", "thank you", "ok cam on"}:
        return "Rất vui được giúp bạn. Bạn có thể hỏi tiếp về ngành học hoặc học phần."
    if text in {"tam biet", "bye", "hen gap lai", "goodbye"}:
        return "Hẹn gặp lại bạn!"
    if text in {"ban la ai", "ban co the lam gi", "ban giup duoc gi", "toi co the hoi gi", "huong dan su dung"}:
        return ("Tôi hỗ trợ thông tin ngành học, dữ kiện chương trình và nội dung học phần. "
                "Bạn có thể hỏi giới thiệu ngành, tín chỉ hoặc tiên quyết theo mã môn. "
                "Câu hỏi cấp chương trình/nhóm không cần mã môn; chọn đúng ngành và phiên bản. "
                "Mỗi lượt hỏi một loại thông tin; câu cấp môn ghi lại mã hoặc tên đầy đủ của môn; "
                "câu sau không tự lấy môn từ câu trước. "
                "Nội dung học phần AI cần bật cho phép kiến thức AI tham khảo.")
    return None


def chat(request: HUSQuestion, answerer: HUSAnswerer, *,
         rewriter: HUSRewriteHandler | None = None) -> HUSChatReply:
    if request.dataset == "auto" and request.course_code is None and request.field is None:
        reply = basic_reply(request.question)
        if reply is not None:
            reply, generation = generate_reply(request, None, reply, rewriter=rewriter)
            return HUSChatReply(mode="basic_chat", reply=reply, generation=generation)
    dataset, _ = question_intent(request.question)
    decision_versions = {version for major, version in answerer.programs.values() if major == request.major}
    match_codes = getattr(answerer, "_matched_course_codes", None)
    if (request.dataset == "auto" and dataset == "f1" and request.version in decision_versions
            and not (match_codes and match_codes(request))):
        # The selector's decision version belongs to F2/F3, not F1 source editions.
        request = request.model_copy(update={"version": None})
    prepare = getattr(answerer, 'prepare_evidence', None)
    if request.allow_llm_rewrite and callable(prepare):
        plan = prepare(request)
        evidence = plan.evidence
        reply, generation = generate_reply(request, evidence, evidence.reply, rewriter=rewriter)
        answer = plan.materialize()
        if generation is None or not generation.used:
            reply = answer.reply
    else:
        answer = answerer.answer(request)
        reply, generation = generate_reply(request, answer, answer.reply, rewriter=rewriter)
    return HUSChatReply(mode="hus_rag", reply=reply, hus_answer=answer, generation=generation)


def workspace_chat(request: HUSQuestion, answerer: HUSAnswerer) -> HUSChatReply:
    result = chat(request, answerer)
    answer = result.hus_answer
    if answer is None or answer.status != "answered":
        return result
    if request.allow_llm_rewrite:
        mode = "grounded_llm" if result.generation and result.generation.used else "extractive"
        result._generation_mode = mode
        return result
    result._generation_mode = "extractive"
    grounded = generate_grounded_answer(request, answerer, answer=answer)
    if grounded is not None:
        reply, citations = grounded if isinstance(grounded, tuple) else (grounded, None)
        if reply:
            result.reply = reply
            result._generation_mode = "grounded_llm"
        if citations:
            result.hus_answer = answer.model_copy(update={"citations": citations})
    return result
