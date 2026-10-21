import unicodedata

import pytest

from app.hus.cleaning import (
    clean_text,
    format_markdown_table,
    infer_attachment_major,
    infer_document_type,
    infer_major,
)
from app.hus.models import DocumentType, MajorCategory


def test_clean_text_nfc_and_zero_width():
    # Decomposed Vietnamese "ế" (e + acute + circumflex) vs NFC
    decomposed = "ke\u0302\u0301 hoa\u0323ch"
    cleaned = clean_text(f"\u200b{decomposed}\ufeff   n\u0103m   2026")
    assert unicodedata.is_normalized("NFC", cleaned)
    assert cleaned == "kế hoạch năm 2026"
    assert clean_text("A\u200c\u200d\u2060B") == "AB"


def test_infer_document_type():
    assert infer_document_type("Quy chế đào tạo đại học năm 2026") == DocumentType.REGULATION
    assert infer_document_type("Thông báo về việc đóng học phí") == DocumentType.ANNOUNCEMENT
    assert infer_document_type("Khung chương trình đào tạo Cử nhân Toán học") == DocumentType.CURRICULUM
    assert infer_document_type("Mẫu đơn xin hoãn thi kết thúc học phần") == DocumentType.FORM
    assert infer_document_type("Giới thiệu về khoa Toán - Cơ - Tin học") == DocumentType.GENERAL_INFO
    assert infer_document_type("Đơn đề nghị cấp giấy", "Quy định chung") == DocumentType.FORM
    assert infer_document_type("Quy chế đào tạo", "Mẫu đơn xin học lại") == DocumentType.REGULATION


def test_infer_major_from_url():
    # Data Science
    assert (
        infer_major("Thông tin chung", "https://mim.hus.vnu.edu.vn/category/khoa-hoc-du-lieu/")
        == MajorCategory.DATA_SCIENCE
    )
    assert (
        infer_major("Giới thiệu", "https://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu")
        == MajorCategory.DATA_SCIENCE
    )
    assert (
        infer_major(
            "Tài liệu",
            "https://mim.hus.vnu.edu.vn/sites/default/files/105.-Khoa-h%E1%BB%8Dc-d%E1%BB%AF-li%E1%BB%87u-chuan.pdf",
        )
        == MajorCategory.DATA_SCIENCE
    )

    # Computer Science
    assert (
        infer_major("Chương trình", "https://mim.hus.vnu.edu.vn/category/khmt-tt/")
        == MajorCategory.COMPUTER_SCIENCE
    )
    assert (
        infer_major("Ngành đào tạo", "https://mim.hus.vnu.edu.vn/vi/khmt-tt")
        == MajorCategory.COMPUTER_SCIENCE
    )
    assert (
        infer_major("Chương trình CLC", "https://mim.hus.vnu.edu.vn/vi/mt-khtt-clc")
        == MajorCategory.COMPUTER_SCIENCE
    )
    assert (
        infer_major(
            "Đề cương",
            "https://mim.hus.vnu.edu.vn/sites/default/files/104.-KHMTTT-chuan.docx",
        )
        == MajorCategory.COMPUTER_SCIENCE
    )

    # Mathematics - Informatics
    assert (
        infer_major("Thông tin", "https://mim.hus.vnu.edu.vn/category/toantin/")
        == MajorCategory.MATHEMATICS_INFORMATICS
    )
    assert (
        infer_major(
            "CTĐT",
            "https://mim.hus.vnu.edu.vn/sites/default/files/103.%20To%C3%A1n%20tin-chuan.pdf",
        )
        == MajorCategory.MATHEMATICS_INFORMATICS
    )

    # Mathematics
    assert (
        infer_major("Đào tạo", "https://mim.hus.vnu.edu.vn/category/toanhoc/")
        == MajorCategory.MATHEMATICS
    )
    assert (
        infer_major(
            "CTĐT Toán",
            "https://mim.hus.vnu.edu.vn/sites/default/files/CTDT-Toanhoc-130815.pdf",
        )
        == MajorCategory.MATHEMATICS
    )


