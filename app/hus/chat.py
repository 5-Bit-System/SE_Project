"""F1/F2/F3 and basic conversation, with no course recommendation dependencies."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.hus.answering import HUSAnswerer, question_intent
from app.hus.retrieval import _tokens
from app.schemas.hus import HUSAnswer, HUSQuestion


class HUSChatReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["basic_chat", "hus_rag"]
    reply: str
    hus_answer: HUSAnswer | None = None


def basic_reply(question: str) -> str | None:
    text = " ".join(_tokens(question))
    if text in {"chao", "xin chao", "chao ban", "xin chao ban", "hi", "hello", "alo"}:
        return "Chào bạn! Bạn muốn tìm hiểu về ngành học, chương trình đào tạo hay một học phần?"
    if text in {"cam on", "cam on ban", "thanks", "thank you", "ok cam on"}:
        return "Rất vui được giúp bạn. Bạn có thể hỏi tiếp về ngành học hoặc học phần."
    if text in {"tam biet", "bye", "hen gap lai", "goodbye"}:
        return "Hẹn gặp lại bạn!"
    if text in {"ban la ai", "ban co the lam gi", "ban giup duoc gi", "toi co the hoi gi", "huong dan su dung"}:
        return ("Tôi hỗ trợ thông tin ngành học, dữ kiện chương trình và nội dung học phần. "
                "Bạn có thể hỏi giới thiệu ngành, tín chỉ hoặc tiên quyết theo mã môn. "
                "Nội dung học phần AI cần bật cho phép kiến thức AI tham khảo.")
    return None


def chat(request: HUSQuestion, answerer: HUSAnswerer) -> HUSChatReply:
    if request.dataset == "auto" and request.course_code is None and request.field is None:
        reply = basic_reply(request.question)
        if reply is not None:
            return HUSChatReply(mode="basic_chat", reply=reply)
    dataset, _ = question_intent(request.question)
    decision_versions = {version for major, version in answerer.programs.values() if major == request.major}
    if request.dataset == "auto" and dataset == "f1" and request.version in decision_versions:
        # The selector's decision version belongs to F2/F3, not F1 source editions.
        request = request.model_copy(update={"version": None})
    answer = answerer.answer(request)
    return HUSChatReply(mode="hus_rag", reply=answer.reply, hus_answer=answer)
