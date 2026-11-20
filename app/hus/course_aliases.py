"""Scoped HUS course abbreviations, Roman numeral variants, and longest-first matcher."""

from __future__ import annotations

from collections.abc import Iterable

from app.hus.rag_loader import F2Course
from app.hus.retrieval import COURSE_CODE, _tokens

DEFAULT_MAJOR_ALIASES: dict[str, tuple[str, ...]] = {
    "mathematics": ("toan hoc", "toanhoc", "nganh toan", "mathematics"),
    "mathematics_informatics": ("toan tin", "toantin", "toan hoc va tin hoc", "mathematics informatics"),
    "computer_science": (
        "khoa hoc may tinh va thong tin",
        "khoa hoc may tinh",
        "may tinh va khoa hoc thong tin",
        "may tinh va thong tin",
        "khmttt",
        "khmtt",
        "khmt tt",
        "khmt",
        "computer science",
    ),
    "data_science": ("khoa hoc du lieu", "khdl", "data science"),
}

# Map normalized student abbreviations and Roman numeral / short variants to
# normalized course title phrases (`_tokens` joined by single spaces).
# Bare "ai" is deliberately excluded because in Vietnamese it means "who"
# ("ai dạy", "làm việc cho ai", "ai cấp bằng"); only explicit course-qualified
# phrases ("mon ai", "hoc phan ai", "nhap mon ai") or "ttnt" map to AI courses.
COURSE_ALIAS_MAP: dict[str, tuple[str, ...]] = {
    "gt1": ("giai tich 1",),
    "gt 1": ("giai tich 1",),
    "giai tich i": ("giai tich 1",),
    "gt2": ("giai tich 2",),
    "gt 2": ("giai tich 2",),
    "giai tich ii": ("giai tich 2",),
    "gt3": ("giai tich 3",),
    "gt 3": ("giai tich 3",),
    "giai tich iii": ("giai tich 3",),
    "dstt": (
        "dai so tuyen tinh",
        "dai so tuyen tinh 1",
        "dai so tuyen tinh 2",
        "dai so tuyen tinh 3",
    ),
    "d s t t": (
        "dai so tuyen tinh",
        "dai so tuyen tinh 1",
        "dai so tuyen tinh 2",
        "dai so tuyen tinh 3",
    ),
    "dstt1": ("dai so tuyen tinh 1",),
    "dstt 1": ("dai so tuyen tinh 1",),
    "dai so tuyen tinh i": ("dai so tuyen tinh 1",),
    "dstt2": ("dai so tuyen tinh 2",),
    "dstt 2": ("dai so tuyen tinh 2",),
    "dai so tuyen tinh ii": ("dai so tuyen tinh 2",),
    "dstt3": ("dai so tuyen tinh 3",),
    "dstt 3": ("dai so tuyen tinh 3",),
    "dai so tuyen tinh iii": ("dai so tuyen tinh 3",),
    "csdl": ("co so du lieu",),
    "ttnt": ("tri tue nhan tao", "nhap mon tri tue nhan tao"),
    "mon ai": ("tri tue nhan tao", "nhap mon tri tue nhan tao"),
    "hoc phan ai": ("tri tue nhan tao", "nhap mon tri tue nhan tao"),
    "nhap mon ai": ("tri tue nhan tao", "nhap mon tri tue nhan tao"),
    "tri tue nhan tao": ("tri tue nhan tao", "nhap mon tri tue nhan tao"),
    "ctdl": ("cau truc du lieu va giai thuat", "cau truc du lieu va thuat toan"),
    "ctdlgt": ("cau truc du lieu va giai thuat", "cau truc du lieu va thuat toan"),
    "ctdl gt": ("cau truc du lieu va giai thuat", "cau truc du lieu va thuat toan"),
    "ctdl va gt": ("cau truc du lieu va giai thuat", "cau truc du lieu va thuat toan"),
    "ctdl tt": ("cau truc du lieu va giai thuat", "cau truc du lieu va thuat toan"),
    "ctdl va tt": ("cau truc du lieu va giai thuat", "cau truc du lieu va thuat toan"),
    "cau truc du lieu va giai thuat": (
        "cau truc du lieu va giai thuat",
        "cau truc du lieu va thuat toan",
    ),
    "xstk": ("xac suat thong ke", "xac suat va thong ke"),
    "xs tk": ("xac suat thong ke", "xac suat va thong ke"),
    "xac suat va thong ke": ("xac suat thong ke", "xac suat va thong ke"),
    "mmt": ("mang may tinh",),
    "hdh": ("he dieu hanh", "nguyen li he dieu hanh", "nguyen ly he dieu hanh"),
    "he dieu hanh": ("he dieu hanh", "nguyen li he dieu hanh", "nguyen ly he dieu hanh"),
    "nguyen ly he dieu hanh": (
        "he dieu hanh",
        "nguyen li he dieu hanh",
        "nguyen ly he dieu hanh",
    ),
    "cnpm": ("cong nghe phan mem", "nhap mon cong nghe phan mem"),
    "nhap mon cnpm": ("cong nghe phan mem", "nhap mon cong nghe phan mem"),
    "nhap mon cong nghe phan mem": ("cong nghe phan mem", "nhap mon cong nghe phan mem"),
    "ktmt": ("kien truc may tinh",),
    "lthdt": ("lap trinh huong doi tuong",),
    "oop": ("lap trinh huong doi tuong",),
    "ltdt": ("ly thuyet do thi",),
    "gt so": ("giai tich so", "giai tich so 1", "giai tich so 2"),
    "gts": ("giai tich so", "giai tich so 1", "giai tich so 2"),
    "gts1": ("giai tich so 1",),
    "gts 1": ("giai tich so 1",),
    "gt so 1": ("giai tich so 1",),
    "giai tich so i": ("giai tich so 1",),
    "gts2": ("giai tich so 2",),
    "gts 2": ("giai tich so 2",),
    "gt so 2": ("giai tich so 2",),
    "giai tich so ii": ("giai tich so 2",),
    "attt": ("an toan thong tin", "an toan va bao mat thong tin"),
    "kpdll": ("khai pha du lieu", "nhap mon khai pha cac tap du lieu lon"),
    "kpdl": ("khai pha du lieu", "nhap mon khai pha cac tap du lieu lon"),
    "xlha": ("xu ly anh", "xu ly hinh anh"),
    "xlnn": (
        "xu ly ngon ngu tu nhien",
        "xu li ngon ngu tu nhien",
        "xu li ngon ngu tu nhien va ung dung",
        "xu li ngon ngu tu nhien va hoc sau",
    ),
    "xlnntn": (
        "xu ly ngon ngu tu nhien",
        "xu li ngon ngu tu nhien",
        "xu li ngon ngu tu nhien va ung dung",
        "xu li ngon ngu tu nhien va hoc sau",
    ),
    "nlp": (
        "xu ly ngon ngu tu nhien",
        "xu li ngon ngu tu nhien",
        "xu li ngon ngu tu nhien va ung dung",
        "xu li ngon ngu tu nhien va hoc sau",
    ),
    "xu ly ngon ngu tu nhien": (
        "xu ly ngon ngu tu nhien",
        "xu li ngon ngu tu nhien",
        "xu li ngon ngu tu nhien va ung dung",
        "xu li ngon ngu tu nhien va hoc sau",
    ),
    "xu li ngon ngu tu nhien": (
        "xu ly ngon ngu tu nhien",
        "xu li ngon ngu tu nhien",
        "xu li ngon ngu tu nhien va ung dung",
        "xu li ngon ngu tu nhien va hoc sau",
    ),
    "xu ly ngon ngu tu nhien va ung dung": ("xu li ngon ngu tu nhien va ung dung",),
    "xu ly ngon ngu tu nhien va hoc sau": ("xu li ngon ngu tu nhien va hoc sau",),
    "trr": ("toan roi rac",),
    "ptvp": ("phuong trinh vi phan",),
    "ptdhr": (
        "phuong trinh dao ham rieng",
        "phuong trinh dao ham rieng 1",
        "phuong trinh dao ham rieng 2",
    ),
    "ptdhr1": ("phuong trinh dao ham rieng 1",),
    "ptdhr 1": ("phuong trinh dao ham rieng 1",),
    "phuong trinh dao ham rieng i": ("phuong trinh dao ham rieng 1",),
    "ptdhr2": ("phuong trinh dao ham rieng 2",),
    "ptdhr 2": ("phuong trinh dao ham rieng 2",),
    "phuong trinh dao ham rieng ii": ("phuong trinh dao ham rieng 2",),
    "tkdgtt": ("thiet ke va danh gia thuat toan",),
    "tk va dgtt": ("thiet ke va danh gia thuat toan",),
    "ltcb": ("lap trinh co ban",),
    "thcs": ("tin hoc co so",),
    "kltn": ("khoa luan tot nghiep",),
    "tgmt": ("thi giac may tinh",),
    "tuh": ("toi uu hoa",),
    "ttss": ("tinh toan song song",),
    "ppnckh": ("phuong phap nghien cuu khoa hoc",),
    "atmt": ("nhap mon an toan may tinh",),
    "mmatdl": ("mat ma va an toan du lieu",),
    "mm va atdl": ("mat ma va an toan du lieu",),
    "xs1": ("xac suat 1",),
    "xs 1": ("xac suat 1",),
    "xac suat i": ("xac suat 1",),
    "xs2": ("xac suat 2",),
    "xs 2": ("xac suat 2",),
    "xac suat ii": ("xac suat 2",),
    "cac mo hinh toan ung dung i": ("cac mo hinh toan ung dung 1",),
    "cac mo hinh toan ung dung ii": ("cac mo hinh toan ung dung 2",),
    "ly thuyet tro choi": ("li thuyet tro choi",),
    "ky thuat lay mau khao sat": ("ki thuat lay mau khao sat",),
    "he thong thong tin dia ly": ("he thong thong tin dia li",),
    "nguyen ly cac ngon ngu lap trinh": ("nguyen li cac ngon ngu lap trinh",),
}


