import unicodedata

import pytest

from app.hus.cleaning import (
    clean_table_cell,
    clean_text,
    format_markdown_table,
    infer_attachment_major,
    infer_document_type,
    infer_major,
    normalize_vertical_text,
    slugify,
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

    assert (
        infer_major(
            "Tài liệu",
            "https://mim.hus.vnu.edu.vn/sites/default/files/105.-Khoa-h%C3%A1%C2%BB%C2%8Dc-d%C3%A1%C2%BB%C2%AF-li%C3%A1%C2%BB%C2%87u-chu%C3%A1%C2%BA%C2%A9n%20final%20Q%C3%84%C2%90%203569%20Scan.pdf",
        )
        == MajorCategory.DATA_SCIENCE
    )

    # Mathematics - Informatics
    assert (
        infer_major("Thông tin", "https://mim.hus.vnu.edu.vn/category/toantin/")
        == MajorCategory.MATHEMATICS_INFORMATICS
    )
    assert (
        infer_major(
            "CTĐT",
            "https://mim.hus.vnu.edu.vn/sites/default/files/103.%20To%C3%83%C2%A1n%20tin-chu%C3%A1%C2%BA%C2%A9n%20final%20QD%203567%20Scan.pdf",
        )
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
        infer_major(
            "ThS Cơ sở toán học cho tin học CTDT 4934.pdf",
            "https://mim.hus.vnu.edu.vn/sites/default/files/116.%20ThS%20C%C6%A1%20s%E1%BB%9F%20to%C3%A1n%20h%E1%BB%8Dc%20cho%20tin%20h%E1%BB%8Dc%20CTDT%204934.pdf",
        )
        == MajorCategory.MATHEMATICS_INFORMATICS
    )
    assert (
        infer_major("Bộ môn Toán ứng dụng", "https://mim.hus.vnu.edu.vn/vi/news")
        == MajorCategory.MATHEMATICS
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


def test_clean_table_cell():
    assert clean_table_cell(None) == ""
    assert clean_table_cell("") == ""
    assert clean_table_cell("   ") == ""
    assert clean_table_cell("Normal text") == "Normal text"
    assert clean_table_cell("Option A | Option B") == "Option A / Option B"
    assert clean_table_cell("Line 1\nLine 2") == "Line 1<br>Line 2"
    assert clean_table_cell("Line 1\r\nLine 2\r\nLine 3") == "Line 1<br>Line 2<br>Line 3"
    assert clean_table_cell("  \n  <br>  Line 1  <br>  \n  ") == "Line 1"
    assert clean_table_cell("Multiple \n\n\n lines") == "Multiple<br>lines"
    assert clean_table_cell("Text with <br /> and <br>") == "Text with<br>and"
    assert clean_table_cell(123) == "123"


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


def test_format_markdown_table_with_newlines_and_breaks():
    grid = [
        ["STT", "Học phần\n(Chi tiết)", "Số TC\nLT/TH"],
        [1, "Toán cao cấp 1\n(Giải tích)", "3\n2/1"],
        [2, "Đại số | Tuyến tính\r\nKỳ 1", 3],
        [None, None, None],
    ]
    lines = format_markdown_table(grid)
    # Check that each output line is strictly on 1 physical line (no embedded newlines)
    for line in lines:
        assert "\n" not in line
        assert "\r" not in line
        assert line.startswith("| ")
        assert line.endswith(" |")

    assert lines[0] == "| STT | Học phần<br>(Chi tiết) | Số TC<br>LT/TH |"
    assert lines[1] == "| --- | --- | --- |"
    assert lines[2] == "| 1 | Toán cao cấp 1<br>(Giải tích) | 3<br>2/1 |"
    assert lines[3] == "| 2 | Đại số / Tuyến tính<br>Kỳ 1 | 3 |"
    assert len(lines) == 4


@pytest.mark.parametrize(
    "raw_input, expected",
    [
        # Spaces
        ("ỉhc nít ốS", "Số tín chỉ"),
        ("tếyuht íL", "Lý thuyết"),
        ("hnàh cựhT", "Thực hành"),
        ("cọh ựT", "Tự học"),
        # <br> tags
        ("ỉhc<br>nít<br>ốS", "Số tín chỉ"),
        ("tếyuht<br>íL", "Lý thuyết"),
        ("hnàh<br>cựhT", "Thực hành"),
        ("cọh<br>ựT", "Tự học"),
        # <br/> and <br /> with whitespace
        ("ỉhc<br/>nít<br />ốS", "Số tín chỉ"),
        ("ỉhc  <br>  nít  <br/>  ốS", "Số tín chỉ"),
        ("tếyuht <br /> íL", "Lý thuyết"),
        ("hnàh  <br>  cựhT", "Thực hành"),
        ("cọh  <br/>  ựT", "Tự học"),
        # Multiple <br> tags
        ("ỉhc<br><br>nít<br><br>ốS", "Số tín chỉ"),
        # Newlines
        ("ỉhc\nnít\nốS", "Số tín chỉ"),
        ("tếyuht\r\níL", "Lý thuyết"),
        ("hnàh\n\ncựhT", "Thực hành"),
        ("cọh\r\nựT", "Tự học"),
        # Case insensitivity
        ("ỈHC NÍT ỐS", "Số tín chỉ"),
        ("TẾYUHT ÍL", "Lý thuyết"),
        ("HNÀH CỰHT", "Thực hành"),
        ("CỌH ỰT", "Tự học"),
        ("ỉhc Nít ốs", "Số tín chỉ"),
        ("Tếyuht Íl", "Lý thuyết"),
        ("Hnàh Cựht", "Thực hành"),
        ("Cọh Ựt", "Tự học"),
        # Embedded in markdown table rows
        (
            "| STT | Mã<br>học phần | Học phần | ỉhc<br>nít<br>ốS | Số giờ tín chỉ |",
            "| STT | Mã<br>học phần | Học phần | Số tín chỉ | Số giờ tín chỉ |",
        ),
        (
            "|  |  |  |  | tếyuht<br>íL | hnàh<br>cựhT | cọh<br>ựT |  |",
            "|  |  |  |  | Lý thuyết | Thực hành | Tự học |  |",
        ),
        # Normal text remains unchanged
        ("Toán giải tích", "Toán giải tích"),
        ("", ""),
    ],
)
def test_normalize_vertical_text_variations(raw_input: str, expected: str):
    assert normalize_vertical_text(raw_input) == expected


def test_clean_table_cell_vertical_text():
    assert clean_table_cell("ỉhc<br>nít<br>ốS") == "Số tín chỉ"
    assert clean_table_cell("ỉhc\nnít\nốS") == "Số tín chỉ"
    assert clean_table_cell("tếyuht<br>íL") == "Lý thuyết"
    assert clean_table_cell("hnàh\ncựhT") == "Thực hành"
    assert clean_table_cell("cọh<br>ựT") == "Tự học"
    assert clean_table_cell("  \n ỉhc <br> nít <br> ốS \n ") == "Số tín chỉ"


def test_clean_text_vertical_text():
    assert clean_text("Khung chương trình: ỉhc nít ốS") == "Khung chương trình: Số tín chỉ"
    assert clean_text("tếyuht íL và hnàh cựhT") == "Lý thuyết và Thực hành"


def test_format_markdown_table_vertical_text():
    grid = [
        ["STT", "Mã\nhọc phần", "Học phần", "ỉhc\nnít\nốS", "Số giờ tín chỉ", None, None, "Mã số\ntiên quyết"],
        [None, None, None, None, "tếyuht\níL", "hnàh\ncựhT", "cọh\nựT", None],
        [1, "MAT1001", "Giải tích 1", 3, 30, 15, 0, None],
    ]
    lines = format_markdown_table(grid)
    assert len(lines) == 4
    assert lines[0] == "| STT | Mã<br>học phần | Học phần | Số tín chỉ | Số giờ tín chỉ |  |  | Mã số<br>tiên quyết |"
    assert lines[1] == "| --- | --- | --- | --- | --- | --- | --- | --- |"
    assert lines[2] == "|  |  |  |  | Lý thuyết | Thực hành | Tự học |  |"
    assert lines[3] == "| 1 | MAT1001 | Giải tích 1 | 3 | 30 | 15 | 0 |  |"
    for token in ("ỉhc", "tếyuht", "hnàh", "cọh"):
        for line in lines:
            assert token not in line


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


def test_slugify_basic():
    assert slugify("Thông báo đào tạo") == "thong-bao-dao-tao"
    assert slugify("Khoa Toán - Cơ - Tin học (MIM)") == "khoa-toan-co-tin-hoc-mim"
    assert slugify("Đề án & Quy chế Đào tạo -- HUS (2023)") == "de-an-quy-che-dao-tao-hus-2023"


def test_slugify_special_characters_and_whitespace():
    assert slugify("  --- Hello   World ---  ") == "hello-world"
    assert slugify("file_name.test_123.pdf") == "file-name-test-123-pdf"
    assert slugify("!@#$%^&*()") == ""
    assert slugify("") == ""


def test_slugify_max_length():
    long_title = "Đây là một tiêu đề rất dài để kiểm tra tính năng cắt ngắn ký tự của slugify"
    slug = slugify(long_title, max_length=30)
    assert len(slug) <= 30
    assert not slug.endswith("-")
    assert not slug.startswith("-")
