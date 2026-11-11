"""Immutable, allowlisted evidence from one canonical RAG answer."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import TYPE_CHECKING

from app.hus.rag_loader import RAGDataError

from .client import HUSLLMError
from .contracts import HUSRewriteContext

if TYPE_CHECKING:
    from .document import HUSRewriteDocument

MAX_PROMPT_CHARS = 12000
_FACT_KEYS = {'course_code', 'course_name', 'field', 'value', 'review_status',
              'prerequisite_status', 'has_prerequisite_conflict', 'unresolved_prerequisites',
              'program_id'}
_GROUP_KEYS = {'group_key', 'group_title', 'source_heading', 'group_note',
               'min_credits_if_selected', 'offered_credits'}


def _invalid() -> None:
    raise RAGDataError('Invalid canonical LLM evidence identity or scope')


def _mapping(parent: dict, key: str) -> dict:
    value = parent.get(key, {})
    if not isinstance(value, dict):
        _invalid()
    return value


def _facts(source: dict) -> dict:
    facts = {key: value for key, value in source.items() if key in _FACT_KEYS}
    field, value = facts.get('field'), facts.get('value')
    dict_keys = {'hours': {'lecture', 'practice', 'self_study', 'total'},
                 'course_info': {'course_name', 'credits'},
                 'program_credits': {'credits_required'}, 'group_rules': _GROUP_KEYS}
    if field in dict_keys:
        if not isinstance(value, dict) or set(value) - dict_keys[field]:
            _invalid()
        if any(type(v) not in {str, int, float, type(None)} for v in value.values()):
            _invalid()
    elif field == 'program_groups':
        if not isinstance(value, list):
            _invalid()
        for group in value:
            if (not isinstance(group, dict) or set(group) - _GROUP_KEYS
                    or any(type(v) not in {str, int, float, type(None)} for v in group.values())):
                _invalid()
    elif field == 'prerequisites':
        if not isinstance(value, list) or any(v is not None and type(v) is not str for v in value):
            _invalid()
    elif field == 'credits':
        if type(value) not in {int, float}:
            _invalid()
    elif field == 'name':
        if type(value) is not str:
            _invalid()
    else:
        _invalid()
    for key in set(facts) - {'value', 'has_prerequisite_conflict', 'unresolved_prerequisites'}:
        if type(facts[key]) is not str:
            _invalid()
    if ('has_prerequisite_conflict' in facts and type(facts['has_prerequisite_conflict']) is not bool):
        _invalid()
    unresolved = facts.get('unresolved_prerequisites', [])
    if not isinstance(unresolved, list) or any(type(code) is not str for code in unresolved):
        _invalid()
    return facts


@dataclass(frozen=True)
class HUSEvidenceBundle:
    json_text: str

    @property
    def payload(self) -> dict:
        # Return a fresh value; later mutation cannot change the validation snapshot.
        return json.loads(self.json_text)


def build_bundle(context: HUSRewriteContext) -> HUSEvidenceBundle:
    question, answer = context.question, context.answer
    if not question.allow_llm_rewrite:
        raise HUSLLMError('disabled')
    if (answer.status != 'answered' or answer.dataset not in {'f1', 'f2', 'f3'}
            or answer.major != question.major or answer.version != question.version
            or not answer.citations or not answer.release_id
            or not re.fullmatch(r'[A-Za-z0-9._-]{1,100}', answer.release_id)
            or not re.fullmatch(r'[0-9a-f]{64}', answer.release_sha256 or '')):
        _invalid()
    if answer.dataset == 'f3' and not question.allow_generated_reference:
        raise HUSLLMError('disabled')
    sources, ids, groups = [], set(), set()
    for citation in answer.citations:
        if (citation.dataset != answer.dataset or type(citation.citation_id) is not str
                or citation.citation_id in ids
                or not re.fullmatch(r'[1-9][0-9]{0,2}', citation.citation_id)
                or type(citation.quote) is not str or not citation.quote.strip()
                or not citation.review_status):
            _invalid()
        ids.add(citation.citation_id)
        meta = citation.metadata
        if not isinstance(meta, dict):
            _invalid()
        provenance = _mapping(meta, 'provenance')
        record = _mapping(provenance, 'portable_record')
        identity = _mapping(provenance, 'release_identity')
        bound = False
        for binding in (meta, identity):
            for key, expected in (('release_id', answer.release_id),
                                  ('release_sha256', answer.release_sha256)):
                if key in binding and binding[key] != expected:
                    _invalid()
            bound = bound or {'release_id', 'release_sha256'}.issubset(binding)
        if not bound:
            _invalid()
        scopes = [_mapping(meta, 'scope'), _mapping(record, 'scope')]
        for major in (meta.get('major'), record.get('major'),
                      *(scope.get('major') for scope in scopes)):
            if major is not None and major != answer.major:
                _invalid()
        versions = [scope['curriculum_version'] for scope in scopes if 'curriculum_version' in scope]
        variants = [scope['program_variant'] for scope in scopes if 'program_variant' in scope]
        if 'program_variant' in meta:
            variants.append(meta['program_variant'])
        if any(v is not None and type(v) is not str for v in versions + variants):
            _invalid()
        if len(set(versions)) > 1 or len(set(variants)) > 1:
            _invalid()
        version = versions[0] if versions else answer.version
        variant = variants[0] if variants else None
        if answer.version is not None and version != answer.version:
            _invalid()
        if question.program_variant and variant != question.program_variant:
            _invalid()
        codes = [meta.get('course_code'), record.get('course_code'),
                 answer.facts.get('course_code'), question.course_code]
        codes.extend(re.findall(r'(?<!\w)[A-Za-z]{3}\d{4}[A-Za-z]?(?!\w)', question.question))
        if any(code is not None and (type(code) is not str or
               not re.fullmatch(r'[A-Za-z]{3}\d{4}[A-Za-z]?', code)) for code in codes):
            _invalid()
        unique_codes = {code.upper() for code in codes if code is not None}
        if len(unique_codes) > 1:
            _invalid()
        code = next(iter(unique_codes), None)
        if answer.dataset == 'f3' and code is None:
            _invalid()
        if (answer.dataset == 'f3'
                and (citation.content_origin != 'generated' or citation.evidence_kind != 'ai')):
            _invalid()
        if answer.dataset == 'f1' and citation.content_origin == 'generated':
            _invalid()
        source_scope = {'major': answer.major, 'version': version,
                        'program_variant': variant, 'course_code': code,
                        'field': meta.get('field') or answer.facts.get('field') or question.field}
        if any(value is not None and type(value) is not str for value in source_scope.values()):
            _invalid()
        groups.add((version, variant, code, source_scope['field'],
                    citation.review_status, citation.content_origin))
        sources.append({'citation_id': citation.citation_id, 'quote': citation.quote,
                        'quote_sha256': sha256(citation.quote.encode('utf-8')).hexdigest(),
                        'review_status': citation.review_status,
                        'content_origin': citation.content_origin, 'scope': source_scope})
    if answer.dataset != 'f2' and len(groups) != 1:
        _invalid()
    payload = {'schema_version': 'hus-llm-evidence-v1', 'question': question.question,
               'release': {'id': answer.release_id, 'sha256': answer.release_sha256},
               'scope': {'dataset': answer.dataset, 'major': answer.major,
                         'version': answer.version, 'group_key': question.group_key},
               'facts': _facts(answer.facts) if answer.dataset == 'f2' else {}, 'sources': sources}
    try:
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                             separators=(',', ':'), allow_nan=False)
    except (ValueError, TypeError):
        _invalid()
    if len(encoded) > MAX_PROMPT_CHARS:
        raise HUSLLMError('prompt_budget')
    return HUSEvidenceBundle(encoded)


def build_evidence(context: HUSRewriteContext) -> HUSEvidenceBundle | HUSRewriteDocument:
    """Default protocol dispatcher; retain explicit v1 bundles for F2/legacy users."""
    bundle = build_bundle(context)
    if bundle.payload['scope']['dataset'] == 'f2':
        return bundle
    from .document import build_document

    return build_document(bundle)