def test_infer_major_from_title_and_content():
    # Data Science
    assert (
        infer_major("Tuyển sinh ngành Khoa học dữ liệu 2026", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.DATA_SCIENCE
    )
    assert (
        infer_major("Data Science Laboratory", "https://mim.hus.vnu.edu.vn/vi/content/dslab")
        == MajorCategory.DATA_SCIENCE
    )
    assert (
        infer_major("Định hướng chuyên sâu KHDL", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.DATA_SCIENCE
    )

    # Computer Science
    assert (
        infer_major(
            "Ngành Máy tính và Khoa học thông tin", "https://mim.hus.vnu.edu.vn/vi/news"
        )
        == MajorCategory.COMPUTER_SCIENCE
    )
    assert (
        infer_major("Ngành Khoa học máy tính", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.COMPUTER_SCIENCE
    )
    assert (
        infer_major("Thông báo sinh viên KHMT-TT", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.COMPUTER_SCIENCE
    )
    assert (
        infer_major("Khung CTĐT MT&KHTT", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.COMPUTER_SCIENCE
    )

    # Mathematics - Informatics
    assert (
        infer_major("Ngành Toán - Tin", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.MATHEMATICS_INFORMATICS
    )
    assert (
        infer_major("Ngành Toán tin ứng dụng", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.MATHEMATICS_INFORMATICS
    )
    assert (
        infer_major(
            "Chương trình đào tạo Toán học và Tin học", "https://mim.hus.vnu.edu.vn/vi/news"
        )
        == MajorCategory.MATHEMATICS_INFORMATICS
    )
    assert (
        infer_major("Bộ môn Toán ứng dụng", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.MATHEMATICS_INFORMATICS
    )

    # Mathematics
    assert (
        infer_major("Cử nhân ngành Toán học", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.MATHEMATICS
    )
    assert (
        infer_major("Cử nhân tài năng Toán", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.MATHEMATICS
    )
    assert (
        infer_major("Lớp CNTN Toán K68", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.MATHEMATICS
    )
    assert (
        infer_major("Bộ môn Toán cơ", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.MATHEMATICS
    )

    # Content lead fallback when title is generic
    assert (
        infer_major(
            "Thông báo chung",
            "https://mim.hus.vnu.edu.vn/vi/news",
            "Về việc tổ chức hội thảo ngành Khoa học dữ liệu năm 2026...",
        )
        == MajorCategory.DATA_SCIENCE
    )
    assert (
        infer_major(
            "Thông báo chung",
            "https://mim.hus.vnu.edu.vn/vi/news",
            "Kế hoạch thực tập dành riêng cho sinh viên ngành Toán - Tin...",
        )
        == MajorCategory.MATHEMATICS_INFORMATICS
    )


@pytest.mark.parametrize("path", [
    "/vi/toan-hoc-va-tin-hoc",
    "/category/toan-hoc-va-tin-hoc/",
    "/vi/TOAN-HOC-VA-TIN-HOC",
    "/files/103.-Toan-hoc-va-Tin-hoc-chuan.docx",
    "/files/Toán học và Tin học.pdf",
    "/files/To%C3%A1n%20h%E1%BB%8Dc%20v%C3%A0%20Tin%20h%E1%BB%8Dc.pdf",
    "/vi/toan-hoc/toan-hoc-va-tin-hoc",
])
def test_full_math_informatics_url_takes_precedence_over_mathematics(path: str) -> None:
    url = f"https://mim.hus.vnu.edu.vn{path}"
    for title in ("Chương trình Toán học và Tin học", "Thông tin đào tạo"):
        assert infer_major(title, url) == MajorCategory.MATHEMATICS_INFORMATICS
    assert infer_attachment_major(
        url, "Thông tin chương trình.", parent_major=MajorCategory.MATHEMATICS,
    ) == MajorCategory.MATHEMATICS_INFORMATICS


def test_mathematics_url_with_other_suffix_stays_mathematics() -> None:
    assert infer_major(
        "Thông tin đào tạo", "https://mim.hus.vnu.edu.vn/vi/toan-hoc-va-ung-dung",
    ) == MajorCategory.MATHEMATICS


@pytest.mark.parametrize("title", [
    "Thông báo dành cho Toán học và Khoa học dữ liệu",
    "Thông báo dành cho Toán học và Khoa học máy tính",
    "Thông báo dành cho Toán học và Toán - Tin",
    "Thông báo dành cho Toán học và Tin học, Khoa học dữ liệu",
    "Thông báo dành cho Toán - Tin và Khoa học máy tính",
    "Thông báo dành cho Khoa học máy tính và Khoa học dữ liệu",
])
@pytest.mark.parametrize("path", ["/vi/news", "/vi/toan-hoc"])
def test_multiple_majors_in_title_stay_general(title: str, path: str) -> None:
    url = f"https://mim.hus.vnu.edu.vn{path}"
    # Neither a single-major lead nor a missing lead may narrow the title's scope.
    for content in ("Sinh viên ngành Toán học đăng ký học phần theo hướng dẫn sau.", ""):
        assert infer_major(title, url, content) == MajorCategory.GENERAL
        assert infer_major(
            unicodedata.normalize("NFD", title.upper()), url, content,
        ) == MajorCategory.GENERAL


def test_faculty_name_and_compound_major_do_not_count_as_multiple_majors() -> None:
    assert infer_major(
        "Khoa Toán - Cơ - Tin học: Chương trình Toán học và Tin học",
        "https://mim.hus.vnu.edu.vn/vi/news",
        "Sinh viên ngành Toán học đăng ký học phần.",
    ) == MajorCategory.MATHEMATICS_INFORMATICS


def test_infer_major_general_and_defaults():
    # University-wide / General documents
    assert (
        infer_major("Quy chế đào tạo đại học năm 2026", "https://hus.vnu.edu.vn/dao-tao/dai-hoc")
        == MajorCategory.GENERAL
    )
    assert (
        infer_major("Bậc đào tạo", "https://tuyensinh.hus.vnu.edu.vn/dai-hoc")
        == MajorCategory.GENERAL
    )
    # Faculty-wide information (Khoa Toán - Cơ - Tin học as a whole)
    assert (
        infer_major(
            "Giới thiệu về khoa Toán - Cơ - Tin học", "https://mim.hus.vnu.edu.vn/vi/gioi-thieu"
        )
        == MajorCategory.GENERAL
    )
    assert (
        infer_major("Sứ mệnh & Tầm nhìn", "https://mim.hus.vnu.edu.vn/vi/content/su-menh-tam-nhin")
        == MajorCategory.GENERAL
    )
    assert (
        infer_major("Biểu mẫu", "https://mim.hus.vnu.edu.vn/vi/cacloaibieumau")
        == MajorCategory.GENERAL
    )
    assert (
        infer_major("Học bổng", "https://mim.hus.vnu.edu.vn/vi/scholarships")
        == MajorCategory.GENERAL
    )


def test_format_markdown_table():
    grid = [
        ["Mã HP", "Tên học phần", "Tín chỉ"],
        ["MAT1001", "Giải tích 1", "3"],
        ["MAT1002", "Đại số tuyến tính", "3"],
    ]
    lines = format_markdown_table(grid)
    assert lines[0] == "| Mã HP | Tên học phần | Tín chỉ |"
    assert lines[1] == "| --- | --- | --- |"
    assert lines[2] == "| MAT1001 | Giải tích 1 | 3 |"


@pytest.mark.parametrize("scope", [
    "Quy chế áp dụng cho tất cả sinh viên toàn trường.",
    "Quy định áp dụng chung cho sinh viên toàn khoa.",
    "Thông báo dành cho tất cả các ngành học.",
    "Quy chế áp dụng cho toàn bộ sinh viên trong toàn trường.",
    "Quy chế áp dụng cho sinh viên các ngành.",
])
def test_explicit_shared_scope_prevents_attachment_inheritance(scope: str) -> None:
    assert infer_attachment_major(
        "https://mim.hus.vnu.edu.vn/files/rules.docx", scope,
        parent_major=MajorCategory.DATA_SCIENCE,
    ) == MajorCategory.GENERAL


def test_shared_scope_overrides_incidental_major_and_url() -> None:
    content = (
        "Quy chế áp dụng cho tất cả sinh viên toàn trường. "
        "Ví dụ minh họa cho ngành Khoa học dữ liệu."
    )
    url = "https://mim.hus.vnu.edu.vn/files/khoa-hoc-du-lieu/rules.docx"
    assert infer_major("Quy chế", url, content) == MajorCategory.GENERAL
    assert infer_attachment_major(
        url, content, parent_major=MajorCategory.DATA_SCIENCE,
    ) == MajorCategory.GENERAL


def test_shared_scope_in_title() -> None:
    assert infer_major(
        "Quy định chung toàn trường", "https://mim.hus.vnu.edu.vn/vi/khoa-hoc-du-lieu",
    ) == MajorCategory.GENERAL


@pytest.mark.parametrize("content, expected", [
    ("Hướng dẫn đăng ký học phần.", MajorCategory.DATA_SCIENCE),
    ("Áp dụng cho tất cả sinh viên ngành Khoa học dữ liệu.", MajorCategory.DATA_SCIENCE),
    ("Tham khảo quy chế toàn trường.", MajorCategory.DATA_SCIENCE),
    ("Không áp dụng cho sinh viên toàn trường; dành riêng ngành Khoa học dữ liệu.",
     MajorCategory.DATA_SCIENCE),
    ("Chưa áp dụng cho sinh viên toàn trường. Ngành Khoa học máy tính thử nghiệm.",
     MajorCategory.COMPUTER_SCIENCE),
])
def test_only_unknown_attachments_inherit_parent(content: str, expected: MajorCategory) -> None:
    assert infer_attachment_major(
        "https://mim.hus.vnu.edu.vn/files/guide.docx", content,
        parent_major=MajorCategory.DATA_SCIENCE,
    ) == expected
