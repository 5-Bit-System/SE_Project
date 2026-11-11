"""Unit tests for HUS course abbreviations and scoped longest-first course matching."""

from __future__ import annotations

import pytest

from app.hus.answering import MAJOR_NAMES
from app.hus.course_aliases import (
    COURSE_ALIAS_MAP,
    match_scoped_courses,
    resolve_course_details,
)
from app.hus.question_routing import COURSE_FIELD_TERMS
from app.hus.rag_loader import HUSRAGData

SCOPES = {
    "mathematics": "QD3565-2023",
    "mathematics_informatics": "QD3567-2023",
    "computer_science": "QD3568-2023",
    "data_science": "QD3569-2023",
}


@pytest.fixture(scope="module")
def rag_data() -> HUSRAGData:
    return HUSRAGData.load_current()


def _courses(rag_data: HUSRAGData, major: str):
    return rag_data.f2_courses(major=major, version=SCOPES[major])


def test_required_alias_keys_present_and_bare_ai_excluded():
    required_keys = {
        "gt1",
        "giai tich i",
        "gt2",
        "giai tich ii",
        "gt3",
        "giai tich iii",
        "dstt",
        "d s t t",
        "csdl",
        "ttnt",
        "mon ai",
        "hoc phan ai",
        "ctdl",
        "ctdlgt",
        "ctdl va gt",
        "xstk",
        "mmt",
        "hdh",
        "cnpm",
        "ktmt",
        "lthdt",
        "oop",
        "ltdt",
        "gt so",
        "gts",
        "attt",
        "kpdll",
        "kpdl",
        "xlha",
        "xlnn",
        "nlp",
    }
    assert required_keys.issubset(COURSE_ALIAS_MAP.keys())
    assert "ai" not in COURSE_ALIAS_MAP


@pytest.mark.parametrize(
    "question,major,expected_codes,expected_alias_tokens",
    [
        ("Môn GT1 có bao nhiêu tín chỉ?", "computer_science", {"MAT2501"}, {"gt1"}),
        ("Môn Giải tích I mấy tín?", "mathematics", {"MAT2302"}, {"giai", "tich", "i"}),
        ("Học phần GT2 có mấy tc?", "data_science", {"MAT2502"}, {"gt2"}),
        ("Giải tích II học trước môn nào?", "mathematics_informatics", {"MAT2303"}, {"giai", "tich", "ii"}),
        ("GT3 bao nhiêu tín chỉ?", "computer_science", {"MAT2503"}, {"gt3"}),
        ("Giải tích III ở ngành Toán học mấy tín?", "mathematics", {"MAT2304"}, {"giai", "tich", "iii"}),
    ],
)
def test_calculus_abbreviations_and_roman_numerals_across_majors(
    rag_data: HUSRAGData,
    question: str,
    major: str,
    expected_codes: set[str],
    expected_alias_tokens: set[str],
):
    codes, alias_tokens = match_scoped_courses(
        question,
        _courses(rag_data, major),
        major_aliases=MAJOR_NAMES,
        field_terms=COURSE_FIELD_TERMS,
    )
    assert codes == expected_codes
    assert alias_tokens == expected_alias_tokens


@pytest.mark.parametrize(
    "question,major,expected_codes",
    [
        ("Môn ĐSTT có bao nhiêu tín chỉ?", "computer_science", {"MAT2400"}),
        ("Môn d s t t mấy tín?", "data_science", {"MAT2400"}),
        ("Môn ĐSTT có mấy tín?", "mathematics_informatics", {"MAT2300", "MAT2301"}),
        ("Môn ĐSTT có mấy tín?", "mathematics", {"MAT2300", "MAT2301", "MAT3339"}),
        ("Môn ĐSTT 1 có bao nhiêu tín?", "mathematics", {"MAT2300"}),
        ("Đại số tuyến tính II mấy tín?", "mathematics_informatics", {"MAT2301"}),
    ],
)
def test_linear_algebra_aliases_respect_major_specific_course_splits(
    rag_data: HUSRAGData,
    question: str,
    major: str,
    expected_codes: set[str],
):
    codes, alias_tokens = match_scoped_courses(question, _courses(rag_data, major))
    assert codes == expected_codes
    assert alias_tokens


