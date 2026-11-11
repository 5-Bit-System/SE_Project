"""Allowlisted failure metadata; never retain provider text, headers or unknown IDs."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Stage = Literal['provider_envelope', 'provider_budget', 'document_budget',
                'output_json', 'output_schema', 'output_ids', 'output_text',
                'output_atoms', 'output_symbols', 'output_coverage', 'output_budget']
Finish = Literal['stop', 'length', 'content_filter', 'tool_calls', 'function_call', 'missing', 'other']


class HUSLLMDiagnostic(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, strict=True)
    stage: Stage
    finish_reason: Finish | None = None
    content_kind: Literal['text', 'null', 'missing', 'other'] | None = None
    content_chars: int | None = Field(default=None, ge=0)
    has_tool_call: bool | None = None
    leaf_id: str | None = Field(default=None, pattern=r'^b(?:00[1-9]|0[1-5][0-9]|06[0-4])$')


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
