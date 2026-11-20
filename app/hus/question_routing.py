"""Small lexical intent rules over requested clauses, independent of evaluation data."""

from __future__ import annotations

import re
import unicodedata

from app.hus.retrieval import COURSE_CODE, _tokens


def has(text: str, *phrases: str) -> bool:
    return any(f" {phrase} " in f" {text} " for phrase in phrases)


CAREER_EXCLUSION = re.compile(
    r'^(?:(?:minh|toi|ban) )?(?:khong (?:can|hoi|lay|trich|yeu cau|nhac)|'
    r'dung (?:trich|ke|nhac)) (?:(?:ve|phan|noi dung) )?'
    r'(?:giang day|day hoc|giang vien|giao vien)\b'
    r'(?: (?:trong|tai|o) (?:cac )?(?P<workplace>doanh nghiep|cong ty|truong(?: dai hoc)?))?')
TEACHING_TERMS = ('giang day', 'day hoc', 'giang vien', 'giao vien')
NAME_LANGUAGE_TERMS = ('ten tieng viet', 'ten bang tieng viet', 'ten day du bang tieng viet',
                       'ten tieng anh', 'ten bang tieng anh', 'ten day du bang tieng anh')

# A broad course introduction is F3 content. Explicit fields retain priority;
# consume only request grammar, leaving the course name/code and qualifiers.
COURSE_OVERVIEW = re.compile(
    r'^(?:(?:toi|minh|em) (?:muon|can) )?'
    r'(?:(?:ban|hay|xin|nho|vui long) )*'
    r'(?:tim hieu|gioi thieu|tong quan)(?: ve)? '
    r'(?=(?:mon(?: hoc)?|hoc phan)\b|[a-z]{3}\d{4}[a-z]?\b)')


def _clause_texts(question: str) -> tuple[str, ...]:
    """Keep one common boundary/normalization policy for requests and exclusions."""
    # Bare 'nhung' is ambiguous without accents. Preserve the bounded content
    # phrase 'học những'; other adversative 'nhung' still separates clauses.
    # Resolve the *accented* grammatical particle before accent folding. Never
    # remove bare `thi`: that may be an actual examination, also without accents.
    # The caller's original question and all conditional/negative objects remain.
    question = unicodedata.normalize('NFC', question)
    question = re.sub(r'\bthì\b', ' ', question, flags=re.IGNORECASE)
    question = re.sub(r"\b((?:học|hoc)\s+)nhung\b", r"\1những", question, flags=re.IGNORECASE)
    parts = re.split(r"[,;:.!?]|\b(?:nhưng|nhung)\b|\b(?:và|va)\s+(?=không|khong|đừng|dung)",
                     question, flags=re.IGNORECASE)
    return tuple(' '.join(_tokens(part)) for part in parts)


def career_exclusions(question: str) -> tuple[str | None, ...]:
    """Teaching exclusions retain workplace scope; None means topic-wide."""
    return tuple(match['workplace'] for part in _clause_texts(question)
                 if (match := CAREER_EXCLUSION.match(part)))


def _requested_clauses(question: str) -> tuple[str, ...]:
    """Ignore explicit refused objects, retaining subsequent affirmative claims."""
    # Consume a bounded refused object, not the remainder of its sentence. An
    # affirmative request after it must still reach every safety/intent rule.
    field_objects = {term for terms in COURSE_FIELD_TERMS.values() for term in terms}
    field_objects.update({"so tin chi", "dieu kien tien quyet", "goi y danh gia"})
    field_objects.update(NAME_LANGUAGE_TERMS)
    field_pattern = "|".join(re.escape(term) for term in sorted(field_objects, key=lambda t: (-len(t), t)))
    refused = re.compile(
        r"^(?:(?:minh|toi|ban) )?(?:"
        r"khong ket luan du dieu kien dang ky|khong du doan thu nhap|"
        r"(?:khong (?:can|hoi|yeu cau|nho|lay|coi)|dung coi) "
        r"(?:la )?(?:goi do la )?(?:"
        r"(?:de cuong|chuan dau ra) chinh thuc|(?:muc |du bao )?luong(?: hay xep hang)?|"
        r"tu van chon mon|khuyen minh chon nganh|lap (?:lo trinh hoc|ke hoach hoc)|"
        r"cong ty dang tuyen|noi dung mon|goi y ai|lich hoc|" + field_pattern + r"))\b")
    active = []
    for text in _clause_texts(question):
        text = CAREER_EXCLUSION.sub('', text, count=1).strip()
        text = refused.sub("", text, count=1).strip()
        if text:
            active.append(text)
    return tuple(active)


