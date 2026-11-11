"""Immutable source leaves; provider selects words, backend owns spans and layout."""
import json
import re
from dataclasses import dataclass
from hashlib import sha256

from .client import HUSLLMError
from .coverage import EvidenceUnit, source_units
from .diagnostics import HUSLLMDiagnostic
from .evidence import MAX_PROMPT_CHARS, HUSEvidenceBundle

MAX_LEAVES = 64
MAX_UNITS = 128
MAX_LEAF_CHARS = 3000
SCHEMA = 'hus-llm-document-v3'
_PREFIX = re.compile(r'^[ \t]*(?:(?:[-*•]|\d+[.)]|#{1,6})[ \t]+)?')
_LIST = re.compile(r'^[ \t]*(?:[-*•]|\d+[.)])[ \t]+')


@dataclass(frozen=True)
class HUSSourceLeaf:
    id: str
    citation_id: str
    start: int
    end: int
    prefix: str
    text: str
    layout: str
    units: tuple[EvidenceUnit, ...]


@dataclass(frozen=True)
class HUSRewriteDocument:
    bundle: HUSEvidenceBundle
    json_text: str
    leaves: tuple[HUSSourceLeaf, ...]

    @property
    def payload(self) -> dict:
        return json.loads(self.json_text)

    @property
    def sha256(self) -> str:
        return sha256(self.json_text.encode('utf-8')).hexdigest()


def build_document(bundle: HUSEvidenceBundle) -> HUSRewriteDocument:
    payload = bundle.payload
    if payload['scope']['dataset'] not in {'f1', 'f3'}:
        raise ValueError('Compact document accepts F1/F3 only')
    leaves = []
    unit_count = 0
    for source in payload['sources']:
        quote = source['quote']
        units = source_units(quote)
        unit_count += len(units)
        selected = []
        start = 0
        for boundary in re.finditer(r'\r?\n|$', quote):
            end = boundary.start()
            while end > start and quote[end - 1].isspace():
                end -= 1
            line = quote[start:end]
            if line.strip():
                prefix = _PREFIX.match(line).group()
                covered = tuple(unit for unit in units if start <= unit.start and unit.end <= end)
                leaf = HUSSourceLeaf(f'b{len(leaves)+1:03}', source['citation_id'], start, end,
                                     prefix, line[len(prefix):],
                                     'list_item' if _LIST.match(prefix) else 'paragraph', covered)
                if len(line) > MAX_LEAF_CHARS:
                    raise HUSLLMError('prompt_budget', diagnostic=HUSLLMDiagnostic(stage='document_budget'))
                selected.append(leaf)
                leaves.append(leaf)
            start = boundary.end()
        if (any(sum(leaf.start <= unit.start and unit.end <= leaf.end for leaf in selected) != 1 for unit in units)
                or ''.join(c for leaf in selected for c in leaf.prefix + leaf.text if not c.isspace())
                != ''.join(c for c in quote if not c.isspace())):
            raise HUSLLMError('prompt_budget', diagnostic=HUSLLMDiagnostic(stage='document_budget'))
        source.pop('quote')
        source['segments'] = [{'id': leaf.id, 'text': leaf.text, 'layout': leaf.layout, 'prefix': leaf.prefix}
                              for leaf in selected]
    if not leaves or len(leaves) > MAX_LEAVES or unit_count > MAX_UNITS:
        raise HUSLLMError('prompt_budget', diagnostic=HUSLLMDiagnostic(stage='document_budget'))
    payload['schema_version'] = SCHEMA
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    if len(encoded) > MAX_PROMPT_CHARS:
        raise HUSLLMError('prompt_budget', diagnostic=HUSLLMDiagnostic(stage='document_budget'))
    return HUSRewriteDocument(bundle, encoded, tuple(leaves))
