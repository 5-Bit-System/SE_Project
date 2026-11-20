"""Compatibility with Workspace's established lexical answer policy."""

import re
from collections import defaultdict
from collections.abc import Iterable

from app.hus.answer_support import (
    COMMAND_SYNTAX,
    REQUEST_SYNTAX,
    REQUEST_WORDS,
    WORKPLACE_REFUSAL,
    _qualifier_supported,
    _scope_query,
    _source_scope,
    supported_hits,
)
from app.hus.answering import HUSAnswerer, question_intent
from app.hus.question_routing import (
    CAREER_TERMS,
    COURSE_FIELD_TERMS,
    CREDIT_TERMS,
    TEACHING_TERMS,
    _assessment_text,
    _prerequisite_text,
    _requested_clauses,
    assessment_fact_request,
    career_exclusions,
    course_overview_requested,
    has,
    out_of_scope,
    requested_program_fields,
    requested_text,
)
from app.hus.retrieval import COURSE_CODE, RetrievalHit, _body, _tokens

# Workspace accepts these common parts of a request across exact source excerpts.
WORKSPACE_REQUEST_WORDS = REQUEST_WORDS | frozenset((
    "khung", "ky", "tiet", "bang", "roi", "ngoai", "vao", "tap", "coi", "dat",
))
WORKSPACE_CAREER_TERMS = (*CAREER_TERMS, "nghien cuu va phat trien", "co hoi lam")
WORKSPACE_FIELDS = {
    **COURSE_FIELD_TERMS,
    "credits": CREDIT_TERMS,
    "suggested_assessment": (
        "danh gia", "thi", "bai kiem tra", "hinh thuc kiem tra",
        "kiem tra danh gia", "thi giua ky", "thi cuoi ky",
    ),
    "objectives": ("muc tieu", "chuan dau ra", "nang luc", "huong toi", "dao tao de", "muc dich dao tao"),
}


def _workspace_rule(question: str) -> tuple[str | None, str | None]:
    clauses = _requested_clauses(question)
    text = " ".join(clauses)
    course = any(COURSE_CODE.fullmatch(t) for t in _tokens(text)) or has(text, "hoc phan", "mon hoc")
    if assessment_fact_request(question):
        return "f3", "official_assessment"
    if out_of_scope(question):
        return None, None
    program_fields = requested_program_fields(question)
    if program_fields:
        return "f2", program_fields[0]
    if has(text, *WORKSPACE_FIELDS["credits"]):
        return "f2", "credits"
    if has(_prerequisite_text(clauses), *WORKSPACE_FIELDS["prerequisites"]):
        return "f2", "prerequisites"
    if has(text, *WORKSPACE_FIELDS["hours"]):
        return "f2", "hours"
    if has(text, *WORKSPACE_FIELDS["name"]):
        return "f2", "name"
    if has(text, "hoc tiep", "sau dai hoc", "hoc len", "cao hoc", "nghien cuu sinh", "hoc cao hon"):
        return "f1", "further_study"
    corporate_subject = (bool(re.search(r'\bvai tro (?:nao |gi )?cua (?:cac )?(?:doanh nghiep|cong ty)\b', text))
                         or bool(re.match(r'^(?:(?:cac|nhung|mot) )?(?:doanh nghiep|cong ty)\b', text)))
    role_at_work = (bool(re.search(r'\bvai tro (?:nao|gi)\b', text))
                   and has(text, 'doanh nghiep', 'cong ty') and not corporate_subject
                   and not has(text, *WORKSPACE_FIELDS['objectives'], *WORKSPACE_FIELDS['content'],
                               'gioi thieu', 'tong quan', 'mon', 'hoc phan', 'chuong trinh', 'ctdt', 'nhom', 'dao tao'))
    if not course and (has(text, *WORKSPACE_CAREER_TERMS) or role_at_work):
        return "f1", "careers"
    if has(_assessment_text(text), *WORKSPACE_FIELDS["suggested_assessment"]):
        return "f3", "suggested_assessment"
    if has(text, *WORKSPACE_FIELDS["objectives"]):
        return ("f3", "objectives") if course else ("f1", "objectives")
    if has(text, *WORKSPACE_FIELDS["content"]):
        return "f3", "content"
    if course and course_overview_requested(text):
        return "f3", "content"
    if not course and has(text, "gioi thieu", "tong quan", "nganh", "chuong trinh", "nen tang", "lich su hinh thanh"):
        return "f1", "introduction"
    return None, None



def _workspace_course_fields(question: str) -> tuple[str, ...]:
    """Detect explicit course fields before the single-field routing priority.

    Repeated synonyms count once. Reuse preview disambiguation so 'hình dung
    trước môn' does not acquire a prerequisite request.
    """
    clauses = _requested_clauses(question)
    text = " ".join(clauses)
    # 'Cần học những môn nào trước môn X?' asks for prerequisites, not
    # syllabus content. A separate affirmative 'và học những gì?' remains.
    content_parts = []
    for clause in clauses:
        for part in re.split(r"\bva\b", clause):
            if (has(_prerequisite_text((part,)), *WORKSPACE_FIELDS["prerequisites"])
                    or has(part, "can hoc", "phai hoc")):
                part = re.sub(r"\bhoc (?:gi|nhung)\b", "hoc", part)
            content_parts.append(part)
    fields = []
    for field, terms in WORKSPACE_FIELDS.items():
        active = _prerequisite_text(clauses) if field == "prerequisites" else text
        if field == "content":
            active = " ".join(content_parts)
            active = re.sub(r"\bnoi dung (?:ai|do ai|tham khao|sinh)\b", " ", active)
            active = re.sub(r"\bcho phep dung noi dung\b", " ", active)
        if has(active, *terms):
            fields.append(field)
    return tuple(fields)