def requested_text(question: str) -> str:
    """Normalized requested clauses for keyword, scope and evidence checks."""
    return " ".join(_requested_clauses(question))


PROGRAM_VARIANT_PATTERNS = {
    'high_quality': re.compile(r'\b(?:(?:(?:he|chuong trinh(?: dao tao)?|ctdt) )?clc|'
                               r'(?:he|chuong trinh(?: dao tao)?|ctdt) chat luong cao)\b'),
    'standard': re.compile(r'\b(?:he|chuong trinh) chuan\b'),
    'talent': re.compile(r'\b(?:he|chuong trinh) tai nang\b'),
    'advanced': re.compile(r'\b(?:he|chuong trinh) tien tien\b'),
}


def program_variant_scope(text: str) -> tuple[str, set[str]]:
    """Consume bounded scope phrases, never globally ignore their component words."""
    variants = set()
    for variant, pattern in PROGRAM_VARIANT_PATTERNS.items():
        if pattern.search(text):
            variants.add(variant)
            text = pattern.sub(' ', text)
    return text, variants


def requested_program_variants(question: str) -> set[str]:
    return {variant for clause in _requested_clauses(question)
            for variant in program_variant_scope(clause)[1]}


VARIANT_ENUMERATION = re.compile(
    r'(?<!khong )(?<!chua )\b(?:co|gom|dao tao) (?:nhung |cac |hai |\d+ )?'
    r'(?:chuong trinh(?: dao tao)? )?(?:cu nhan )?'
    r'(?:he|chuong trinh) (?:chuan|tai nang|chat luong cao|tien tien|clc)\b'
    r'(?: (?:va|voi|cung) (?:cu nhan )?(?:he|chuong trinh) '
    r'(?:chuan|tai nang|chat luong cao|tien tien|clc)\b)+'
    r'(?: (?:nhu the nao|ra sao|the nao|gi|nao))?$'
)


def variant_enumeration_requested(question: str) -> bool:
    clauses = _requested_clauses(question)
    text = ' '.join(clauses)
    if (len(requested_program_variants(question)) < 2
            or has(text, 'so sanh', 'doi chieu', 'khac nhau', 'khac gi',
                   'khac biet', 'phan biet', 'giong nhau', 'khong', 'chua')):
        return False
    return any(VARIANT_ENUMERATION.search(clause) for clause in clauses)


RECOMMENDATION = ("nen hoc", "nen dang ky", "goi y mon", "de xuat mon", "chon mon",
                  "du dieu kien dang ky", "du dieu kien tot nghiep", "co du dieu kien hoc",
                  "lo trinh", "ky toi nen", "ky toi hoc", "nen uu tien",
                  "xep hang", "chon cho", "chon ho", "to hop mon", "xep lich")
EXTERNAL_ACTIONS = ("dang nhap", "gui thu", "email", "thoi tiet", "mua dien thoai",
                    "ngan hang chuyen tien", "chuyen tien", "tai khoan ca nhan")
UNSUPPORTED = ("hoc phi", "diem chuan", "chi tieu", "tuyen sinh", "luong", "lich hoc", "hoc bong",
               "giang vien", "thoi khoa bieu", "quy che", "dang mo", "dang duoc mo",
               "mo lop", "cho trong", "han dang ky", "hien tai", "hien nay", "nam nay")
ASSESSMENT_COMPOUNDS = ('do thi', 'thi giac', 'thi truong', 'thi nghiem', 'hien thi')
VALUE_COMPOUNDS = ('khoi luong', 'uoc luong', 'dinh luong', 'chat luong', 'nang luong',
                   'luong tu', 'luong giac', 'ham luong', 'dai luong')


def _without_compounds(text: str, compounds: tuple[str, ...]) -> str:
    return re.sub(r'\b(?:' + '|'.join(map(re.escape, compounds)) + r')\b', ' ', text)


