"""Local automatic Gemini policy: offline only after an observed HTTP 429."""

import os
from threading import Event

from app.hus.chat import HUSChatReply, basic_reply, chat
from app.hus.diagnostics import generation_diagnostic
from app.hus.llm.capacity import llm_call_slot
from app.hus.llm.client import HUSLLMError
from app.hus.llm.config import HUSLLMSettings
from app.hus.llm.contracts import HUSGeneration
from app.hus.question_routing import question_intent
from app.schemas.hus import HUSDiagnostic


def auto_enabled() -> bool:
    try:
        return os.environ.get('HUS_LLM_AUTO', '').lower() == 'true' and HUSLLMSettings.read_enabled()
    except ValueError:
        return False


class AutoLLMUnavailable(Exception):
    """No offline substitution is permitted for a non-quota model error."""

    def __init__(self, generation=None):
        super().__init__('Automatic LLM unavailable')
        self.diagnostic = generation_diagnostic(generation) or HUSDiagnostic(code='provider_error')


class AutoLLMPolicy:
    def __init__(self):
        self._quota = Event()

    @property
    def quota_exhausted(self) -> bool:
        return self._quota.is_set()

    def _interpret(self, request, answerer, interpreter):
        if (os.environ.get('HUS_LLM_INTENT_ENABLED', '').lower() != 'true'
                or self.quota_exhausted or request.dataset != 'auto'
                or request.field is not None or basic_reply(request.question) is not None
                or question_intent(request.question)[0] is not None):
            return request, None, None
        # Rules/scope/action/source checks precede provider I/O. Do not reinterpret
        # evidence rejection or permission failures as permission to answer.
        baseline = answerer.answer(request)
        if not baseline.diagnostic or baseline.diagnostic.code != 'routing_unknown':
            return request, None, None
        try:
            with llm_call_slot():
                if self.quota_exhausted:
                    raise HUSLLMError('http_error', status_code=429)
                try:
                    if interpreter is None:
                        from .client import HUSLLMClient
                        from .intent import HUSIntentInterpreter

                        interpreter = HUSIntentInterpreter(HUSLLMClient(HUSLLMSettings.from_env()))
                    result = interpreter(request.model_copy(deep=True), answerer)
                except HUSLLMError as error:
                    if error.code == 'http_error' and error.status_code == 429:
                        self._quota.set()
                    raise
        except HUSLLMError as error:
            generation = HUSGeneration(used=False, fallback_reason=error.code,
                                       http_status=error.status_code)
            if error.code == 'http_error' and error.status_code == 429:
                return request, generation, None
            raise AutoLLMUnavailable(generation) from None
        except (ValueError, TypeError):
            raise AutoLLMUnavailable(HUSGeneration(used=False, fallback_reason='configuration')) from None
        if result.request is None:
            from app.hus.diagnostics import MAJOR_LABELS

            reason = ('Câu hỏi cần ngành ' + MAJOR_LABELS[result.suggested_major] +
                      '. Hãy chọn lại ngành rồi hỏi lại.' if result.suggested_major else
                      'Bạn muốn hỏi thông tin ngành, dữ kiện chương trình hay nội dung của môn nào? '
                      'Hãy nêu một ý và mã/tên đầy đủ của môn nếu có.')
            answer = answerer._missing(request, None, reason, clarify=True,
                diagnostic_code='scope_conflict' if result.suggested_major else 'clarification_required',
                suggested_major=result.suggested_major)
            return request, result.metadata, HUSChatReply(mode='hus_rag', reply=answer.reply,
                hus_answer=answer, interpretation=result.metadata)
        return result.request, result.metadata, None

    def reply(self, request, answerer, *, rewriter=None, interpreter=None):
        request, interpretation, clarification = self._interpret(request, answerer, interpreter)
        if clarification is not None:
            return clarification
        exhausted = self.quota_exhausted

        def guarded_rewriter(context):
            # generate_reply holds llm_call_slot here. Recheck after evidence
            # preparation and latch a 429 before releasing that provider slot.
            if self.quota_exhausted:
                raise HUSLLMError('http_error', status_code=429)
            try:
                handler = rewriter
                if handler is None:
                    from app.hus.llm.adapter import get_default_rewriter

                    handler = get_default_rewriter(HUSLLMSettings.from_env())
                if handler is None:
                    raise HUSLLMError('pipeline_unavailable')
                return handler(context)
            except HUSLLMError as error:
                if error.code == 'http_error' and error.status_code == 429:
                    self._quota.set()
                raise

        result = chat(request.model_copy(update={'allow_llm_rewrite': not exhausted}),
                      answerer, rewriter=guarded_rewriter)
        if interpretation is not None:
            result = result.model_copy(update={'interpretation': interpretation})
        answer = result.hus_answer
        # Clarifications, missing evidence and basic conversation are not model
        # failures and must not cause a provider call or invented factual answer.
        if answer is None or answer.status != 'answered':
            return result
        if exhausted:
            return result.model_copy(update={'generation': HUSGeneration(
                used=False, fallback_reason='http_error', http_status=429)})
        generation = result.generation
        if generation and generation.used:
            return result
        if generation and generation.fallback_reason == 'http_error' and generation.http_status == 429:
            self._quota.set()
            return result
        raise AutoLLMUnavailable(generation)