@pytest.mark.parametrize(
    "question,major,expected_codes,expected_tokens",
    [
        ("Môn CSDL có mấy tín chỉ?", "computer_science", {"MAT3507"}, {"csdl"}),
        ("Học phần CSDL học những gì?", "data_science", {"MAT3507"}, {"csdl"}),
        ("CSDL bao nhiêu tín?", "mathematics_informatics", {"MAT3507"}, {"csdl"}),
        ("Môn TTNT có bao nhiêu tín chỉ?", "computer_science", {"MAT1206E"}, {"ttnt"}),
        ("Cho hỏi môn AI học gì?", "data_science", {"MAT3508"}, {"mon", "ai"}),
        ("Học phần AI có mấy tín chỉ?", "mathematics_informatics", {"MAT3508"}, {"hoc", "phan", "ai"}),
        ("Môn CTDL&GT mấy tín?", "computer_science", {"MAT3514"}, {"ctdl", "gt"}),
        ("Môn CTDL và GT học gì?", "data_science", {"MAT3514"}, {"ctdl", "va", "gt"}),
        ("Học phần CTDLGT bao nhiêu tín chỉ?", "mathematics_informatics", {"MAT3514"}, {"ctdlgt"}),
        ("Môn XSTK mấy tín chỉ?", "computer_science", {"MAT2323"}, {"xstk"}),
        ("Môn XSTK bao nhiêu tc?", "data_science", {"MAT2323"}, {"xstk"}),
        ("Môn MMT có bao nhiêu tín chỉ?", "computer_science", {"MAT3506"}, {"mmt"}),
        ("Môn HĐH mấy tín chỉ?", "computer_science", {"MAT3550E"}, {"hdh"}),
        ("Môn LTHĐT có bao nhiêu tín chỉ?", "computer_science", {"MAT1202"}, {"lthdt"}),
        ("Học phần OOP mấy tín?", "data_science", {"MAT1202"}, {"oop"}),
        ("LTHĐT bao nhiêu tc?", "mathematics_informatics", {"MAT1202"}, {"lthdt"}),
        ("Môn CNPM có mấy tín chỉ?", "computer_science", {"MAT1207"}, {"cnpm"}),
        ("Môn KTMT bao nhiêu tín?", "computer_science", {"MAT3505"}, {"ktmt"}),
        ("Môn GTS có mấy tín chỉ?", "data_science", {"MAT2034"}, {"gts"}),
        ("Môn GT số bao nhiêu tín?", "mathematics_informatics", {"MAT2404"}, {"gt", "so"}),
        ("Môn KPDL có bao nhiêu tín chỉ?", "computer_science", {"MAT3534"}, {"kpdl"}),
        ("Môn KPDLL có mấy tín chỉ?", "mathematics_informatics", {"MAT3565"}, {"kpdll"}),
        ("Môn NLP có mấy tín chỉ?", "computer_science", {"MAT3561E"}, {"nlp"}),
        ("Môn XLNN bao nhiêu tín chỉ?", "data_science", {"MAT3399"}, {"xlnn"}),
    ],
)
def test_student_abbreviations_resolve_across_four_majors(
    rag_data: HUSRAGData,
    question: str,
    major: str,
    expected_codes: set[str],
    expected_tokens: set[str],
):
    codes, alias_tokens = match_scoped_courses(
        question,
        _courses(rag_data, major),
        major_aliases=MAJOR_NAMES,
        field_terms=COURSE_FIELD_TERMS,
    )
    assert codes == expected_codes
    assert alias_tokens == expected_tokens


@pytest.mark.parametrize(
    "question",
    [
        "Sinh viên tốt nghiệp làm việc cho ai?",
        "Ai cấp bằng tốt nghiệp đại học?",
        "Môn Toán rời rạc do ai phụ trách?",
        "Ai có thể học lên thạc sĩ, tiến sĩ?",
        "Không cần gợi ý AI, cho biết tổng tín chỉ chương trình?",
    ],
)
def test_conversational_vietnamese_ai_never_matches_artificial_intelligence(
    rag_data: HUSRAGData,
    question: str,
):
    for major in SCOPES:
        codes, alias_tokens = match_scoped_courses(
            question,
            _courses(rag_data, major),
            major_aliases=MAJOR_NAMES,
            field_terms=COURSE_FIELD_TERMS,
        )
        assert "MAT1206E" not in codes
        assert "MAT3508" not in codes
        assert "MAT3377" not in codes
        assert "ai" not in alias_tokens