NEGATED_OUT_OF_SCOPE = (
    "chua can ket luan du dieu kien",
    "chua can du dieu kien",
    "khong can ket luan du dieu kien",
    "khong can du dieu kien",
    "thay vi xep hang",
    "khong can xep hang",
    "khong xep hang",
    "chua can xep hang",
    "thay vi chon",
    "khong can chon",
    "chua can chon",
)


def out_of_scope(question: str) -> bool:
    text = requested_text(question)
    for phrase in NEGATED_OUT_OF_SCOPE:
        text = text.replace(phrase, " ")
    return has(text, *RECOMMENDATION, *EXTERNAL_ACTIONS)



def unsupported_request(question: str) -> bool:
    # Accent folding merges salary with scientific compounds. Consume only the
    # complete compound: a later separate salary/admission request stays active.
    text = _without_compounds(requested_text(question), VALUE_COMPOUNDS)
    text = re.sub(r'\b(?:bat dau tuyen sinh|tuyen sinh (?:lan dau|dau tien))\b', 'bat dau', text)
    return has(text, *UNSUPPORTED) or bool(re.search(r"\b20(?:2[6-9]|[3-9]\d)\b", text))


def _assessment_text(text: str) -> str:
    """Domain compounds containing folded 'thi' are not examination requests."""
    # Pilot training/programmes are not exams or grades. Require a bounded
    # pilot context so an actual "bai thi diem ..." remains an assessment.
    text = re.sub(r'\b(?:dao tao|chuong trinh|trien khai|de an|du an|mo) thi diem\b', ' ', text)
    return _without_compounds(text, ASSESSMENT_COMPOUNDS)


def verified_requested(question: str) -> bool:
    text = requested_text(question)
    return ("%" in question and has(_assessment_text(text), "thi", "diem", "danh gia")) or has(
        text, "chinh thuc", "da xac minh", "hien hanh", "hien nay", "hien tai", "nam nay",
        "ty le", "ti le", "phan tram", "cuoi ky", "trong so", "ty trong", "ti trong")


def assessment_fact_request(question: str) -> bool:
    text = _assessment_text(requested_text(question))
    assessment = has(text, "thi", "diem", "danh gia", "cuoi ky", "giua ky", "trac nghiem", "tu luan")
    return assessment and ("%" in question or has(
        text, "phan tram", "ty le", "ti le", "trong so", "ty trong", "ti trong", "chiem",
        "hinh thuc thi", "trac nghiem", "tu luan"))


def _prerequisite_text(clauses: tuple[str, ...]) -> str:
    text = " ".join(clauses)
    # Suppress a preview phrase only for an explicit content/objective request.
    # Required earlier study takes priority even when another clause previews it.
    preview_requested = has(text, "noi dung", "chu de", "hoc gi", "hoc ve", "phan se hoc",
                            "muc tieu", "chuan dau ra", "de cuong", "danh gia", "kiem tra")
    required_study = has(text, "can hoc", "phai hoc", "can hoan thanh", "phai hoan thanh")
    prerequisite_text = text
    if preview_requested and not required_study:
        prerequisite_text = " ".join(
            re.sub(r"\b(?:hinh dung|tim hieu|xem) truoc mon\b", "mon", clause)
            for clause in clauses
        )
    return prerequisite_text


def _prerequisites_requested(clauses: tuple[str, ...]) -> bool:
    text = _prerequisite_text(clauses)
    return (has(text, *COURSE_FIELD_TERMS['prerequisites'])
            or bool(re.search(r'\b(?:can|phai) (?:hoan thanh|hoc)\b.{0,240}\btruoc\b', text))
            or bool(re.search(r'\btruoc khi hoc\b.{0,240}\b(?:can|phai) hoc\b', text)))


CONCEPT_REQUEST = re.compile(
    r'\bkhai niem (?:gi|nao)\b|'
    r'^(?:(?:toi|minh|em) (?:muon|can) )?(?:(?:ban|hay|xin|nho|vui long) )*'
    r'(?:giai thich|tim hieu)(?: ve)? (?:cac |nhung )?khai niem\b')


