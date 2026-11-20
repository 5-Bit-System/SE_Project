"""L2 server-side rewrite boundary; not a raw provider-output schema."""

from collections.abc import Callable
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.schemas.hus import HUSAnswer, HUSQuestion

from .usage import HUSUsage

ModelID = str
FallbackReason = Literal[
    'basic_chat', 'not_answered', 'no_sources', 'f3_opt_out', 'ineligible_dataset',
    'configuration', 'pipeline_unavailable', 'invalid_result', 'adapter_error',
    'provider_error', 'disabled', 'http_error', 'timeout', 'transport_error', 'invalid_response',
    'prompt_budget', 'output_budget', 'invalid_output', 'evidence_coverage', 'unsafe_prompt', 'busy',
]


class HUSGeneration(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, strict=True)
    used: bool
    requested_model: ModelID | None = None
    model: ModelID | None = None
    fallback_reason: FallbackReason | None = None
    prompt_sha256: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$',
                                     exclude_if=lambda value: value is None)
    usage: HUSUsage | None = Field(default=None, exclude_if=lambda value: value is None)
    http_status: int | None = Field(default=None, ge=100, le=599,
                                    exclude_if=lambda value: value is None)

    @model_validator(mode='after')
    def consistent_outcome(self):
        if self.used:
            if not self.model or self.fallback_reason is not None or self.http_status is not None:
                raise ValueError('Used generation requires a returned model and no fallback')
        elif self.model is not None or self.fallback_reason is None:
            raise ValueError('Unused generation requires a fallback and no returned model')
        return self


class HUSRewriteContext(BaseModel):
    """Defensive copies of the effective request and canonical answer; no key/history."""

    model_config = ConfigDict(extra='forbid', frozen=True)
    question: HUSQuestion
    answer: HUSAnswer
    requested_model: ModelID


class HUSTextRewrite(BaseModel):
    """Trusted adapter's validated F1/F3 result; never accept raw model JSON here."""

    model_config = ConfigDict(extra='forbid', frozen=True, strict=True, str_strip_whitespace=True)
    kind: Literal['text'] = 'text'
    reply: Annotated[str, StringConstraints(strip_whitespace=False)] = Field(min_length=1)
    model: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9._:/-]+$')
    prompt_sha256: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')
    usage: HUSUsage | None = None

    @field_validator('reply')
    @classmethod
    def nonblank_reply(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Rewrite reply must contain text')
        return value


class HUSF2Presentation(BaseModel):
    """F2 can select presentation only. Values and source interpretation remain canonical."""

    model_config = ConfigDict(extra='forbid', frozen=True, strict=True)
    kind: Literal['facts'] = 'facts'
    style: Literal['direct', 'explain_source']
    model: str = Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9._:/-]+$')
    prompt_sha256: str | None = Field(default=None, pattern=r'^[0-9a-f]{64}$')
    usage: HUSUsage | None = None


HUSRewriteHandler = Callable[[HUSRewriteContext], HUSTextRewrite | HUSF2Presentation]
