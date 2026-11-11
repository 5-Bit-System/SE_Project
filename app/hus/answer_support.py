"""Separate conversational request words from specific evidence requirements."""

import re
from collections import defaultdict
from collections.abc import Iterable

from app.hus.question_routing import TEACHING_TERMS, _requested_clauses, career_exclusions, has
from app.hus.retrieval import FIELD_LABELS, STOP_WORDS, RetrievalHit, _body, _tokens

# Request grammar is not a factual claim. Unknown topics still have to occur in
# the quoted body; matching only the intent label or a title is insufficient.
REQUEST_WORDS = frozenset(_tokens(
    "bạn kể giúp đọc trích nói liệt kê giải thích mô tả hình dung phác họa bức tranh "
    "mình tôi muốn cần chỉ đang hỏi xem biết nhờ vui lòng được không thế nào gì bao nhiêu "
    "ở đâu từ khi trước đây bắt đầu thời điểm năm tên gọi ban đầu hình thành lịch sử "
    "theo trang khoa tài liệu nguồn bản đã lưu chương trình đào tạo ngành hệ chuẩn tài năng "
    "sau cử nhân tốt nghiệp ra trường người học sinh viên học phần môn "
    "có thể khả năng cơ hội hướng lĩnh vực nhóm loại phần những nào nào "
    "nếu đủ điều kiện thạc sĩ tiến sĩ cao học nghiên cứu sinh học tiếp học lên cao hơn "
    "nghề nghiệp vị trí việc làm công việc vai trò đảm nhiệm cơ quan doanh nghiệp công ty đơn vị "
    "mục tiêu mục đích năng lực hướng tới xử lý giải quyết vấn đề thông tin dữ liệu nền tảng "
    "kết hợp ba xây dựng dùng nhằm làm kiến thức chủ đề nội dung gồm các phần "
    "gợi ý đề xuất tham khảo mức do AI sinh đồng ý cho phép bật quyền nhớ rõ nguồn gốc "
    "cũng và hay hoặc chưa chính đủ riêng với còn của về tại đến một hai ba "
    "mà như sẽ ghi nhé sao xong nhắc tục chuyên khung kỳ tiết "
    + " ".join(FIELD_LABELS.values()))) | STOP_WORDS


# Match complete request phrases rather than globally ignoring their component
# words (e.g. "định"/"quy" can belong to a substantive academic requirement).
REQUEST_PHRASES = (
    'khong suy sang quy dinh dang ap dung', 'khong phai quy dinh thi',
    'chi coi day la de xuat', 'giu ro gioi han nguon', 'kem canh bao nguon goc',
    'tac gia da liet ke', 'nhung hoat dong nao', 'toi nen hieu',
    'giup toi hieu', 'toi muon hieu', 'rieng doan',
)
REQUEST_SYNTAX = re.compile(r'\b(?:' + '|'.join(map(re.escape, REQUEST_PHRASES)) + r')\b')
# These verbs are also factual skills ("năng lực trình bày"). Only an imperative
# at the start of an active clause is presentation syntax, not a domain claim.
COMMAND_SYNTAX = re.compile(r'^\s*(?:(?:toi|minh) (?:muon|can|nho) )?'
                            r'(?:(?:ban|hay|xin|nho|vui long) )*(?:trinh bay|trich doan|chep)\b')
# Only explicit refusal of a bounded workplace request is presentation syntax.
# Factual negation ("không có ...") and later affirmative objects stay active.
WORKPLACE_REFUSAL = re.compile(
    r'\b(?:khong (?:hoi|can|yeu cau)|dung hoi) (?:(?:ve|den) )?'
    r'(?:(?:cong viec|viec lam|co hoi nghe nghiep|nghe nghiep) (?:(?:trong|tai|o) )?)?'
    r'(?:doanh nghiep|cong ty)\b')


def _scope_query(query: str) -> tuple[str, set[str]]:
    """Recognize explicit edition identifiers; never neutralize arbitrary years."""
    versions = set()

    def edition(match):
        value = match[1]
        versions.add('unknown' if value in {'chua xac dinh', 'chua ro', 'khong ro', 'unknown'}
                     else re.sub(r'^qd\s*', 'qd', value))
        return ' '

    query = re.sub(r'\b(?:edition|phien ban) (chua xac dinh|chua ro|khong ro|unknown|'
                   r'qd\s*\d{3,6} \d{4}|\d{4})\b', edition, query)

    def decision(match):
        versions.add(f'qd{match[1]} {match[2]}')
        return ' '

    query = re.sub(r'\b(?:qd\s*|quyet dinh )(\d{3,6}) (\d{4})\b', decision, query)
    return query, versions


def _source_scope(hit: RetrievalHit) -> tuple:
    """A source passage can continue only inside the same identity/review scope."""
    chunk, meta = hit.chunk, hit.chunk.metadata
    citation = meta.get('citation', {})
    source = citation.get('source_id') or meta.get('record_id') or chunk.chunk_id
    return (chunk.dataset, chunk.major, chunk.version, meta.get('program_variant'),
            meta.get('field'), meta.get('course_code'), meta.get('content_origin'),
            meta.get('review_status'), chunk.package_path, chunk.package_sha256, source,
            citation.get('source_sha256'), citation.get('evidence_path'))


def _qualifier_supported(phrase: str, hit: RetrievalHit) -> bool:
    body = " " + " ".join(_tokens(_body(hit.chunk))) + " "
    if f" {phrase} " in body:
        return True
    variants = {"he chuan": "standard", "tai nang": "talent", "he chat luong cao": "high_quality",
                "he tien tien": "advanced"}
    if phrase in variants:
        return (hit.chunk.metadata.get("program_variant") == variants[phrase]
                or f" he cu nhan {phrase.removeprefix('he ')} " in body)
    return False


def supported_hits(question: str, hits: tuple[RetrievalHit, ...], *,
                   aliases: dict[str, tuple[str, ...]], codes: set[str],
                   extra_neutral: Iterable[str] = ()) -> tuple[RetrievalHit, ...]:
    """Cover factual requirements with exact excerpts from one scoped source.

    Metadata can satisfy explicit edition identity, never a numerical/domain
    claim. Multiple passages may jointly cover a question, but different sources,
    versions, variants, fields or review states cannot complete each other.
    """
    clauses, versions = [], set()
    for clause in _requested_clauses(question):
        text, editions = _scope_query(clause)
        versions.update(editions)
        clauses.append(REQUEST_SYNTAX.sub(' ', COMMAND_SYNTAX.sub(' ', text)))
    query = ' '.join(clauses)
    if len(versions) > 1:
        return ()
    hits = tuple(hit for hit in hits if not versions or ' '.join(_tokens(hit.chunk.version)) in versions)
    neutral = set(REQUEST_WORDS)
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