def concept_requested(question: str) -> bool:
    return any(CONCEPT_REQUEST.search(clause) for clause in _requested_clauses(question))


def ambiguous_major_request(question: str) -> bool:
    text = requested_text(question)
    if (not has(text, 'nganh') or any(COURSE_CODE.fullmatch(t) for t in _tokens(text))
            or has(text, *CAREER_TERMS, *FURTHER_STUDY_TERMS, 'muc tieu', 'muc dich', 'chuan dau ra')):
        return False
    return (has(text, 'dinh huong nao', 'dinh huong gi')
            or bool(re.search(r'\bnganh\b.{0,160}\bhoc (?:nhung |cac )?(?:linh vuc|mon) (?:gi|nao)\b', text)))


CREDIT_TERMS = (
    "tin chi", "so tin", "bao nhieu tin", "may tin", "tong tin",
    "so tc", "bao nhieu tc", "may tc", "tong tc", "khoi luong tin chi",
    "hoc may tin", "hoc may tc", "hoc bao nhieu tin", "hoc bao nhieu tc",
)
TOTAL_CREDIT_TERMS = (
    "tong tin chi", "tong so tin chi", "tong tin", "tong so tin",
    "tong tc", "tong so tc", "tong cong",
)
PROGRAM_CREDIT_PHRASES = (
    "tin chi chuong trinh", "tin chi cua chuong trinh", "tin chi ctdt",
    "so tin chuong trinh", "so tin cua chuong trinh", "so tin ctdt",
    "so tc chuong trinh", "so tc cua chuong trinh", "so tc ctdt",
)


COURSE_FIELD_TERMS = {
    "credits": ("tin chi",),
    "prerequisites": (
        "tien quyet", "hoc truoc", "truoc mon",
        "dieu kien tien quyet", "yeu cau tien quyet",
        "mon tien quyet", "hoc phan tien quyet",
        "hoc mon gi truoc", "hoc gi truoc", "can hoc gi truoc", "can hoc mon gi truoc",
        "phai hoc mon gi truoc", "mon nao truoc", "hoc mon nao truoc",
        "can hoc truoc", "phai hoc truoc",
    ),
    "hours": (
        "so tiet", "so gio", "bao nhieu tiet", "bao nhieu gio",
        "may tiet", "may gio", "so gio hoc", "so tiet hoc",
        "hoc may tiet", "hoc may gio", "hoc bao nhieu tiet", "hoc bao nhieu gio",
    ),
    "name": ("ten mon", "ten hoc phan", "ten day du", "mang ten", "la mon gi",
             "ten cua ma", "ten cua mon", "ten cua hoc phan", "co ten gi"),
    "content": (
        "noi dung", "chu de", "hoc gi", "hoc ve", "phan se hoc", "de cuong", "hoc nhung",
        "hoc nhu the nao", "hoc ra sao", "day nhu the nao", "day gi", "day nhung gi",
    ),
    "objectives": ("muc tieu", "muc dich", "chuan dau ra", "nang luc", "huong toi", "dao tao de", "dao tao nham", "muc dich dao tao"),
    "suggested_assessment": ("danh gia", "thi", "kiem tra"),
}


COURSE_OVERVIEW_TERMS = (
    "nhu the nao", "ra sao", "biet ve", "can biet", "tim hieu",
    "thong tin", "gioi thieu", "tong quan", "mo ta", "khai quat",
)


def course_overview_requested(text: str) -> bool:
    return (has(text, *COURSE_OVERVIEW_TERMS)
            and not has(text, "khong muon", "khong can", "khong hoi", "khong yeu cau"))


def _name_languages(text: str, *, assume_course: bool = False) -> set[str]:
    """A language-qualified name object, not a writing/naming skill topic."""
    course = any(COURSE_CODE.fullmatch(t) for t in _tokens(text)) or has(text, 'mon', 'hoc phan')
    if not course and not assume_course:
        return set()
    languages = set(re.findall(
        r'\bten (?:day du )?(?:bang )?tieng (viet|anh) '
        r'(?=(?:(?:cua|ung voi) )?(?:ma\b|hoc phan\b|mon\b|[a-z]{3}\d{4}[a-z]?\b)'
        r'|la gi\b|va (?:so )?tin chi\b)', text))
    if has(text, *COURSE_FIELD_TERMS['name']):
        languages.update(re.findall(r'\b(?:bang|trong) tieng (viet|anh)\b', text))
    return languages


