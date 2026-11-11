"""Small lexical intent rules over requested clauses, independent of evaluation data."""

from __future__ import annotations

import re

from app.hus.retrieval import COURSE_CODE, _tokens


def has(text: str, *phrases: str) -> bool:
    return any(f" {phrase} " in f" {text} " for phrase in phrases)


CAREER_EXCLUSION = re.compile(
    r'^(?:(?:minh|toi|ban) )?(?:khong (?:can|hoi|lay|trich|yeu cau|nhac)|'
    r'dung (?:trich|ke|nhac)) (?:(?:ve|phan|noi dung) )?'
    r'(?:giang day|day hoc|giang vien|giao vien)\b'
    r'(?: (?:trong|tai|o) (?:cac )?(?P<workplace>doanh nghiep|cong ty|truong(?: dai hoc)?))?')
TEACHING_TERMS = ('giang day', 'day hoc', 'giang vien', 'giao vien')


def _clause_texts(question: str) -> tuple[str, ...]:
    """Keep one common boundary/normalization policy for requests and exclusions."""
    # Bare 'nhung' is ambiguous without accents. Preserve the bounded content
    # phrase 'học những'; other adversative 'nhung' still separates clauses.
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


RECOMMENDATION = ("nen hoc", "nen dang ky", "goi y mon", "de xuat mon", "chon mon",
                  "du dieu kien dang ky", "du dieu kien tot nghiep", "co du dieu kien hoc",
                  "lo trinh", "ky toi nen", "ky toi hoc", "nen uu tien",
                  "xep hang", "chon cho", "chon ho", "to hop mon", "xep lich")
EXTERNAL_ACTIONS = ("dang nhap", "gui thu", "email", "thoi tiet", "mua dien thoai",
                    "ngan hang chuyen tien", "chuyen tien", "tai khoan ca nhan")
UNSUPPORTED = ("hoc phi", "diem chuan", "chi tieu", "tuyen sinh", "luong", "lich hoc", "hoc bong",
               "giang vien", "thoi khoa bieu", "quy che", "dang mo", "dang duoc mo",
               "mo lop", "cho trong", "han dang ky", "hien tai", "hien nay", "nam nay")


def out_of_scope(question: str) -> bool:
    return has(requested_text(question), *RECOMMENDATION, *EXTERNAL_ACTIONS)


def unsupported_request(question: str) -> bool:
    # Accent folding makes 'lương' == 'lượng'; a credit workload isn't salary.
    text = requested_text(question).replace("khoi luong", "khoi")
    return has(text, *UNSUPPORTED) or bool(re.search(r"\b20(?:2[6-9]|[3-9]\d)\b", text))


def verified_requested(question: str) -> bool:
    text = requested_text(question)
    return ("%" in question and has(text, "thi", "diem", "danh gia")) or has(
        text, "chinh thuc", "da xac minh", "hien hanh", "hien nay", "hien tai", "nam nay",
        "ty le", "ti le", "phan tram", "cuoi ky", "trong so", "ty trong", "ti trong")


def assessment_fact_request(question: str) -> bool:
    text = requested_text(question)
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


COURSE_FIELD_TERMS = {
    "credits": ("tin chi",),
    "prerequisites": ("tien quyet", "hoc truoc", "truoc mon"),
    "hours": ("so tiet", "so gio"),
    "name": ("ten mon", "ten hoc phan", "ten day du", "mang ten", "la mon gi",
             "ten cua ma", "ten cua mon", "ten cua hoc phan", "co ten gi"),
    "content": ("noi dung", "chu de", "hoc gi", "hoc ve", "phan se hoc", "de cuong", "hoc nhung"),
    "objectives": ("muc tieu", "chuan dau ra", "nang luc", "huong toi", "dao tao de", "dao tao nham", "muc dich dao tao"),
    "suggested_assessment": ("danh gia", "thi", "kiem tra"),
}


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
            if (has(_prerequisite_text((part,)), *COURSE_FIELD_TERMS["prerequisites"])
                    or has(part, "can hoc", "phai hoc")):
                part = re.sub(r"\bhoc (?:gi|nhung)\b", "hoc", part)
            content_parts.append(part)
    fields = []
    for field, terms in COURSE_FIELD_TERMS.items():
        active = _prerequisite_text(clauses) if field == "prerequisites" else text
        if field == "content":
            active = " ".join(content_parts)
        if has(active, *terms):
            fields.append(field)
    return tuple(fields)


