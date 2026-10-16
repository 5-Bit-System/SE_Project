import unicodedata

from app.hus.cleaning import clean_text, format_markdown_table, infer_document_type
from app.hus.models import DocumentType


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