def requested_name_languages(question: str) -> set[str]:
    # The caller already resolves the canonical course. Keep suffix modifiers
    # attached to their active clause, including when the code is an API hint.
    return {language for clause in _requested_clauses(question)
            for language in _name_languages(clause, assume_course=True)}


def _course_name_requested(text: str) -> bool:
    terms = tuple(t for t in COURSE_FIELD_TERMS['name'] if t not in {'mang ten', 'co ten gi'})
    course = any(COURSE_CODE.fullmatch(t) for t in _tokens(text)) or has(text, 'mon', 'hoc phan')
    return has(text, *terms) or bool(_name_languages(text)) or (course and has(text, 'mang ten', 'co ten gi'))


def _content_request_text(text: str) -> str:
    """Content OF an assessment suggestion is not a second syllabus request.

    Called per active clause/conjunction part so a separate affirmative content
    request, including one after a negation, is never consumed by this rule.
    """
    assessment = r'(?:goi y|de xuat) (?:danh gia|kiem tra)'
    text = re.sub(r'\bnoi dung (?=(?:cua )?(?:phan )?' + assessment + r'\b)', '', text)
    match = re.search(r'\b' + assessment + r'\b', text)
    if match:
        tail = re.sub(r'\b(?:co )?noi dung (?:gi|nhu the nao|ra sao)\b', ' ', text[match.end():])
        text = text[:match.end()] + tail
    return text


def requested_course_fields(question: str) -> tuple[str, ...]:
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
            if (_prerequisites_requested((part,))
                    or has(part, "can hoc", "phai hoc")):
                part = re.sub(r"\bhoc (?:gi|nhung)\b", "hoc", part)
            content_parts.append(_content_request_text(part))
    fields = []
    for field, terms in COURSE_FIELD_TERMS.items():
        active = _prerequisite_text(clauses) if field == "prerequisites" else text
        if field == "content":
            active = " ".join(content_parts)
        if field == 'suggested_assessment':
            active = _assessment_text(active)
        if field == 'name':
            if _course_name_requested(active):
                fields.append(field)
            continue
        if field == 'prerequisites':
            if _prerequisites_requested(clauses):
                fields.append(field)
            continue
        if field == 'content' and concept_requested(question):
            fields.append(field)
            continue
        if has(active, *terms):
            fields.append(field)
    return tuple(fields)


CATALOG_FIELDS = {"program_course_count", "program_course_list"}
PROGRAM_FIELDS = {"program_credits", "program_groups", "group_rules"} | CATALOG_FIELDS
CATALOG_OBJECT = r'(?:hoc phan|mon(?: hoc)?)'
CATALOG_REQUEST_SUFFIX = r'(?: giup (?:toi|minh|em))?'
SCOPED_CATALOG_COUNT = re.compile(
    r'(?:(?:hay|xin|vui long) )?dem (?:so )?' + CATALOG_OBJECT + CATALOG_REQUEST_SUFFIX)
SCOPED_CATALOG_LIST = re.compile(
    r'(?:(?:hay|xin|vui long) )?(?:cho (?:toi|minh|em) xem )?'
    r'(?:liet ke (?:(?:tat ca|toan bo) )?(?:cac )?|(?:toan bo )?danh sach )'
    + CATALOG_OBJECT + CATALOG_REQUEST_SUFFIX)
CAREER_TERMS = ("nghe nghiep", "viec lam", "lam nghe", "sau tot nghiep", "ra truong",
                "lam o dau", "lam viec", "noi lam viec", "cong viec", "vi tri", "nghien cuu phat trien")
FURTHER_STUDY_TERMS = ("hoc tiep", "sau dai hoc", "hoc len", "cao hoc", "nghien cuu sinh", "hoc cao hon")
FURTHER_STUDY_HEADINGS = ('kha nang hoc tap nang cao', 'kha nang hoc tap va nang cao',
                         'hoc tap nang cao sau tot nghiep', 'hoc tap nang cao sau khi tot nghiep')
