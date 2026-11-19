"""Separate conversational request words from specific evidence requirements."""

import re
import unicodedata
from collections import defaultdict
from collections.abc import Callable

from app.hus.question_routing import (
    ASSESSMENT_COMPOUNDS,
    COURSE_OVERVIEW,
    FURTHER_STUDY_HEADINGS,
    FURTHER_STUDY_TERMS,
    TEACHING_TERMS,
    VALUE_COMPOUNDS,
    WORKPLACE_PATTERN,
    _requested_clauses,
    career_exclusions,
    concept_requested,
    has,
    program_variant_scope,
    variant_enumeration_requested,
)
from app.hus.rag_loader import RAGChunk
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
    "mà như sẽ ghi nhé sao xong nhắc tục chuyên "
    + " ".join(FIELD_LABELS.values()))) | STOP_WORDS


# Match complete request phrases rather than globally ignoring their component
# words (e.g. "định"/"quy" can belong to a substantive academic requirement).
REQUEST_PHRASES = (
    'khong suy sang quy dinh dang ap dung', 'khong phai quy dinh thi',
    'chi coi day la de xuat', 'giu ro gioi han nguon', 'kem canh bao nguon goc',
    'tac gia da liet ke', 'nhung hoat dong nao', 'toi nen hieu',
    'giup toi hieu', 'toi muon hieu', 'rieng doan',
    'moc bat dau', 'duoc dien giai the nao',
)
REQUEST_SYNTAX = re.compile(r'\b(?:' + '|'.join(map(re.escape, REQUEST_PHRASES)) + r')\b')
# These verbs are also factual skills ("năng lực trình bày"). Only an imperative
# at the start of an active clause is presentation syntax, not a domain claim.
COMMAND_SYNTAX = re.compile(r'^\s*(?:(?:toi|minh) (?:muon|can|nho) )?'
                            r'(?:(?:ban|hay|xin|nho|vui long) )*'
                            r'(?:trinh bay|trich doan|chep|gioi thieu|dien giai|mo ta|giai thich|tim hieu)\b')
REQUEST_OPENING = re.compile(r'^(?:cho (?:em|minh|toi) (?:hoi|biet)|'
                             r'(?:em|minh|toi) muon hoi|ban cho (?:em|minh|toi) biet)\b')
CAREER_QUESTION_SUBJECT = re.compile(
    r'^(?P<context>(?:(?:sau khi tot nghiep|tot nghiep|hoc xong|ra truong)\b.*?)?\s*)'
    r'\bem (?=(?:co the )?(?:lam viec|lam o dau|lam nghe)\b)')
GREETING_CLAUSE = re.compile(r'^(?:xin )?chao(?: ban)?$')
# Only explicit refusal of a bounded workplace request is presentation syntax.
# Factual negation ("không có ...") and later affirmative objects stay active.
WORKPLACE_REFUSAL = re.compile(
    r'\b(?:khong (?:hoi|can|yeu cau)|dung hoi) (?:(?:ve|den) )?'
    r'(?:(?:cong viec|viec lam|co hoi nghe nghiep|nghe nghiep) (?:(?:trong|tai|o) )?)?'
    r'(?:doanh nghiep|cong ty)\b')
PURPOSE_REQUEST = re.compile(r'\b(?:dao tao (?:de|nham)|muc dich(?: dao tao)?|muc tieu chung)\b')
PURPOSE_SOURCE = re.compile(
    r'^(?:\d+ )*(?:(?:chuong trinh|nganh|viec dao tao|dao tao)\b.{0,220}\b(?:nham|de)\b'
    r'|muc dich\b|muc tieu (?:chung|dao tao)\b'
    r'|muc tieu (?:cua )?(?:chuong trinh|nganh)\b.{0,220}\bdao tao\b)')
PURPOSE_HEADING = re.compile(r'^(?:\d+ )*(?:muc tieu(?: chung| dao tao| cua chuong trinh dao tao)?'
                             r'|muc dich(?: dao tao)?)$')
