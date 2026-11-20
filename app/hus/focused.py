"""Explicit source resolution and bounded source paragraphs; no provider or gold IDs."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256

from app.hus.answer_support import SOURCE_FORMAT, _chunk_scope, _scope_query
from app.hus.question_routing import _requested_clauses
from app.hus.retrieval import RetrievalHit, _body, _tokens
from app.schemas.hus import HUSSourceChoice


def source_id(chunk):
    meta = chunk.metadata
    return meta.get('citation', {}).get('source_id') or meta.get('record_id') or chunk.chunk_id


@dataclass(frozen=True)
class SourceSelection:
    chunks: tuple
    choices: tuple[HUSSourceChoice, ...] = ()


def resolve_sources(chunks, request, variant, format_supported=None):
    """Use the complete eligible inventory, independent of top-k order."""
    _, editions = _scope_query(' '.join(_tokens(request.question)))
    if len(editions) > 1:
        return SourceSelection(())
    if editions and request.version and ' '.join(_tokens(request.version)) not in editions:
        return SourceSelection(())
    formats = {m['format'] for clause in _requested_clauses(request.question)
               if (m := SOURCE_FORMAT.match(_scope_query(clause)[0]))}
    if len(formats) > 1:
        return SourceSelection(())
    filtered = tuple(c for c in chunks
        if (not editions or ' '.join(_tokens(c.version)) in editions)
        and (not variant or c.metadata.get('program_variant') == variant)
        and (not request.source_id or source_id(c) == request.source_id)
        and (not formats or (format_supported is not None and all(
            format_supported(RetrievalHit(c, 0.0, ()), kind) for kind in formats)))
        and c.metadata.get('review_status') in ({'include', 'include_markdown'} if c.dataset == 'f1' else {'needs_review'})
        and (c.dataset != 'f3' or c.metadata.get('content_origin') == 'generated'))
    groups = {}
    for chunk in filtered:
        groups.setdefault(_chunk_scope(chunk), []).append(chunk)
    if len(groups) <= 1:
        return SourceSelection(filtered)
    choices = []
    for group in groups.values():
        c, meta = group[0], group[0].metadata
        choices.append(HUSSourceChoice(source_id=source_id(c), version=c.version,
            program_variant=meta.get('program_variant'),
            label=meta.get('citation', {}).get('title') or meta.get('title') or source_id(c),
            review_status=meta['review_status']))
    return SourceSelection((), tuple(sorted(choices, key=lambda c: (
        c.version, c.program_variant or '', c.source_id, c.review_status))))


# These identify concepts through descriptive text, not course/record/chunk IDs.
# New aliases need review and regression, rather than a similarity threshold.
TOPICS = {
    'object': (r'\bdoi tuong\b', r'\bdoi tuong (?:la|la mot the hien)|\bdoi tuong la mot the hien|\bdoi tuong la'),
    'inheritance': (r'\bke thua\b', r'\bke thua (?:bieu dien|la)\b'),
    'research_question': (r'\bcau hoi nghien cuu\b', r'\bcau hoi nghien cuu xac dinh\b'),
    'research_scope': (r'\bpham vi\b', r'\bpham vi gioi han\b'),
    'overfitting': (r'\bqua khop\b', r'\bco the ghi nho nhieu\b.*\bhuan luyen\b.*\bdu lieu moi\b'),
}
_GRAMMAR = re.compile(r'\b(?:duoc giai thich the nao|nhu the nao|ra sao|la gi|'
    r'giai thich|noi dung|khai niem|huong dan|gioi han|cho vi du|kem vi du|vi du|'
    r'hoc phan|mon hoc|trong mon|trong|mon|cac|nhung|va|dat|ve|hay|xin)\b')
_EVERYDAY = re.compile(r'^(?:noi dung )?[a-z]{3}\d{4}[a-z]? '
    r'(?:ly giai chuyen|giai thich vi sao) mo hinh (?:hoc thuoc|ghi nho) du lieu cu '
    r'nhung du doan kem tren du lieu moi(?: nhu the nao)?$')


def focused_content_request(question):
    text = ' '.join(_tokens(question))
    return (bool(re.search(r'\b(?:giai thich|ly giai)\b', text))
            and any(re.search(pattern, text) for pattern, _ in TOPICS.values()))


@dataclass(frozen=True)
class FocusRequest:
    topics: tuple[str, ...] = ()
    examples: bool = False
    whole: bool = False
    valid: bool = True
    related_only: bool = False
    guard_question: str = ''


def focus_request(request, chunks, field):
    question = request.question
    if field == 'introduction':
        # Consume a complete overview request; any trailing domain/condition stays.
        question = re.sub(r'^(?:cho (?:mình|tôi|em) )?(?:một )?bức tranh khái quát (?:về )?(?:ngành )?',
                          'Giới thiệu ngành ', question, flags=re.IGNORECASE)
    if field != 'content':
        return FocusRequest(guard_question=question)
    raw = ' '.join(_tokens(question))
    if _EVERYDAY.fullmatch(raw):
        return FocusRequest(('overfitting',), related_only=True, guard_question=question)
    text = raw
    # Only a COMPLETE course title used as a locator is consumed, not its words.
    names = {c.metadata.get('course_name', '') for c in chunks} - {''}
    for name in sorted(names, key=len, reverse=True):
        title = re.escape(' '.join(_tokens(name)))
        text = re.sub(r'\b(?:trong )?(?:mon(?: hoc)?|hoc phan) ' + title + r'\b', ' ', text)
    text = re.sub(r'\b[a-z]{3}\d{4}[a-z]?\b', ' ', text)
    whole = bool(re.search(r'\b(?:toan bo|day du|tat ca)\b', text))
    topics = tuple(key for key, (pattern, _) in TOPICS.items() if re.search(pattern, text))
    if not topics:
        return FocusRequest(whole=whole, guard_question=question)
    examples = bool(re.search(r'\bvi du\b', text))
    for topic in topics:
        text = re.sub(TOPICS[topic][0], ' ', text)
    text = _GRAMMAR.sub(' ', text)
    return FocusRequest(topics, examples, whole, not text.strip(), guard_question=question)


def description_span(chunk):
    """Keep a whole description including every adjacent sentence/condition."""
    quote = _body(chunk)
    if type(chunk.metadata.get('unit_index')) is not int:
        return None  # An overview/title list is not a definition.
    first = quote.find('\n')
    if first < 0:
        return None
    end = len(quote)
    for marker in ('\nKhái niệm thành phần:', '\nVí dụ minh họa'):
        pos = quote.find(marker)
        if pos >= 0:
            end = min(end, pos)
    start = first + 1
    # Only the known one-line keyword/example sections are independently
    # optional. An extra line may contain a condition/continuation: keep the
    # whole chunk rather than guessing that context is dispensable.
    tail = quote[end:].splitlines()
    if any(line.strip() and not line.startswith(('Khái niệm thành phần:', 'Ví dụ minh họa')) for line in tail):
        return (0, len(quote))
    for line in tail:
        if line.startswith('Khái niệm thành phần:'):
            content = line.split(':', 1)[1]
            qualifiers = ' '.join(_tokens(content))
            if (re.search(r'[.!?]\s+\S', content)
                    or re.search(r'\b(?:neu|khi|chi|tru|ngoai|voi dieu kien|tuy|khong|can|phai|'
                                 r'luon|tat ca|gioi han|ap dung|sau day|duoi day)\b', qualifiers)):
                return (0, len(quote))
        elif line.strip() and not re.match(r'^Ví dụ minh họa(?: do AI biên soạn)?:', line):
            return (0, len(quote))
    if re.search(r'\b(?:sau day|duoi day|vi du sau|dieu kien sau)\b',
                 ' '.join(_tokens(quote[start:end]))):
        return (0, len(quote))
    return (start, end) if quote[start:end].strip() else None


def select_focus_hits(hits, focus):
    if not focus.valid:
        return ()
    if not focus.topics:
        return hits
    chosen = {}
    for topic in focus.topics:
        matches = []
        for hit in hits:
            span = description_span(hit.chunk)
            if span and re.search(TOPICS[topic][1], ' '.join(_tokens(_body(hit.chunk)[slice(*span)]))):
                matches.append(hit)
        if not matches:
            return ()
        # Retain all matching descriptive chunks within the resolved source,
        # not a target/gold ID or a title-only hit.
        for hit in matches:
            chosen[hit.chunk.chunk_id] = hit
    return tuple(sorted(chosen.values(), key=lambda h: h.chunk.metadata['locator'].get('start_char', 0)))


def build_plan(request, hits, focus, release):
    units, aspects = [], []
    for i, hit in enumerate(hits, 1):
        chunk, quote = hit.chunk, _body(hit.chunk)
        span = description_span(chunk) if focus.topics and not focus.examples and not focus.whole else None
        start, end = span or (0, len(quote))
        # Keep literal lines/layout backend-owned; an aspect requires ALL its lines.
        offset = start
        for line in quote[start:end].splitlines(keepends=True):
            text = line.rstrip('\r\n')
            if text.strip():
                units.append({'id': f'u{len(units)+1:03}', 'citation_id': str(i),
                    'start': offset, 'end': offset + len(text), 'text': text,
                    'offset_scope': 'canonical_citation_quote',
                    'title': quote.splitlines()[0], 'source_id': source_id(chunk),
                    'quote_sha256': sha256(quote.encode()).hexdigest()})
            offset += len(line)
    for topic in focus.topics or ('requested_source',):
        required = []
        for i, hit in enumerate(hits, 1):
            span = description_span(hit.chunk)
            if topic == 'requested_source' or (span and re.search(TOPICS[topic][1],
                    ' '.join(_tokens(_body(hit.chunk)[slice(*span)])))):
                required.extend(u['id'] for u in units if u['citation_id'] == str(i))
        aspects.append({'id': topic, 'required_unit_ids': required})
    plan = {'schema_version': 'hus-focused-evidence-v1', 'question': request.question,
        'aspects': aspects, 'units': units, 'related_only': focus.related_only,
        'release': {'id': release['release_id'], 'sha256': release['release_sha256']},
        'scope': {'dataset': hits[0].chunk.dataset, 'major': request.major,
            'version': hits[0].chunk.version,
            'program_variant': hits[0].chunk.metadata.get('program_variant'),
            'field': hits[0].chunk.metadata.get('field'),
            'course_code': hits[0].chunk.metadata.get('course_code'), 'source_id': source_id(hits[0].chunk)}}
    return json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def render_plan(plan_json):
    plan = json.loads(plan_json)
    prefix = ('Một khái niệm liên quan trong nguồn; không kết luận đây là nguyên nhân duy nhất.\n\n'
              if plan['related_only'] else '')
    return prefix + '\n'.join(u['text'] + ' [' + u['citation_id'] + ']' for u in plan['units'])