def _match_scoped_phrases(
    question: str,
    scoped_courses: tuple[F2Course, ...],
    *,
    major_aliases: dict[str, tuple[str, ...]] | None = None,
    field_terms: dict[str, tuple[str, ...]] | None = None,
) -> tuple[set[str], set[str], set[str]]:
    """Consume longest phrases first and return (matched_codes, alias_tokens_used, name_matched_codes)."""
    from app.hus.question_routing import COURSE_FIELD_TERMS, requested_text

    active_major_aliases = DEFAULT_MAJOR_ALIASES if major_aliases is None else major_aliases
    active_field_terms = COURSE_FIELD_TERMS if field_terms is None else field_terms

    remaining = f" {requested_text(question)} "
    by_name: dict[str, set[str]] = {}
    for course in scoped_courses:
        phrase = " ".join(_tokens(course.course["course_name"]))
        if phrase:
            by_name.setdefault(phrase, set()).add(course.course_code)

    by_alias: dict[str, set[str]] = {}
    for raw_alias, target_phrases in COURSE_ALIAS_MAP.items():
        alias = " ".join(_tokens(raw_alias))
        if not alias:
            continue
        codes: set[str] = set()
        for target in target_phrases:
            norm_target = " ".join(_tokens(target))
            if norm_target in by_name:
                codes.update(by_name[norm_target])
        if codes:
            by_alias.setdefault(alias, set()).update(codes)

    by_phrase: dict[str, set[str]] = {}
    for phrase, codes in by_name.items():
        by_phrase.setdefault(phrase, set()).update(codes)
    for alias, codes in by_alias.items():
        by_phrase.setdefault(alias, set()).update(codes)
    for names in active_major_aliases.values():
        for alias in names:
            norm_alias = " ".join(_tokens(alias))
            if norm_alias:
                by_phrase.setdefault(norm_alias, set())
    for terms in active_field_terms.values():
        for term in terms:
            norm_term = " ".join(_tokens(term))
            if norm_term:
                by_phrase.setdefault(norm_term, set())

    matched_codes: set[str] = set()
    alias_tokens_used: set[str] = set()
    name_matched_codes: set[str] = set()

    for phrase in sorted(by_phrase, key=lambda item: (len(item), item), reverse=True):
        if f" {phrase} " in remaining:
            codes = by_phrase[phrase]
            if codes:
                matched_codes.update(codes)
                if phrase in by_name:
                    name_matched_codes.update(by_name[phrase])
                if phrase in by_alias and phrase not in by_name:
                    alias_tokens_used.update(_tokens(phrase))
            remaining = remaining.replace(f" {phrase} ", " ")

    return matched_codes, alias_tokens_used, name_matched_codes


