"""Text normalization, cleaning utilities, table formatting, and document type/major inference."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

from app.hus.models import DocumentType, MajorCategory


def clean_text(text: str) -> str:
    """Normalize Unicode to NFC, strip zero-width characters, and collapse spaces."""
    if not text:
        return ""
    for char in ("\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"):
        text = text.replace(char, "")
    return unicodedata.normalize("NFC", re.sub(r"[ \t]+", " ", text)).strip()


def _strip_accents(text: str) -> str:
    """Remove Vietnamese diacritics for robust URL slug matching."""
    decomposed = unicodedata.normalize("NFKD", text.replace("đ", "d").replace("Đ", "d"))
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def infer_document_type(title: str, content: str = "") -> DocumentType:
    """Infer DocumentType using keyword rules on title and content."""
    for text in (title.lower(), content[:300].lower()):
        if any(k in text for k in ("đơn", "biểu mẫu", "phiếu đăng ký")):
            return DocumentType.FORM
        if any(k in text for k in ("quy chế", "quy định", "hướng dẫn thực hiện", "điều lệ")):
            return DocumentType.REGULATION
        if any(k in text for k in ("thông báo", "kế hoạch", "lịch thi", "lịch học", "thời khóa biểu")):
            return DocumentType.ANNOUNCEMENT
        if any(k in text for k in ("chương trình đào tạo", "khung chương trình", "chuẩn đầu ra", "học phần")):
            return DocumentType.CURRICULUM
    return DocumentType.GENERAL_INFO


_FACULTY_PATTERN = re.compile(
    r"khoa\s+toán\s*(?:-\s*cơ\s*-\s*tin\s*học|-\s*cơ\s*-\s*tin|\s+cơ\s+tin\s+học|\s+cơ\s+tin|\b)",
    re.IGNORECASE,
)


def _find_all_major_matches(text: str) -> set[MajorCategory]:
    """Find all unique majors mentioned in normalized text with faculty names masked out."""
    if not text:
        return set()

    masked = _FACULTY_PATTERN.sub(" ", text.lower())
    matches: set[MajorCategory] = set()

    # 1. Data Science
    if any(k in masked for k in ("khoa học dữ liệu", "data science")) or re.search(r"\bkhdl\b", masked):
        matches.add(MajorCategory.DATA_SCIENCE)

    # 2. Computer Science
    if (
        any(
            k in masked
            for k in (
                "máy tính và khoa học thông tin",
                "khoa học máy tính",
                "máy tính và thông tin",
                "máy tính & khoa học thông tin",
                "khmt-tt",
            )
        )
        or re.search(r"\b(?:khmttt|mt&khtt|mtkhtt)\b", masked)
    ):
        matches.add(MajorCategory.COMPUTER_SCIENCE)

    # 3. Mathematics - Informatics
    if (
        any(
            k in masked
            for k in (
                "toán - tin",
                "toán tin",
                "toán học và tin học",
                "toán ứng dụng",
            )
        )
        or re.search(r"\btoantin\b", masked)
    ):
        matches.add(MajorCategory.MATHEMATICS_INFORMATICS)

    # 4. Mathematics (exclude 'toán học và tin học' which belongs to MATHEMATICS_INFORMATICS)
    text_for_math = masked.replace("toán học và tin học", " ")
    if (
        any(
            k in text_for_math
            for k in (
                "cử nhân tài năng toán",
                "toán cơ",
                "toán học",
            )
        )
        or re.search(r"\bcntn\s+toán\b", text_for_math)
    ):
        matches.add(MajorCategory.MATHEMATICS)

    return matches


def infer_major(title: str, url: str, content: str = "") -> MajorCategory:
    """Infer MajorCategory by inspecting URL slug, title, and initial content.

    Priority order:
    1. URL slug of Khoa Toán - Cơ - Tin học (MIM) & attachments.
    2. Keywords in document title.
    3. Keywords in initial content lead.
    4. Default to GENERAL for faculty/university-wide regulations and announcements.
    """
    unquoted_url = _strip_accents(unquote(url).lower())

    # 1. Check URL slug patterns
    if any(
        k in unquoted_url
        for k in (
            "/category/khoa-hoc-du-lieu",
            "/khoa-hoc-du-lieu",
            "khoa-hoc-du-lieu",
            "khoa hoc du lieu",
            "data-science",
            "data science",
        )
    ):
        return MajorCategory.DATA_SCIENCE

    if any(
        k in unquoted_url
        for k in (
            "/category/khmt-tt",
            "/khmt-tt",
            "khmt-tt",
            "khmttt",
            "/mt-khtt",
            "mt-khtt",
            "mt&khtt",
            "mtkhtt",
        )
    ):
        return MajorCategory.COMPUTER_SCIENCE

    if any(
        k in unquoted_url
        for k in (
            "/category/toantin",
            "/toantin",
            "toantin",
            "toan-tin",
            "toan tin",
        )
    ):
        return MajorCategory.MATHEMATICS_INFORMATICS

    if any(
        k in unquoted_url
        for k in (
            "/category/toanhoc",
            "/toanhoc",
            "toanhoc",
            "toan-hoc",
            "toan hoc",
        )
    ):
        return MajorCategory.MATHEMATICS

    # 2. Check title
    cleaned_title = clean_text(title)
    title_matches = _find_all_major_matches(cleaned_title)
    if len(title_matches) == 1:
        return next(iter(title_matches))

    # 3. Check lead content (up to 1000 characters)
    if content:
        lead_content = clean_text(content[:1000])
        content_matches = _find_all_major_matches(lead_content)
        if len(content_matches) == 1:
            return next(iter(content_matches))

    # 4. Default to GENERAL
    return MajorCategory.GENERAL


def infer_attachment_major(
    url: str, content: str = "", *, parent_major: MajorCategory = MajorCategory.GENERAL,
) -> MajorCategory:
    """Prefer an attachment's own major; otherwise inherit its parent's major.

    Shared by live crawling and catalog migration so inherited labels survive
    backfilling. Use the URL filename, as the crawler does, rather than the
    catalog's generated display title.
    """
    filename = Path(urlsplit(url).path).name or "attachment"
    major = infer_major(filename, url, content)
    return parent_major if major == MajorCategory.GENERAL else major


def format_markdown_table(rows: list[list[str]]) -> list[str]:
    """Format 2D table grid to standard Markdown table with column alignment."""
    if not rows:
        return []

    cleaned_rows = []
    for row in rows:
        cells = [clean_text(str(c)).replace("|", "/") for c in row]
        if any(cells):
            cleaned_rows.append(cells)

    if not cleaned_rows:
        return []

    col_count = max(len(r) for r in cleaned_rows)
    padded = [r + [""] * (col_count - len(r)) for r in cleaned_rows]

    lines = ["| " + " | ".join(padded[0]) + " |", "|" + " --- |" * col_count]
    for r in padded[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return lines


def extract_document(raw: bytes, url: str, fetched_at: str):
    from app.hus.extractors.html import extract_html

    doc, _ = extract_html(raw, url, fetched_at)
    doc.document_type = infer_document_type(doc.title, doc.content)
    doc.major = infer_major(doc.title, url, doc.content)
    return doc
