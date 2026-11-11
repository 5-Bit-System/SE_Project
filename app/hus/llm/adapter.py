"""Lazy L3 adapter: selected evidence -> provider -> checked L2 result."""

from dataclasses import dataclass

from .client import HUSLLMClient, HUSLLMError
from .config import HUSLLMSettings
from .contracts import HUSRewriteContext, HUSRewriteHandler
from .evidence import build_evidence
from .output import validate_output
from .prompts import build_prompt


@dataclass(frozen=True)
class HUSGroundedAdapter:
    client: HUSLLMClient

    def __call__(self, context: HUSRewriteContext):
        settings = self.client.settings
        if not settings.enabled:
            raise HUSLLMError('disabled')
        if context.requested_model != settings.model:
            raise HUSLLMError('configuration')
        evidence = build_evidence(context)
        prompt = build_prompt(evidence)
        if settings.api_key in prompt.system or settings.api_key in prompt.user:
            raise HUSLLMError('unsafe_prompt')
        response = self.client.complete_result(prompt.messages)
        if settings.api_key in response.content or settings.api_key in response.model:
            raise HUSLLMError('invalid_output')
        return validate_output(response.content, evidence, model=response.model,
                               prompt_sha256=prompt.sha256, usage=response.usage)


def get_default_rewriter(settings: HUSLLMSettings) -> HUSRewriteHandler | None:
    """Construction does no I/O; called only after the L2 consent/source gates."""
    return HUSGroundedAdapter(HUSLLMClient(settings))
