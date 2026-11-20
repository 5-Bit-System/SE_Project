"""L2 permission gates and immutable canonical response; lazy default L3 adapter."""

from pydantic import ValidationError

from app.hus.rag_loader import RAGDataError
from app.schemas.hus import HUSAnswer, HUSQuestion

from .capacity import llm_call_slot
from .client import HUSLLMError
from .config import HUSLLMSettings
from .contracts import (
    FallbackReason,
    HUSF2Presentation,
    HUSGeneration,
    HUSRewriteContext,
    HUSRewriteHandler,
    HUSTextRewrite,
)

_PROVIDER_REASONS = {'disabled', 'http_error', 'timeout', 'transport_error', 'invalid_response',
                     'configuration', 'prompt_budget', 'output_budget', 'invalid_output',
                     'evidence_coverage', 'unsafe_prompt', 'busy'}
_F2_LEADS = {
    'direct': 'Thông tin theo nguồn đã chọn:',
    'explain_source': 'Dưới đây là dữ kiện và trạng thái được ghi nhận trong nguồn đã chọn:',
}


def generate_reply(
    request: HUSQuestion,
    answer: HUSAnswer | None,
    reply: str,
    *,
    rewriter: HUSRewriteHandler | None = None,
) -> tuple[str, HUSGeneration | None]:
    """Check both flags before delegating provider work to a validated adapter.

    Either flag off preserves the exact legacy response shape. When enabled,
    failures report a safe reason and retain the original reply. The injected
    adapter must validate provider output in L3 before returning a typed result.
    The default L3 factory is resolved only after the permission/source gates.
    """
    if not request.allow_llm_rewrite:
        return reply, None

    def fallback(reason: FallbackReason, model: str | None = None, http_status: int | None = None):
        return reply, HUSGeneration(used=False, requested_model=model, fallback_reason=reason,
                                    http_status=http_status)

    try:
        if not HUSLLMSettings.read_enabled():
            return reply, None
    except ValueError:
        return fallback('configuration')

    if answer is None:
        return fallback('basic_chat')
    if answer.status != 'answered':
        return fallback('not_answered')
    if answer.dataset not in {'f1', 'f2', 'f3'}:
        return fallback('ineligible_dataset')
    if answer.dataset == 'f3' and not request.allow_generated_reference:
        return fallback('f3_opt_out')
    if not answer.citations:
        return fallback('no_sources')

    try:
        settings = HUSLLMSettings.from_env()
    except ValueError:
        return fallback('configuration')
    if settings.api_key in settings.model:
        return fallback('configuration')
    context = HUSRewriteContext(question=request.model_copy(deep=True),
                                answer=answer.model_copy(deep=True),
                                requested_model=settings.model)
    try:
        with llm_call_slot():
            if rewriter is None:
                from .adapter import get_default_rewriter

                rewriter = get_default_rewriter(settings)
            if rewriter is None:
                return fallback('pipeline_unavailable', settings.model)
            result = rewriter(context)
            if answer.dataset == 'f2':
                if type(result) is not HUSF2Presentation:
                    return fallback('invalid_result', settings.model)
                result = HUSF2Presentation.model_validate(result.model_dump(warnings=False))
                rendered = _F2_LEADS[result.style] + '\n\n' + reply
            else:
                if type(result) is not HUSTextRewrite:
                    return fallback('invalid_result', settings.model)
                result = HUSTextRewrite.model_validate(result.model_dump(warnings=False))
                rendered = '\n\n'.join([*answer.warnings, result.reply])
            # Reject accidental credential echoes even from an incorrectly wired adapter.
            if settings.api_key in rendered or settings.api_key in result.model:
                return fallback('invalid_result', settings.model)
            generation = HUSGeneration(used=True, requested_model=settings.model, model=result.model,
                                       prompt_sha256=result.prompt_sha256, usage=result.usage)
    except RAGDataError:
        raise  # Canonical faults must not be disguised as an LLM fallback.
    except HUSLLMError as error:
        reason = error.code if error.code in _PROVIDER_REASONS else 'provider_error'
        status = error.status_code
        if reason != 'http_error' or type(status) is not int or not 100 <= status <= 599:
            status = None
        return fallback(reason, settings.model, status)
    except (ValidationError, ValueError, TypeError, KeyError):
        return fallback('invalid_result', settings.model)
    except Exception:
        return fallback('adapter_error', settings.model)
    return rendered, generation