WORKPLACE_PATTERN = r'(?:doanh nghiep|cong ty|truong(?: dai hoc)?|dai hoc|vien(?: nghien cuu)?)'
ROLE_WORKPLACE = re.compile(r'\b(?:tai|trong|o) (?:(?:cac|nhung|don vi) )*' + WORKPLACE_PATTERN + r'\b')


def _graduate_role_requested(clause: str) -> bool:
    """Roles at an institution concern graduates; roles of it do not."""
    clause = re.sub(r'^(?:theo )?(?:nguon|trang|tai lieu) gioi thieu\b', 'nguon', clause)
    actor = r'(?:(?:cac|nhung|mot) )?(?:nha truong|' + WORKPLACE_PATTERN + r')\b'
    role = r'(?:vai tro(?: cong tac)?|chuc danh|co hoi giang day)'
    institution_subject = (
        re.search(r'\b' + role + r' (?:(?:nao|gi) )?cua ' + actor, clause)
        or re.match('^' + actor, clause))
    role_at_work = bool(re.search(r'\bvai tro (?:cong tac )?(?:nao|gi)\b', clause))
    teaching = has(clause, 'co hoi giang day')
    person_title = has(clause, 'chuc danh')
    context = bool(ROLE_WORKPLACE.search(clause)) or has(clause, 'cu nhan', 'tot nghiep')
    return ((person_title or ((role_at_work or teaching) and context)) and not institution_subject
            and not has(clause, *COURSE_FIELD_TERMS['objectives'], *COURSE_FIELD_TERMS['content'],
                        'gioi thieu', 'tong quan', 'mon', 'hoc phan', 'chuong trinh', 'ctdt', 'nhom', 'dao tao'))


def question_group_keys(question: str) -> set[str]:
    """Explicit Roman group keys retain hierarchy punctuation, unlike tokens."""
    # Remove just an explicit refused group object, retaining dots and any
    # subsequent affirmative clause. Raw periods are hierarchy, not boundaries.
    question = re.sub(
        r"\b(?:không|khong)\s+(?:cần|can|hỏi|hoi|lấy|lay)\s+(?:nhóm|nhom)\s+"
        r"[ivx]+(?:\s*\.\s*\d+)*(?!\w|\.\d)", " ", question, flags=re.IGNORECASE)
    pattern = r"([ivx]+(?:\s*\.\s*\d+)*)(?!\w|\.\d)"
    keys = re.findall(r"\b(?:nhóm|nhom)\s+" + pattern, question, flags=re.IGNORECASE)
    if keys:
        keys += re.findall(r"(?:\b(?:và|va|hay|hoặc|hoac)\s+|,\s*)" + pattern,
                           question, flags=re.IGNORECASE)
    return {re.sub(r"\s", "", key).upper() for key in keys}


def program_total_request(question: str) -> bool:
    text = requested_text(question)
    return has(text, "chuong trinh", "ctdt", "toan khoa") and has(text, *TOTAL_CREDIT_TERMS)