FORMER_NAME_REQUEST = re.compile(r'\b(?:tung mang ten|ten (?:cu|goi truoc day)|truoc day mang ten)\b')
FORMER_NAME_SOURCE = re.compile(r'\b(?:truoc (?:day|kia) (?:la|mang ten)|ten cu|doi ten|tien than)\b')
ACCOMPANYING_CONDITION_REQUEST = re.compile(
    r'(?<!khong )(?<!chua )(?<!duoc )\b(?:duoc )?(?:neu|ghi|liet ke)'
    r'(?: (?P<object>kha nang hoc tiep|kha nang hoc sau dai hoc|co hoi nghe nghiep|vi tri viec lam))?'
    r' kem (?:nhung |cac )?dieu kien '
    r'(?:nao|gi|ra sao|nhu the nao|the nao)\b')
CONDITION_SOURCE = re.compile(
    r'(?<!khong )(?<!chua )\b(?:tuy (?:theo|thuoc)|'
    r'(?:neu|khi) (?:(?:khong|chua) )?(?:du|dap ung)|voi dieu kien)\b'
    r'|^(?:(?:\d+ )?kha nang hoc tap nang cao trinh do sau khi tot nghiep )?'
    r'(?:sinh vien|cu nhan|nguoi hoc) (?:co )?du dieu kien va co nhu cau'
    r'(?: hoc tap nang cao trinh do)?(?: trong linh vuc chuyen mon(?: cua minh)?)?'
    r' (?:se )?co the hoc tiep\b')
AI_PROFILE_LOCATOR = re.compile(r'\b(?:trong|theo|tu) ho so ai tham khao(?: da luu)?\b')
COURSE_PROFILE_LOCATOR = re.compile(r'\bho so (?:mon|hoc phan) (?P<code>[a-z]{3}\d{4}[a-z]?)\b')
SOURCE_FORMAT = re.compile(r'^(?:(?:theo|trong|tu) )?(?:ban|tai lieu|nguon|tep) (?P<format>pdf|docx)\b')
WHOLE_FIELD = re.compile(r'\btoan bo (?:(?:cac|nhung) )?(?P<field>muc tieu|noi dung)\b')
SOURCE_NEGATED = re.compile(r'(?<!neu )(?<!khi )(?<!voi dieu kien )\b(?:khong|chua) '
                            r'(?:duoc )?(?:co|neu|ghi|luu|nam|liet ke|trinh bay|dung)\b')
WORKPLACE_OBJECT = re.compile(
    r'\b(?:o|tai|trong) (?:(?:cac|nhung|don vi) )*' + WORKPLACE_PATTERN
    + r'(?: (?:va|hoac) (?:(?:cac|nhung|don vi) )*' + WORKPLACE_PATTERN + r')*\b')


def _workplace_body(text: str) -> str:
    """Do not fold personnel 'viên' into institutional 'viện' evidence."""
    text = unicodedata.normalize('NFC', text).casefold()
    text = re.sub(r'\bviên\b', ' ', text)
    # For unaccented sources retain conservative, bounded personnel compounds.
    text = re.sub(r'\b(?:sinh|giang|nhan|lap trinh|chuyen|ky thuat|cong tac|nghien cuu) vien\b', ' ', text)
    text = ' '.join(_tokens(text))
    return re.sub(r'\b(?:(?:thi|moi|hien|cong|chien|nong|lam) truong|'
                  r'truong (?:hop|phai|luc|dien|tu|vector))\b', ' ', text)


def _presentation_syntax(clause: str, *, content: bool, purpose: bool, learning_basis: bool = False,
                         source_subject_words: set[str] | None = None) -> str:
    """Remove bounded question grammar; retain factual presentation skills/topics."""
    if learning_basis:
        # Retain the objects; the source must separately state their basis role.
        clause = re.sub(r'\bdua tren\b', ' ', clause)
    if purpose:
        clause = re.sub(r'\bphuc vu (?:nhung|cac) bai toan\b', ' ', clause)
    if re.search(r'\b(?:khong|chua) (?:duoc )?trinh bay\b', clause):
        return clause
    # The passive question ending is grammar; any earlier skill/topic remains.
    clause = re.sub(r'\bduoc trinh bay (?:ra sao|nhu the nao|the nao)$', ' ', clause)
    subject = re.match(r'^(.*?)\btrinh bay\b', clause)
    if (source_subject_words is not None and subject
            and re.match(r'^(?:theo |trong )?(?:ban )?(?:tai lieu|nguon|trang|chuong trinh|nganh)\b', subject[1])
            and set(_tokens(subject[1])) <= source_subject_words):
        clause = clause[:subject.start()] + subject[1] + clause[subject.end():]
    if content:
        clause = re.sub(r'\btrinh bay (?:gi|nhu the nao|the nao)$', ' ', clause)
        clause = re.sub(r'^((?:noi dung|chu de) (?:(?:ai|tham khao|cua|mon|hoc phan|'
                        r'[a-z]{3}\d{4}[a-z]?) )*)trinh bay\b', r'\1', clause)
    return clause