def match_scoped_courses(
    question: str,
    courses: Iterable[F2Course],
    *,
    major_aliases: dict[str, tuple[str, ...]] | None = None,
    field_terms: dict[str, tuple[str, ...]] | None = None,
) -> tuple[set[str], set[str]]:
    """Match exact course names and scoped abbreviations longest-first.

    Returns `(matched_codes, alias_tokens_used)` where `matched_codes` contains
    only courses present in `courses` and `alias_tokens_used` contains the
    normalized tokens of matched aliases.
    """
    scoped_courses = tuple(courses)
    if not scoped_courses:
        return set(), set()
    matched_codes, alias_tokens_used, _ = _match_scoped_phrases(
        question,
        scoped_courses,
        major_aliases=major_aliases,
        field_terms=field_terms,
    )
    return matched_codes, alias_tokens_used


def resolve_course_details(
    question: str,
    courses: Iterable[F2Course],
    **kwargs,
) -> list[dict[str, str]]:
    """Return sorted details (`course_code`, `course_name`, `match_type`) for matched courses in `courses`."""
    from app.hus.question_routing import requested_text

    scoped_courses = tuple(courses)
    if not scoped_courses:
        return []
    course_by_code = {course.course_code: course for course in scoped_courses}
    text = requested_text(question)
    explicit_codes = {
        token.upper()
        for token in _tokens(text)
        if COURSE_CODE.fullmatch(token) and token.upper() in course_by_code
    }
    matched_codes, _, name_matched_codes = _match_scoped_phrases(
        question,
        scoped_courses,
        major_aliases=kwargs.get("major_aliases"),
        field_terms=kwargs.get("field_terms"),
    )
    all_codes = sorted(explicit_codes | matched_codes)
    details: list[dict[str, str]] = []
    for code in all_codes:
        if code in explicit_codes:
            match_type = "code"
        elif code in name_matched_codes:
            match_type = "name"
        else:
            match_type = "alias"
        details.append(
            {
                "course_code": code,
                "course_name": course_by_code[code].course["course_name"],
                "match_type": match_type,
            }
        )
    return details