@pytest.mark.parametrize(
    "question,major",
    [
        ("ở ngành khoa học máy tính học mấy tín chỉ", "computer_science"),
        ("Ngành Khoa học máy tính và thông tin học mấy tín?", "computer_science"),
        ("Chương trình ngành Khoa học dữ liệu học mấy tc?", "data_science"),
    ],
)
def test_major_names_and_credit_phrases_never_false_match_hoc_may(
    rag_data: HUSRAGData,
    question: str,
    major: str,
):
    codes, alias_tokens = match_scoped_courses(
        question,
        _courses(rag_data, major),
        major_aliases=MAJOR_NAMES,
        field_terms=COURSE_FIELD_TERMS,
    )
    assert codes == set()
    assert alias_tokens == set()


@pytest.mark.parametrize(
    "question,major",
    [
        ("Môn CSDL có bao nhiêu tín chỉ?", "mathematics"),
        ("Môn MMT có bao nhiêu tín chỉ?", "mathematics"),
        ("Môn HĐH có bao nhiêu tín chỉ?", "data_science"),
        ("Môn CNPM có bao nhiêu tín chỉ?", "mathematics"),
        ("Môn LTHĐT có bao nhiêu tín chỉ?", "mathematics"),
        ("Môn TTNT có bao nhiêu tín chỉ?", "mathematics"),
        ("Môn CTDL&GT có bao nhiêu tín chỉ?", "mathematics"),
        ("Môn LTDT có bao nhiêu tín chỉ?", "computer_science"),
        ("Môn XLHA có bao nhiêu tín chỉ?", "data_science"),
    ],
)
def test_scoped_check_alias_not_in_selected_major_returns_empty(
    rag_data: HUSRAGData,
    question: str,
    major: str,
):
    codes, alias_tokens = match_scoped_courses(
        question,
        _courses(rag_data, major),
        major_aliases=MAJOR_NAMES,
        field_terms=COURSE_FIELD_TERMS,
    )
    assert codes == set()
    assert alias_tokens == set()


def test_gts_in_mathematics_returns_both_numerical_analysis_courses(rag_data: HUSRAGData):
    codes, alias_tokens = match_scoped_courses(
        "Môn GTS ở ngành Toán học có mấy tín chỉ?",
        _courses(rag_data, "mathematics"),
    )
    assert codes == {"MAT2307", "MAT3329"}
    assert alias_tokens == {"gts"}


def test_longer_course_titles_do_not_collide_with_shorter_aliases_or_names(rag_data: HUSRAGData):
    cs_courses = _courses(rag_data, "computer_science")
    ds_courses = _courses(rag_data, "data_science")

    codes_ai_topic, tokens_ai_topic = match_scoped_courses(
        "Môn Một số vấn đề chọn lọc về Trí tuệ nhân tạo có mấy tín chỉ?",
        cs_courses,
    )
    assert codes_ai_topic == {"MAT3377"}
    assert tokens_ai_topic == set()

    codes_web_db, tokens_web_db = match_scoped_courses(
        "Môn Cơ sở dữ liệu Web và hệ thống thông tin bao nhiêu tc?",
        ds_courses,
    )
    assert codes_web_db == {"MAT3385"}
    assert tokens_web_db == set()


def test_resolve_course_details_distinguishes_code_name_and_alias(rag_data: HUSRAGData):
    cs_courses = _courses(rag_data, "computer_science")

    by_code = resolve_course_details("MAT3507 có mấy tín chỉ?", cs_courses)
    assert by_code == [
        {
            "course_code": "MAT3507",
            "course_name": "Cơ sở dữ liệu",
            "match_type": "code",
        }
    ]

    by_name = resolve_course_details("Môn Cơ sở dữ liệu có mấy tín chỉ?", cs_courses)
    assert by_name == [
        {
            "course_code": "MAT3507",
            "course_name": "Cơ sở dữ liệu",
            "match_type": "name",
        }
    ]

    by_alias = resolve_course_details("Môn CSDL có mấy tín chỉ?", cs_courses)
    assert by_alias == [
        {
            "course_code": "MAT3507",
            "course_name": "Cơ sở dữ liệu",
            "match_type": "alias",
        }
    ]