def _learning_basis_ids(group):
    """Explicit positive basis language, from the same further-study source."""
    if group[0].chunk.dataset != 'f1' or group[0].chunk.metadata.get('field') != 'further_study':
        return set()
    return {hit.chunk.chunk_id for hit in group for part in re.split(r'[.!?;]+', _body(hit.chunk))
            if (has(' '.join(_tokens(part)), 'la tien de', 'la nen tang', 'la co so',
                    'tao tien de', 'lam nen tang', 'lam co so', 'dua tren')
                and not has(' '.join(_tokens(part)), 'khong', 'chua'))}


def _purpose_material(group):
    """Find explicit program aims, without treating a skills list as its purpose."""
    selected, total = [], 0
    for hit in group:
        parts = [part for part in re.split(r'\n\s*\n', _body(hit.chunk)) if part.strip()]
        included = set()
        for index, part in enumerate(parts):
            words = _tokens(part)
            total += len(words)
            normalized = ' '.join(words)
            if (not PURPOSE_SOURCE.search(normalized)
                    or re.match(r'^(?:\d+ )*muc tieu dao tao (?:chuan dau ra|sinh vien co nang luc)\b',
                                normalized)):
                continue
            if len(words) <= 6 or PURPOSE_HEADING.fullmatch(' '.join(words)):
                # A heading alone is insufficient; never borrow across a hit/gap.
                if (index + 1 >= len(parts) or parts[index + 1].lstrip().startswith('#')
                        or len(_tokens(parts[index + 1])) < 8
                        or re.match(r'^(?:chuan dau ra|sinh vien co nang luc)\b',
                                    ' '.join(_tokens(parts[index + 1])))):
                    continue
                included.add(index + 1)
            included.add(index)
        selected.extend(word for index in included for word in _tokens(parts[index]))
    return set(selected), len(selected) / total if total else 0


def training_purpose_requested(question):
    active = ' '.join(_requested_clauses(question))
    return bool(PURPOSE_REQUEST.search(active)) and not has(active, 'chuan dau ra', 'nang luc', 'ky nang')


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
    return _chunk_scope(hit.chunk)


