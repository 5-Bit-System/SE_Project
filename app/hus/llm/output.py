"""Strict structural, anchor, atom and source-unit retention; not entailment proof."""

import html
import json
import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .client import HUSLLMError
from .contracts import HUSF2Presentation, HUSTextRewrite
from .coverage import require_qualitative_coverage
from .diagnostics import HUSLLMDiagnostic
from .document import HUSRewriteDocument
from .evidence import HUSEvidenceBundle
from .usage import HUSUsage

MAX_OUTPUT_CHARS = 8192
_LINK_OR_HTML = re.compile(
    r'(?i)(?:<\s*/?\s*[a-z]|https?\s*:|www\.|/hus/sources/|'
    r'\b[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}(?:\b|/)|\[[0-9,\s]+\])')


class _Point(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    text: str = Field(min_length=1, max_length=3000)
    citation_id: str = Field(pattern=r'^[1-9][0-9]{0,2}$')
    anchor_quote: str = Field(min_length=1, max_length=6000)


class _TextOutput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: Literal['rewrite']
    points: list[_Point] = Field(min_length=1, max_length=20)


class _FactsOutput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: Literal['facts']
    style: Literal['direct', 'explain_source']
    fact_keys: list[str]
    citation_ids: list[str]


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate JSON key')
        value[key] = item
    return value


def _reject_constant(value):
    raise ValueError('Nonfinite JSON constant')


def _normal(text: str) -> str:
    text = unicodedata.normalize('NFKC', text)
    return ''.join('-' if unicodedata.category(c) == 'Pd' or c == '\u2212' else c for c in text)


def _atoms(text: str) -> tuple[set[str], set[str]]:
    text = _normal(text)
    numbers = {re.sub(r'\s+', '', value) for value in re.findall(
        r'(?<!\d)[+-]?\d+(?:[.,]\d+)*(?:\s*%)?(?!\d)', text)}
    codes = set(re.findall(r'(?<!\w)[^\W\d_]{2,8}\d{3,6}[A-Za-z]?(?!\w)', text))
    codes.update(re.findall(r'\b[A-Z]{2,6}\s+[0-9]{3,6}[A-Z]?\b', text))
    return numbers, {re.sub(r'\s+', '', code).upper() for code in codes}


def _bad(code='invalid_output'):
    raise HUSLLMError(code)


def _facts_bad(stage, issue, code='invalid_output'):
    raise HUSLLMError(code, diagnostic=HUSLLMDiagnostic(stage=stage, facts_issue=issue)) from None


def _validate_facts(raw, payload, sources, *, model, prompt_sha256, usage):
    """Same strict F2 decisions, with fixed internal labels and no rejected values."""
    try:
        parsed = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (ValueError, TypeError, KeyError, RecursionError):
        _facts_bad('output_json', 'json')
    try:
        result = _FactsOutput.model_validate(parsed)
    except ValidationError as error:
        locations = {e['loc'] for e in error.errors(include_input=False, include_url=False)}
        issue = 'kind' if ('kind',) in locations else 'style' if ('style',) in locations else 'schema'
        _facts_bad('output_schema', issue)
    checks = (
        (len(result.fact_keys) != len(set(result.fact_keys)), 'duplicate_fact_keys'),
        (len(result.citation_ids) != len(set(result.citation_ids)), 'duplicate_citation_ids'),
        (set(result.fact_keys) != set(payload['facts']), 'fact_keys'),
        (set(result.citation_ids) != set(sources), 'citation_ids'),
    )
    for failed, issue in checks:
        if failed:
            _facts_bad('output_coverage', issue, 'evidence_coverage')
    try:
        return HUSF2Presentation(style=result.style, model=model,
                                 prompt_sha256=prompt_sha256, usage=usage)
    except (ValueError, TypeError, KeyError, RecursionError):
        _facts_bad('output_schema', 'presentation')


def validate_output(raw: str, bundle: HUSEvidenceBundle | HUSRewriteDocument, *, model: str,
                    prompt_sha256: str, usage: HUSUsage | None = None):
    if isinstance(bundle, HUSRewriteDocument):
        from .output_v3 import validate_compact_output

        return validate_compact_output(raw, bundle, model=model, prompt_sha256=prompt_sha256, usage=usage)
    if len(raw) > MAX_OUTPUT_CHARS:
        if bundle.payload['scope']['dataset'] == 'f2':
            _facts_bad('output_budget', 'budget', 'output_budget')
        _bad('output_budget')
    payload = bundle.payload
    sources = {source['citation_id']: source for source in payload['sources']}
    if payload['scope']['dataset'] == 'f2':
        return _validate_facts(raw, payload, sources, model=model, prompt_sha256=prompt_sha256, usage=usage)
    try:
        parsed = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        result = _TextOutput.model_validate(parsed)
        coverage = {cid: (set(), set()) for cid in sources}
        rendered, seen = [], set()
        for point in result.points:
            source = sources.get(point.citation_id)
            if source is None or not point.text.strip():
                _bad()
            anchor = point.anchor_quote
            if (anchor not in source['quote']
                    or len(anchor.strip()) < min(20, len(source['quote'].strip()))):
                _bad()
            content = _normal(html.unescape(html.unescape(point.text)))
            if _LINK_OR_HTML.search(content):
                _bad()
            scope_text = ' '.join(v for v in source['scope'].values() if isinstance(v, str))
            allowed = _atoms(anchor + ' ' + scope_text)
            atoms = _atoms(point.text)
            if any(not actual.issubset(valid) for actual, valid in zip(atoms, allowed, strict=True)):
                _bad()
            identity = (point.citation_id, point.text, anchor)
            if identity in seen:
                _bad()
            seen.add(identity)
            for collected, actual in zip(coverage[point.citation_id], atoms, strict=True):
                collected.update(actual)
            rendered.append(point.text.strip() + ' [' + point.citation_id + ']')
        if {point.citation_id for point in result.points} != set(sources):
            _bad('evidence_coverage')
        for cid, source in sources.items():
            if any(not required.issubset(actual) for required, actual in
                   zip(_atoms(source['quote']), coverage[cid], strict=True)):
                _bad('evidence_coverage')
        require_qualitative_coverage(sources,
            [(point.citation_id, point.text, point.anchor_quote) for point in result.points])
        return HUSTextRewrite(reply='\n\n'.join(rendered), model=model,
                              prompt_sha256=prompt_sha256, usage=usage)
    except HUSLLMError:
        raise
    except (ValueError, TypeError, KeyError, RecursionError, ValidationError):
        raise HUSLLMError('invalid_output') from None
