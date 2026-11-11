"""Validate every compact leaf before restoring the original source skeleton."""
import html
import json
import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .client import HUSLLMError
from .contracts import HUSTextRewrite
from .coverage import _retained, require_qualitative_coverage
from .diagnostics import HUSLLMDiagnostic
from .document import MAX_LEAF_CHARS, MAX_LEAVES, HUSRewriteDocument
from .output import (
    _LINK_OR_HTML,
    MAX_OUTPUT_CHARS,
    _atoms,
    _normal,
    _reject_constant,
    _unique_object,
)
from .usage import HUSUsage

_BREAK = re.compile(r'[\r\n\v\f\x85\u2028\u2029]')
_STRUCTURE = re.compile(r'^\s*(?:[-*•]|\d+[.)]|#{1,6})[ \t]+')
_MATH_PUNCTUATION = frozenset('+-*/%=<>|~^\\@&!:()[]{}\'"′″‴')


def _operator(token):
    return len(token) == 1 and (unicodedata.category(token).startswith('S') or token in _MATH_PUNCTUATION)


def _math_tokens(text):
    return tuple(token for token in re.findall(r'\w+|[^\w\s]', _normal(text).casefold())
                 if re.match(r'\w', token) or _operator(token))


def _symbols_retained(original, text):
    required, actual = _math_tokens(original), _math_tokens(text)
    symbols = tuple(token for token in required if _operator(token))
    if symbols != tuple(token for token in actual if _operator(token)):
        return False
    # Retain operator positions relative to source words, not only their counts.
    return not symbols or _retained(required, actual)


class _Item(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    id: str = Field(pattern=r'^b[0-9]{3}$')
    text: str = Field(min_length=1, max_length=MAX_LEAF_CHARS)


class _Output(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: Literal['rewrite_v3']
    items: list[_Item] = Field(min_length=1, max_length=MAX_LEAVES)


def _fail(code, stage, leaf=None):
    raise HUSLLMError(code, diagnostic=HUSLLMDiagnostic(stage=stage, leaf_id=leaf.id if leaf else None)) from None


def validate_compact_output(raw: str, document: HUSRewriteDocument, *, model: str,
                            prompt_sha256: str, usage: HUSUsage | None = None):
    if len(raw) > MAX_OUTPUT_CHARS:
        _fail('output_budget', 'output_budget')
    try:
        parsed = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (ValueError, TypeError, KeyError, RecursionError):
        _fail('invalid_output', 'output_json')
    try:
        output = _Output.model_validate(parsed)
    except ValidationError:
        _fail('invalid_output', 'output_schema')
    expected = {leaf.id for leaf in document.leaves}
    returned = [item.id for item in output.items]
    if len(returned) != len(set(returned)) or set(returned) - expected:
        _fail('invalid_output', 'output_ids')
    if set(returned) != expected:
        _fail('evidence_coverage', 'output_ids')
    by_id = {item.id: item.text for item in output.items}
    sources = {s['citation_id']: s for s in document.bundle.payload['sources']}
    checked = {}
    for leaf in document.leaves:
        source = sources[leaf.citation_id]
        text = by_id[leaf.id].strip()
        content = _normal(html.unescape(html.unescape(text)))
        if (not text or _BREAK.search(text) or _BREAK.search(content)
                or _STRUCTURE.search(content) or _LINK_OR_HTML.search(content)):
            _fail('invalid_output', 'output_text', leaf)
        restored = leaf.prefix + text
        if len(restored) > MAX_LEAF_CHARS:
            _fail('invalid_output', 'output_text', leaf)
        original = source['quote'][leaf.start:leaf.end]
        scope = ' '.join(v for v in source['scope'].values() if isinstance(v, str))
        allowed, actual = _atoms(original + ' ' + scope), _atoms(restored)
        if any(not value.issubset(authority) for value, authority in zip(actual, allowed, strict=True)):
            _fail('invalid_output', 'output_atoms', leaf)
        # A short anchor may extend across source text for binding, not authority.
        anchor = original if len(original.strip()) >= min(20, len(source['quote'].strip())) else source['quote']
        try:
            require_qualitative_coverage({leaf.citation_id: {**source, 'quote': original}},
                                          [(leaf.citation_id, restored, anchor)])
        except HUSLLMError:
            _fail('evidence_coverage', 'output_coverage', leaf)
        if not _symbols_retained(original, restored):
            _fail('invalid_output', 'output_symbols', leaf)
        checked[leaf.id] = restored + ' [' + leaf.citation_id + ']'
    rendered = []
    for cid, source in sources.items():
        cursor, parts = 0, []
        for leaf in document.leaves:
            if leaf.citation_id != cid:
                continue
            parts.extend([source['quote'][cursor:leaf.start], checked[leaf.id]])
            cursor = leaf.end
        parts.append(source['quote'][cursor:])
        rendered.append(''.join(parts))
    return HUSTextRewrite(reply='\n\n'.join(rendered), model=model,
                          prompt_sha256=prompt_sha256, usage=usage)