def _chunk_scope(chunk: RAGChunk, *, coverage_identity: bool = False) -> tuple:
    meta = chunk.metadata
    citation = meta.get('citation', {})
    source = citation.get('source_id') or meta.get('record_id') or chunk.chunk_id
    return (chunk.dataset, chunk.major, chunk.version, meta.get('program_variant'),
            meta.get('field'), meta.get('course_code'), None if coverage_identity else meta.get('content_origin'),
            None if coverage_identity else meta.get('review_status'), chunk.package_path, chunk.package_sha256, source,
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


VARIANT_BODY_PHRASES = {
    'standard': ('he chuan', 'chuong trinh chuan', 'he cu nhan chuan', 'cu nhan he chuan'),
    'talent': ('he tai nang', 'chuong trinh tai nang', 'he cu nhan tai nang', 'cu nhan tai nang'),
    'high_quality': ('he chat luong cao', 'chuong trinh chat luong cao', 'he clc', 'chuong trinh clc'),
    'advanced': ('he tien tien', 'chuong trinh tien tien', 'he cu nhan tien tien'),
}


def _study_request_condition(condition, aliases, codes, hits):
    """Only a full benign desire wrapper; added qualifications never disappear."""
    grammar = ' ' + condition + ' '
    names = {name for values in aliases.values() for name in values}
    names.update(' '.join(_tokens(h.chunk.metadata.get('course_name', ''))) for h in hits)
    names.update(code.lower() for code in codes)
    for name in sorted(names - {''}, key=len, reverse=True):
        grammar = grammar.replace(' ' + name + ' ', ' ')
    grammar = ' '.join(grammar.split())
    return bool(re.fullmatch(
        r'(?:(?:em|toi|minh|ban) )?muon '
        r'(?:hoc(?: tiep|len)?(?: sau(?: khi)?(?: tot nghiep)?)?|tim hieu|hoi)', grammar))


def supported_hits(question: str, hits: tuple[RetrievalHit, ...], *,
                   aliases: dict[str, tuple[str, ...]], codes: set[str],
                   format_supported: Callable[[RetrievalHit, str], bool] | None = None,
                   source_catalog: Callable[[], tuple[RAGChunk, ...]] | None = None) -> tuple[RetrievalHit, ...]:
    """Cover factual requirements with exact excerpts from one scoped source.

    Metadata can satisfy explicit edition identity, never a numerical/domain
    claim. Multiple passages may jointly cover a question, but different sources,
    versions, variants, fields or review states cannot complete each other.
    """
    clauses, versions, variants = [], set(), set()
    formats, whole_fields = set(), set()
    source_denied = False
    f1_scope = bool(hits) and all(hit.chunk.dataset == 'f1' for hit in hits)
    requested = ' '.join(_requested_clauses(question))
    # A conditional question cannot borrow the opposite eligibility condition.
    # Request wrappers ("nếu muốn học tiếp") are not factual prerequisites;
    # substantive conditional objects, including their negation, stay literal.
    conditional_objects = []
    raw = unicodedata.normalize('NFC', question)
    for match in re.finditer(r'\b(?:nếu|neu)\s+([^;.!?]+?)\s+thì\b', raw, flags=re.IGNORECASE):
        condition = ' '.join(_tokens(match[1]))
        if not _study_request_condition(condition, aliases, codes, hits):
            conditional_objects.append(condition)
    content = has(requested, 'noi dung', 'chu de') and not has(requested, 'nang luc', 'ky nang', 'chuan dau ra')
    purpose_requested = training_purpose_requested(question)
    former_name = bool(FORMER_NAME_REQUEST.search(requested))
    learning_basis = (has(requested, *FURTHER_STUDY_TERMS, *FURTHER_STUDY_HEADINGS) and has(requested, 'dua tren')
                      and not has(requested, 'khong dua tren', 'chua dua tren'))
    condition_requested = bool(ACCOMPANYING_CONDITION_REQUEST.search(requested))
    ai_profile_requested = bool(AI_PROFILE_LOCATOR.search(requested) or COURSE_PROFILE_LOCATOR.search(requested))
    further_study_scope = f1_scope and all(h.chunk.metadata.get('field') == 'further_study' for h in hits)
    career_scope = f1_scope and all(h.chunk.metadata.get('field') == 'careers' for h in hits)
    source_subject_words = set(_tokens('theo trong ban tai lieu nguon trang chuong trinh dao tao nganh cua'))
    for names in aliases.values():
        for name in names:
            source_subject_words.update(_tokens(name))
    for clause in _requested_clauses(question):
        if GREETING_CLAUSE.fullmatch(clause):
            continue
        clause = REQUEST_OPENING.sub(' ', clause).strip()
        if career_scope:
            clause = CAREER_QUESTION_SUBJECT.sub(r'\g<context>', clause)
        text, editions = _scope_query(clause)
        versions.update(editions)
        if f1_scope:
            text, scope_variants = program_variant_scope(text)
            variants.update(scope_variants)
        text = ' '.join(text.split())
        source_denied |= bool(SOURCE_NEGATED.search(text))
        if match := SOURCE_FORMAT.match(text):
            formats.add(match['format'])
            text = text[match.end():].lstrip()
        def whole_field(match):
            field = match['field']
            whole_fields.add('objectives' if field == 'muc tieu' else 'content')
            return field
        text = WHOLE_FIELD.sub(whole_field, text)
        text = _presentation_syntax(text, content=content, purpose=purpose_requested, learning_basis=learning_basis,
                                    source_subject_words=source_subject_words if f1_scope else None)
        # Keep the named/generic object while consuming only condition-question grammar.
        text = ACCOMPANYING_CONDITION_REQUEST.sub(lambda m: m['object'] or ' ', text)
        text = AI_PROFILE_LOCATOR.sub(' ', text)
        text = COURSE_PROFILE_LOCATOR.sub(r'\g<code>', text)
        if f1_scope:
            text = re.sub(r'\bvao (?=nam (?:\d{4}|nao)\b)', ' ', text)
            text = re.sub(r'\bphai khong$', ' ', text)
        if further_study_scope:
            text = re.sub(r'\bhoc tap (?:va )?nang cao(?: trinh do)?\b', 'hoc tiep', text)
        if ai_profile_requested:
            text = re.sub(r'\bmuc tieu hoc tap\b', 'muc tieu', text)
        if career_scope:
            text = re.sub(r'\bchuc danh\b|\bvai tro cong tac (?:nao|gi)\b', ' ', text)
        if former_name:
            text = FORMER_NAME_REQUEST.sub(' ', text)
        text = COURSE_OVERVIEW.sub(' ', text)
        if (concept_requested(question) and hits
                and all(h.chunk.dataset == 'f3' and h.chunk.metadata.get('field') == 'content' for h in hits)):
            text = re.sub(r'\b(?:se )?(?:gap|hoc) (?:cac |nhung )?khai niem (?:gi|nao)\b', ' ', text)
            text = re.sub(r'^\s*(?:giai thich|tim hieu)(?: ve)? (?:cac |nhung )?khai niem\b', ' ', text)
        clauses.append(REQUEST_SYNTAX.sub(' ', COMMAND_SYNTAX.sub(' ', text)))
    query = ' '.join(clauses)
    variant_enumeration = (f1_scope and len(variants) > 1
                           and all(h.chunk.metadata.get('field') == 'introduction' for h in hits)
                           and variant_enumeration_requested(question))
    if (formats or ai_profile_requested or whole_fields or variant_enumeration) and source_denied:
        # A source selector remains in force across punctuation. Its negative
        # claim cannot become a request for positive evidence in another clause.
        return ()
    domain_phrases = tuple(phrase for phrase in ASSESSMENT_COMPOUNDS + VALUE_COMPOUNDS if has(query, phrase))
    if len(versions) > 1 or (len(variants) > 1 and not variant_enumeration) or len(formats) > 1 or len(whole_fields) > 1:
        return ()
    hits = tuple(hit for hit in hits
                 if (not versions or ' '.join(_tokens(hit.chunk.version)) in versions)
                 and (not variants or variant_enumeration or hit.chunk.metadata.get('program_variant') in variants)
                 and (not ai_profile_requested or (hit.chunk.dataset == 'f3'
                      and hit.chunk.metadata.get('content_origin') == 'generated'
                      and hit.chunk.metadata.get('review_status') == 'needs_review'))
                 and (not formats or (format_supported is not None
                      and all(format_supported(hit, kind) for kind in formats))))
    neutral = set(REQUEST_WORDS)
    for names in aliases.values():
        for name in names:
            neutral.update(_tokens(name))
    neutral.update(c.lower() for c in codes)
    for hit in hits:
        neutral.update(_tokens(hit.chunk.metadata.get("course_name", "")))
    specific = set(_tokens(query)) - neutral
    # These are factual qualifications even though their individual words can
    # occur in ordinary requests to enumerate programs or describe a degree.
    qualifiers = re.findall(r"\btai nang\b|\bhe (?:chuan|chat luong cao|tien tien)\b|\b(?:mot|hai|ba|\d+) nam\b", query)
    if hits and hits[0].chunk.metadata.get("field") != "further_study":
        qualifiers.extend(re.findall(r"\b(?:thac si|tien si|cao hoc|nghien cuu sinh)\b", query))
    if condition_requested:
        # Remaining conditional objects are facts, including their negation.
        qualifiers.extend(match[0].strip() for clause in clauses for match in
                          re.finditer(r'\b(?:neu|khi|voi dieu kien|tuy theo|tuy thuoc)\b.*$', clause))
    # A requested workplace is factual context, even when its component words
    # also occur in generic career-request grammar. Require the complete phrase
    # in a source body, not a title or scattered words ("kinh doanh ... nghiệp").
    workplaces = {place for clause in clauses for place in
                  re.findall(r"\b(?:doanh nghiep|cong ty)\b", WORKPLACE_REFUSAL.sub(' ', clause))}
    # Keep comma-separated workplace objects before ordinary clause splitting.
    workplace_list = re.sub(r',\s*(?=(?:trường|truong|viện|vien|đại học|dai hoc|'
                            r'doanh nghiệp|doanh nghiep|công ty|cong ty)\b)', ' và ', question,
                            flags=re.IGNORECASE)
    workplace_query = ' '.join(_requested_clauses(workplace_list))
    for workplace_object in WORKPLACE_OBJECT.finditer(WORKPLACE_REFUSAL.sub(' ', workplace_query)):
        workplaces.update(re.findall(r'\b' + WORKPLACE_PATTERN + r'\b', workplace_object[0]))
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
    grouped = list(groups.values())
    purpose = (PURPOSE_REQUEST.search(query) if training_purpose_requested(question)
               and grouped and grouped[0][0].chunk.dataset == 'f1'
               and grouped[0][0].chunk.metadata.get('field') == 'objectives' else None)
    if purpose:
        # Aim requests prefer focused purpose text over a larger outcomes chapter.
        # BM25 order still breaks ties. No source/edition/scope gets merged.
        specific -= set(_tokens(purpose[0]))
        grouped.sort(key=lambda group: _purpose_material(group)[1], reverse=True)
    inventory = None
    for group in grouped:
        former_name_ids = {h.chunk.chunk_id for h in group
                           if former_name and FORMER_NAME_SOURCE.search(' '.join(_tokens(_body(h.chunk))))}
        if former_name and not former_name_ids:
            continue
        if purpose:
            purpose_words, density = _purpose_material(group)
            if not density or not specific <= purpose_words:
                continue
        basis_ids = _learning_basis_ids(group) if learning_basis else set()
        if learning_basis and not basis_ids:
            continue
        condition_ids = {h.chunk.chunk_id for h in group
                         if condition_requested and CONDITION_SOURCE.search(' '.join(_tokens(_body(h.chunk))))}
        if condition_requested and not condition_ids:
            continue
        # Accent folding and generic request words must not turn "dinh luong"
        # plus "thu tu" into evidence for "luong tu". Keep each compound in
        # one body and render that supporting body within this same scope.
        bodies = {h.chunk.chunk_id: ' '.join(_tokens(_body(h.chunk))) for h in group}
        if any(not any(has(body, 'neu ' + condition, 'khi ' + condition, 'voi dieu kien ' + condition)
                       for body in bodies.values()) for condition in conditional_objects):
            continue
        if any(not any(has(body, phrase) for body in bodies.values()) for phrase in domain_phrases):
            continue
        domain_ids = {key for key, body in bodies.items() if has(body, *domain_phrases)}
        context_ids = former_name_ids | basis_ids | domain_ids | condition_ids
        if variant_enumeration:
            if any(not any(has(body, *VARIANT_BODY_PHRASES[v]) for body in bodies.values()) for v in variants):
                continue
            context_ids |= {key for key, body in bodies.items()
                            if any(has(body, *VARIANT_BODY_PHRASES[v]) for v in variants)}
        if group[0].chunk.dataset == 'f1' and group[0].chunk.metadata.get('field') == 'careers':
            bodies = {hit.chunk.chunk_id: " " + _workplace_body(_body(hit.chunk)) + " " for hit in group}
            if any(not any(f" {place} " in body for body in bodies.values()) for place in workplaces):
                continue
            context_ids |= {key for key, body in bodies.items() if any(f" {place} " in body for place in workplaces)}
        words = {hit.chunk.chunk_id: set(_tokens(_body(hit.chunk))) for hit in group}
        if not specific <= set().union(*words.values()):
            continue
        if whole_fields:
            if group[0].chunk.metadata.get('field') not in whole_fields or source_catalog is None:
                continue
            if inventory is None:
                inventory = tuple(source_catalog())
            # Count every eligible part of the physical source field. Different
            # review/origin parts cannot be silently omitted OR merged into it.
            identity = _chunk_scope(group[0].chunk, coverage_identity=True)
            required = {chunk.chunk_id for chunk in inventory
                        if _chunk_scope(chunk, coverage_identity=True) == identity}
            if not required or required != {hit.chunk.chunk_id for hit in group}:
                continue
        selected = [hit for hit in group if whole_fields or not specific or specific & words[hit.chunk.chunk_id]
                    or hit.chunk.chunk_id in context_ids]
        # Render continuations in physical source order, rather than BM25 order.
        return tuple(sorted(selected, key=lambda h: h.chunk.metadata.get('locator', {}).get('start_char', 0)))
    return ()