def _workspace_evidence(question: str, hits: tuple[RetrievalHit, ...], *,
                   aliases: dict[str, tuple[str, ...]], codes: set[str],
                   extra_neutral: Iterable[str] = (),
                   format_supported=None, source_catalog=None) -> tuple[RetrievalHit, ...]:
    """Cover factual requirements with exact excerpts from one scoped source.

    Metadata can satisfy explicit edition identity, never a numerical/domain
    claim. Multiple passages may jointly cover a question, but different sources,
    versions, variants, fields or review states cannot complete each other.
    """
    if has(requested_text(question), "pdf", "docx", "ban word", "clc"):
        return supported_hits(
            question, hits, aliases=aliases, codes=codes, extra_neutral=extra_neutral,
            format_supported=format_supported, source_catalog=source_catalog,
        )
    clauses, versions = [], set()
    for clause in _requested_clauses(question):
        text, editions = _scope_query(clause)
        versions.update(editions)
        clauses.append(REQUEST_SYNTAX.sub(' ', COMMAND_SYNTAX.sub(' ', text)))
    query = ' '.join(clauses)
    if len(versions) > 1:
        return ()
    hits = tuple(hit for hit in hits if not versions or ' '.join(_tokens(hit.chunk.version)) in versions)
    neutral = set(WORKSPACE_REQUEST_WORDS)
    for names in aliases.values():
        for name in names:
            neutral.update(_tokens(name))
    neutral.update(c.lower() for c in codes)
    neutral.update(_tokens(" ".join(extra_neutral)))
    for hit in hits:
        neutral.update(_tokens(hit.chunk.metadata.get("course_name", "")))
    if hits and all(hit.chunk.dataset == "f3" for hit in hits):
        neutral.update(("day", "cot", "loi", "chuong", "trong", "tam"))
    specific = set(_tokens(query)) - neutral
    # These are factual qualifications even though their individual words can
    # occur in ordinary requests to enumerate programs or describe a degree.
    qualifiers = re.findall(r"\btai nang\b|\bhe (?:chuan|chat luong cao|tien tien)\b|\b(?:mot|hai|ba|\d+) nam\b", query)
    if hits and hits[0].chunk.metadata.get("field") != "further_study":
        qualifiers.extend(re.findall(r"\b(?:thac si|tien si|cao hoc|nghien cuu sinh)\b", query))
    # A requested workplace is factual context, even when its component words
    # also occur in generic career-request grammar. Require the complete phrase
    # in a source body, not a title or scattered words ("kinh doanh ... nghiệp").
    workplaces = {place for clause in clauses for place in
                  re.findall(r"\b(?:doanh nghiep|cong ty)\b", WORKPLACE_REFUSAL.sub(' ', clause))}
    workplaces.update(re.findall(r'\b(?:o|tai|trong) (?:cac )?(truong(?: dai hoc)?)\b', query))
    groups = defaultdict(list)
    excluded = career_exclusions(question)
    for hit in hits:
        # Keep canonical excerpts intact. A mixed/excluded quote cannot supply
        # positive evidence; if clean remaining passages are insufficient, refuse.
        if hit.chunk.dataset == 'f1' and hit.chunk.metadata.get('field') == 'careers' and excluded:
            body = ' '.join(_tokens(_body(hit.chunk)))
            if has(body, *TEACHING_TERMS) and any(place is None or has(body, place) for place in excluded):
                continue
        if all(_qualifier_supported(phrase, hit) for phrase in qualifiers):
            groups[_source_scope(hit)].append(hit)
    for group in groups.values():
        context_ids = set()
        if group[0].chunk.dataset == 'f1' and group[0].chunk.metadata.get('field') == 'careers':
            bodies = {hit.chunk.chunk_id: " " + " ".join(_tokens(_body(hit.chunk))) + " " for hit in group}
            if any(not any(f" {place} " in body for body in bodies.values()) for place in workplaces):
                continue
            context_ids = {key for key, body in bodies.items() if any(f" {place} " in body for place in workplaces)}
        words = {hit.chunk.chunk_id: set(_tokens(_body(hit.chunk))) for hit in group}
        if not specific <= set().union(*words.values()):
            continue
        selected = [hit for hit in group if not specific or specific & words[hit.chunk.chunk_id]
                    or hit.chunk.chunk_id in context_ids]
        # Render continuations in physical source order, rather than BM25 order.
        return tuple(sorted(selected, key=lambda h: h.chunk.metadata.get('locator', {}).get('start_char', 0)))
    return ()



def _workspace_intent(question: str) -> tuple[str | None, str | None]:
    return question_intent(question, rule=_workspace_rule)


class WorkspaceAnswerer(HUSAnswerer):
    """Use the Workspace routes and guard with the shared canonical answer builder."""

    route_question = staticmethod(_workspace_intent)
    course_fields = staticmethod(_workspace_course_fields)
    select_evidence = staticmethod(_workspace_evidence)