def requested_program_fields(question: str) -> tuple[str, ...]:
    fields = []
    text = requested_text(question)
    # Short commands can use the selected curriculum. Match the original
    # wording in full so a filter or excluded clause cannot become a total.
    command = ' '.join(_tokens(question))
    catalog = has(text, 'mon', 'hoc phan') and has(text, 'nganh', 'chuong trinh', 'ctdt', 'danh muc')
    if SCOPED_CATALOG_COUNT.fullmatch(command) or (
            catalog and has(text, 'bao nhieu mon', 'bao nhieu hoc phan', 'so mon', 'so hoc phan',
                            'dem mon', 'dem so mon', 'dem hoc phan')):
        fields.append('program_course_count')
    if SCOPED_CATALOG_LIST.fullmatch(command) or (
            catalog and has(text, 'liet ke', 'danh sach mon', 'danh sach hoc phan', 'nhung mon nao', 'gom cac mon')):
        fields.append('program_course_list')
    course_context = has(text, "mon", "hoc phan") or any(COURSE_CODE.fullmatch(t) for t in _tokens(text))
    parts = [part for clause in _requested_clauses(question) for part in re.split(r"\bva\b", clause)]
    program_credit = any(
        has(part, *CREDIT_TERMS) and has(part, "chuong trinh", "ctdt", "toan khoa", "nganh")
        and not has(part.replace("ma mon", ""), "mon", "hoc phan", "nhom", "khoi kien thuc")
        and not any(COURSE_CODE.fullmatch(token) for token in _tokens(part))
        and (not course_context or part.startswith(("chuong trinh", "ctdt", "toan khoa"))
             or has(part, *TOTAL_CREDIT_TERMS, *PROGRAM_CREDIT_PHRASES))
        for part in parts)
    if program_credit:
        fields.append("program_credits")
    group_parts = " ".join(part for part in parts if has(part, "nhom", "khoi kien thuc"))
    group = bool(group_parts) and (bool(question_group_keys(question)) or has(
        group_parts, "nhom kien thuc", "khoi kien thuc", "chuong trinh", "ctdt", "ghi chu", *CREDIT_TERMS))
    if has(group_parts, *CAREER_TERMS) and not (question_group_keys(question) or has(
            group_parts, "nhom kien thuc", "khoi kien thuc", *CREDIT_TERMS)):
        group = False
    if group:
        if question_group_keys(question) or has(group_parts, "ghi chu", "yeu cau", *CREDIT_TERMS):
            fields.append("group_rules")
        elif has(group_parts, "chuong trinh", "ctdt", "nhom kien thuc", "cac nhom", "danh sach nhom", "khoi kien thuc"):
            fields.append("program_groups")
    return tuple(fields)


def question_intent(question: str) -> tuple[str | None, str | None]:
    clauses = _requested_clauses(question)
    text = " ".join(clauses)
    course = (any(COURSE_CODE.fullmatch(t) for t in _tokens(text))
              or has(_without_compounds(text, ('chuyen mon', 'bo mon', 'lien mon')), 'hoc phan', 'mon'))
    if assessment_fact_request(question):
        return "f3", "official_assessment"
    if out_of_scope(question):
        return None, None
    program_fields = requested_program_fields(question)
    if program_fields:
        return "f2", program_fields[0]
    if has(text, *COURSE_FIELD_TERMS["credits"]):
        return "f2", "credits"
    if _prerequisites_requested(clauses):
        return "f2", "prerequisites"
    if has(text, *COURSE_FIELD_TERMS["hours"]):
        return "f2", "hours"
    if _course_name_requested(text):
        return "f2", "name"
    if has(text, *FURTHER_STUDY_TERMS) or (not course and has(text, *FURTHER_STUDY_HEADINGS)):
        return "f1", "further_study"
    role_at_work = any(_graduate_role_requested(clause) for clause in clauses)
    if not course and has(text, 'muc tieu', 'muc dich', 'chuan dau ra', 'dao tao de', 'dao tao nham'):
        return 'f1', 'objectives'
    if not course and (has(text, *CAREER_TERMS) or role_at_work):
        return "f1", "careers"
    if has(_assessment_text(text), *COURSE_FIELD_TERMS["suggested_assessment"]):
        return "f3", "suggested_assessment"
    if ambiguous_major_request(question):
        return 'f1', None
    if has(text, *COURSE_FIELD_TERMS["objectives"]):
        return ("f3", "objectives") if course else ("f1", "objectives")
    if has(text, *COURSE_FIELD_TERMS["content"]) or (course and concept_requested(question)):
        if not course and has(text, 'chuong trinh', 'ctdt'):
            return 'f1', 'introduction'
        return "f3", "content"
    if any(COURSE_OVERVIEW.match(clause) for clause in clauses):
        return 'f3', 'content'
    if not course and has(text, "gioi thieu", "tong quan", "nganh", "chuong trinh", "nen tang", "lich su"):
        return "f1", "introduction"
    return None, None


def is_hus_question(question: str) -> bool:
    if assessment_fact_request(question):
        return True
    if out_of_scope(question):
        return False
    return (question_intent(question)[0] is not None
            or any(COURSE_CODE.fullmatch(t) for t in _tokens(question))
            or has(requested_text(question), "hus", "hoc phi", "diem chuan", "tuyen sinh", "quy che", "hoc bong"))
