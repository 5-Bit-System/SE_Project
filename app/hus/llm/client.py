"""Text-only Chat Completions transport, preserving the raw completion envelope."""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import httpx

from .config import HUSLLMSettings
from .diagnostics import HUSLLMDiagnostic, envelope_diagnostic
from .usage import HUSUsage


@dataclass(frozen=True)
class HUSCompletion:
    """Raw content for L3 budgets; model/usage come from the provider envelope."""
    content: str
    model: str
    usage: HUSUsage | None = None
    diagnostic: HUSLLMDiagnostic | None = None


class HUSLLMError(RuntimeError):
    """Safe failure reason for callers; never includes request/provider content."""

    def __init__(self, code: str, *, status_code: int | None = None,
                 diagnostic: HUSLLMDiagnostic | None = None) -> None:
        self.code = code
        self.status_code = status_code
        self.diagnostic = diagnostic
        super().__init__(f'HUS LLM request failed: {code}')


class HUSLLMClient:
    """Construct without network access; create/close HTTP resources per explicit call.

    The optional transport permits offline tests. Production uses HTTPX's default
    transport, without retries, redirects or environment proxy/netrc credentials.
    This adapter returns untrusted text; evidence validation belongs to L3.
    """

    def __init__(self, settings: HUSLLMSettings, *,
                 transport: httpx.BaseTransport | None = None) -> None:
        self.settings = settings
        self._transport = transport

    def complete(self, messages: Sequence[Mapping[str, str]]) -> str:
        return self.complete_result(messages).content.strip()

    def complete_result(self, messages: Sequence[Mapping[str, str]]) -> HUSCompletion:
        """Keep raw whitespace; only the backwards-compatible text API trims it."""
        if not self.settings.enabled:
            raise HUSLLMError('disabled')
        if (not isinstance(messages, Sequence) or isinstance(messages, (str, bytes))
                or not messages):
            raise ValueError('messages must be a nonempty sequence of text messages')
        payload = []
        for message in messages:
            if (not isinstance(message, Mapping) or set(message) != {'role', 'content'}
                    or message['role'] not in ('system', 'user', 'assistant')
                    or not isinstance(message['content'], str) or not message['content'].strip()):
                raise ValueError('messages must contain role and nonempty text content')
            payload.append(dict(message))
        try:
            with httpx.Client(transport=self._transport, timeout=20.0,
                              follow_redirects=False, trust_env=False) as client:
                response = client.post(
                    self.settings.base_url.rstrip('/') + '/chat/completions',
                    headers={'Authorization': f'Bearer {self.settings.api_key}'},
                    json={'model': self.settings.model, 'messages': payload,
                          'stream': False, 'max_tokens': 1024},
                )
        except httpx.TimeoutException:
            raise HUSLLMError('timeout') from None
        except httpx.RequestError:
            raise HUSLLMError('transport_error') from None
        if not 200 <= response.status_code < 300:
            raise HUSLLMError('http_error', status_code=response.status_code) from None
        diagnostic = HUSLLMDiagnostic(stage='provider_envelope')
        try:
            data = response.json()
            diagnostic = envelope_diagnostic(data)
            choice = data['choices'][0]
            message = choice['message']
            content = message['content']
            model = data['model']
            if (choice.get('finish_reason') != 'stop'
                    or not isinstance(content, str) or not content.strip()
                    or message.get('tool_calls') or message.get('function_call')
                    or not isinstance(model, str)
                    or re.fullmatch(r'[A-Za-z0-9._:/-]{1,100}', model) is None
                    or self.settings.api_key in model):
                raise ValueError('Invalid text completion')
            raw_usage = data.get('usage')
            if raw_usage is not None and not isinstance(raw_usage, dict):
                raise ValueError('Invalid token usage')
            counters = {k: v for k, v in (raw_usage or {}).items()
                        if k in HUSUsage.model_fields}
            usage = HUSUsage.model_validate(counters) if counters else None
        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            raise HUSLLMError('invalid_response', diagnostic=diagnostic) from None
        if usage and usage.completion_tokens is not None and usage.completion_tokens > 1024:
            raise HUSLLMError('output_budget', diagnostic=diagnostic.model_copy(update={'stage': 'provider_budget'})) from None
        return HUSCompletion(content, model, usage, diagnostic)
