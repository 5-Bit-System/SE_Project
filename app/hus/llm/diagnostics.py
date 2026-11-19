"""Allowlisted failure metadata; never retain provider text, headers or unknown IDs."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Stage = Literal['provider_http', 'provider_envelope', 'provider_budget', 'document_budget',
                'output_json', 'output_schema', 'output_ids', 'output_text',
                'output_atoms', 'output_symbols', 'output_coverage', 'output_budget']
Finish = Literal['stop', 'length', 'content_filter', 'tool_calls', 'function_call', 'missing', 'other']
ProviderStatus = Literal['PERMISSION_DENIED', 'UNAUTHENTICATED', 'INVALID_ARGUMENT',
                         'FAILED_PRECONDITION', 'RESOURCE_EXHAUSTED', 'NOT_FOUND',
                         'UNAVAILABLE', 'INTERNAL', 'UNKNOWN', 'other']
AccessIssue = Literal['key_reported_leaked', 'verification_required', 'project_access_denied', 'unspecified']
TextIssue = Literal['blank', 'raw_line_break', 'decoded_line_break', 'structure', 'link_or_html', 'restored_length']
FactsIssue = Literal['budget', 'json', 'kind', 'style', 'schema', 'duplicate_fact_keys',
                     'duplicate_citation_ids', 'fact_keys', 'citation_ids', 'presentation', 'credential_echo']


class HUSLLMDiagnostic(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, strict=True)
    stage: Stage
    finish_reason: Finish | None = None
    content_kind: Literal['text', 'null', 'missing', 'other'] | None = None
    content_chars: int | None = Field(default=None, ge=0)
    has_tool_call: bool | None = None
    leaf_id: str | None = Field(default=None, pattern=r'^b(?:00[1-9]|0[1-5][0-9]|06[0-4])$')
    provider_status: ProviderStatus | None = None
    access_issue: AccessIssue | None = None
    text_issue: TextIssue | None = None
    facts_issue: FactsIssue | None = None

    @model_validator(mode='after')
    def text_issue_stage(self):
        if self.text_issue is not None and self.stage != 'output_text':
            raise ValueError('Text issue requires output_text stage')
        if self.facts_issue is not None:
            expected = ('output_budget' if self.facts_issue == 'budget' else
                        'output_json' if self.facts_issue == 'json' else
                        'output_coverage' if self.facts_issue in {
                            'duplicate_fact_keys', 'duplicate_citation_ids', 'fact_keys', 'citation_ids'}
                        else 'output_schema')
            if self.stage != expected:
                raise ValueError('Facts issue requires its matching output stage')
        return self


def http_error_diagnostic(value, status_code: int) -> HUSLLMDiagnostic:
    """Classify provider-reported errors into fixed labels; discard all free text.

    A generic 403 does not identify a bad key, billing issue or project restriction.
    These labels describe the response, never verify an account's actual state.
    """
    # Google can wrap one error object in a top-level array. Ambiguous or
    # nested arrays stay unspecified; never search arbitrary provider content.
    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], dict):
        value = value[0]
    body = value if isinstance(value, dict) else {}
    error = body.get('error')
    error = error if isinstance(error, dict) else {}
    status = error.get('status', error.get('code'))
    statuses = {'PERMISSION_DENIED', 'UNAUTHENTICATED', 'INVALID_ARGUMENT',
                'FAILED_PRECONDITION', 'RESOURCE_EXHAUSTED', 'NOT_FOUND',
                'UNAVAILABLE', 'INTERNAL', 'UNKNOWN'}
    status = status.upper() if isinstance(status, str) and len(status) <= 32 else 'other'
    status = status if status in statuses else 'other'
    issue = 'unspecified'
    message = error.get('message')
    message = message.casefold() if isinstance(message, str) and len(message) <= 8192 else ''
    details = error.get('details')
    details = details[:16] if isinstance(details, list) else []
    verification = any(isinstance(detail, dict)
                       and detail.get('reason') == 'FREE_TIER_VERIFICATION_REQUIRED' for detail in details)
    if status_code == 403:
        if 'your api key was reported as leaked' in message:
            issue = 'key_reported_leaked'
        elif verification or 'free_tier_verification_required' in message:
            issue = 'verification_required'
        elif 'your project has been denied access' in message:
            issue = 'project_access_denied'
    return HUSLLMDiagnostic(stage='provider_http', provider_status=status, access_issue=issue)


def envelope_diagnostic(value) -> HUSLLMDiagnostic:
    body = value if isinstance(value, dict) else {}
    choices = body.get('choices')
    choice = choices[0] if isinstance(choices, list) and choices and isinstance(choices[0], dict) else {}
    message = choice.get('message')
    message = message if isinstance(message, dict) else {}
    finish = choice.get('finish_reason')
    finish = finish if isinstance(finish, str) and finish in {
        'stop', 'length', 'content_filter', 'tool_calls', 'function_call'} else 'missing' if 'finish_reason' not in choice else 'other'
    content = message.get('content')
    kind = ('missing' if 'content' not in message else 'text' if isinstance(content, str)
            else 'null' if content is None else 'other')
    return HUSLLMDiagnostic(stage='provider_envelope', finish_reason=finish,
        content_kind=kind, content_chars=len(content) if isinstance(content, str) else None,
        has_tool_call=bool(message.get('tool_calls') or message.get('function_call')))