PROGRAM_FIELDS = {"program_credits", "program_groups", "group_rules"}
CAREER_TERMS = ("nghe nghiep", "viec lam", "lam nghe", "sau tot nghiep", "ra truong",
                "lam o dau", "noi lam viec", "cong viec", "vi tri", "nghien cuu phat trien")


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
    return has(text, "chuong trinh", "ctdt", "toan khoa") and has(text, "tong tin chi", "tong cong")


def requested_program_fields(question: str) -> tuple[str, ...]:
    fields = []
    text = requested_text(question)
    course_context = has(text, "mon", "hoc phan") or any(COURSE_CODE.fullmatch(t) for t in _tokens(text))
    parts = [part for clause in _requested_clauses(question) for part in re.split(r"\bva\b", clause)]
    program_credit = any(
        has(part, "tin chi") and has(part, "chuong trinh", "ctdt", "toan khoa", "nganh")
        and not has(part.replace("ma mon", ""), "mon", "hoc phan", "nhom", "khoi kien thuc")
        and not any(COURSE_CODE.fullmatch(token) for token in _tokens(part))
        and (not course_context or part.startswith(("chuong trinh", "ctdt", "toan khoa"))
             or has(part, "tong tin chi", "tong cong", "tin chi chuong trinh", "tin chi cua chuong trinh", "tin chi ctdt"))
        for part in parts)
    if program_credit:
        fields.append("program_credits")
    group_parts = " ".join(part for part in parts if has(part, "nhom", "khoi kien thuc"))
    group = bool(group_parts) and (bool(question_group_keys(question)) or has(
        group_parts, "nhom kien thuc", "khoi kien thuc", "chuong trinh", "ctdt", "tin chi", "ghi chu"))
    if has(group_parts, *CAREER_TERMS) and not (question_group_keys(question) or has(
            group_parts, "nhom kien thuc", "khoi kien thuc", "tin chi")):
        group = False
    if group:
        if question_group_keys(question) or has(group_parts, "ghi chu", "yeu cau", "tin chi"):
            fields.append("group_rules")
        elif has(group_parts, "chuong trinh", "ctdt", "nhom kien thuc", "cac nhom", "danh sach nhom", "khoi kien thuc"):
            fields.append("program_groups")
    return tuple(fields)


def question_intent(question: str) -> tuple[str | None, str | None]:
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
    if has(text, *COURSE_FIELD_TERMS["credits"]):
        return "f2", "credits"
    if has(_prerequisite_text(clauses), *COURSE_FIELD_TERMS["prerequisites"]):
        return "f2", "prerequisites"
    if has(text, *COURSE_FIELD_TERMS["hours"]):
        return "f2", "hours"
    if has(text, *COURSE_FIELD_TERMS["name"]):
        return "f2", "name"
    if has(text, "hoc tiep", "sau dai hoc", "hoc len", "cao hoc", "nghien cuu sinh", "hoc cao hon"):
        return "f1", "further_study"
    corporate_subject = (bool(re.search(r'\bvai tro (?:nao |gi )?cua (?:cac )?(?:doanh nghiep|cong ty)\b', text))
                         or bool(re.match(r'^(?:(?:cac|nhung|mot) )?(?:doanh nghiep|cong ty)\b', text)))
    role_at_work = (bool(re.search(r'\bvai tro (?:nao|gi)\b', text))
                   and has(text, 'doanh nghiep', 'cong ty') and not corporate_subject
                   and not has(text, *COURSE_FIELD_TERMS['objectives'], *COURSE_FIELD_TERMS['content'],
                               'gioi thieu', 'tong quan', 'mon', 'hoc phan', 'chuong trinh', 'ctdt', 'nhom', 'dao tao'))
    if not course and (has(text, *CAREER_TERMS) or role_at_work):
        return "f1", "careers"
    if has(text, *COURSE_FIELD_TERMS["suggested_assessment"]):
        return "f3", "suggested_assessment"
    if has(text, *COURSE_FIELD_TERMS["objectives"]):
        return ("f3", "objectives") if course else ("f1", "objectives")
    if has(text, *COURSE_FIELD_TERMS["content"]):
        return "f3", "content"
    if not course and has(text, "gioi thieu", "tong quan", "nganh", "chuong trinh", "nen tang", "lich su hinh thanh"):
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
