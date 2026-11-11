"""F1/F2/F3 and basic conversation, with no course recommendation dependencies."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.hus.answering import HUSAnswerer, question_intent
from app.hus.llm.contracts import HUSGeneration, HUSRewriteHandler
from app.hus.llm.generation import generate_reply
from app.hus.retrieval import _tokens
from app.schemas.hus import HUSAnswer, HUSQuestion


class HUSChatReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["basic_chat", "hus_rag"]
    reply: str
    hus_answer: HUSAnswer | None = None
    generation: HUSGeneration | None = Field(default=None, exclude_if=lambda value: value is None)


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
    if text in {"chao", "xin chao", "chao ban", "xin chao ban", "hi", "hello", "alo"}:
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
    if request.dataset == "auto" and dataset == "f1" and request.version in decision_versions:
        # The selector's decision version belongs to F2/F3, not F1 source editions.
        request = request.model_copy(update={"version": None})
    answer = answerer.answer(request)
    reply, generation = generate_reply(request, answer, answer.reply, rewriter=rewriter)
    return HUSChatReply(mode="hus_rag", reply=reply, hus_answer=answer, generation=generation)
