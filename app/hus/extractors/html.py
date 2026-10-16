"""HTML extraction, markdown conversion, and attachment discovery."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import hashlib
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from app.hus.cleaning import clean_text
from app.hus.models import DocumentStatus, DocumentType, HUSAttachment, HUSDocument, Publisher
from app.hus.urls import CrawlError, canonicalize_url

_DROP = (
    "nav, header, footer, aside, form, script, style, noscript, iframe, svg, "
    "[role=navigation], .breadcrumb, .pager, .menu, .tabs, .sidebar"
)
_MAIN = ("main", "[role=main]", "#content", "#main-content", ".region-content", "article", ".post-content", ".entry-content")
_HEADINGS = {f"h{n}" for n in range(1, 7)}
_INLINE = {"a", "span", "strong", "b", "em", "i", "u", "font", "small", "sup", "sub", "code", "abbr"}
_ATTACHMENT_EXT = (".pdf", ".doc", ".docx", ".xls", ".xlsx")
_DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})(?:\s*-\s*(\d{1,2}):(\d{2}))?")
_VN = timezone(timedelta(hours=7))


def _clean(text: str) -> str:
    return clean_text(re.sub(r"\s+", " ", text))


def _valid_iso(value: str) -> str | None:
    try:
        datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    return value.strip()


def _published(soup: BeautifulSoup) -> str | None:
    meta = soup.find("meta", property="article:published_time")
    if meta and meta.get("content") and (iso := _valid_iso(meta["content"])):
        return iso
    tag = soup.find("time", datetime=True)
    if tag and (iso := _valid_iso(tag["datetime"])):
        return iso
    for el in soup.select(".submitted, .date-display-single, .post-date, .created, .time"):
        m = _DATE_RE.search(el.get_text(" "))
        if not m:
            continue
        day, month, year, hour, minute = m.groups()
        try:
            if hour is None:
                return date(int(year), int(month), int(day)).isoformat()
            return datetime(
                int(year), int(month), int(day), int(hour), int(minute), tzinfo=_VN
            ).isoformat()
        except ValueError:
            continue
    return None


def _main(soup: BeautifulSoup) -> Tag:
    for selector in _MAIN:
        el = soup.select_one(selector)
        if el and _clean(el.get_text(" ")):
            return el
    return soup.body or soup


def _table(table: Tag) -> list[str]:
    # Expand colspan/rowspan by building a 2D matrix
    rows_data: list[list[str]] = []
    matrix: list[dict[int, str]] = []
    table_rows = table.find_all("tr")

    def span(value: str | int, limit: int) -> int:
        try:
            return max(1, min(int(value), limit))
        except ValueError:
            return 1

    for r_idx, tr in enumerate(table_rows):
        if len(matrix) <= r_idx:
            matrix.append({})
        c_idx = 0
        for cell in tr.find_all(["th", "td"]):
            while c_idx in matrix[r_idx]:
                c_idx += 1
            text = _clean(cell.get_text(" ")).replace("|", "/")
            rowspan = span(cell.get("rowspan", 1) or 1, len(table_rows) - r_idx)
            # shortcut: cap malformed colspan at 128; raise if HUS publishes wider real tables.
            colspan = span(cell.get("colspan", 1) or 1, 128)
            for r in range(r_idx, r_idx + rowspan):
                while len(matrix) <= r:
                    matrix.append({})
                for c in range(c_idx, c_idx + colspan):
                    matrix[r][c] = text
            c_idx += colspan

    for row_dict in matrix:
        if not row_dict:
            continue
        max_col = max(row_dict.keys())
        row_cells = [row_dict.get(c, "") for c in range(max_col + 1)]
        if any(row_cells):
            rows_data.append(row_cells)

    if not rows_data:
        return []

    lines = []
    col_count = max(len(r) for r in rows_data)
    padded_rows = [r + [""] * (col_count - len(r)) for r in rows_data]

    lines.append("| " + " | ".join(padded_rows[0]) + " |")
    lines.append("|" + " --- |" * col_count)
    for r in padded_rows[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return lines


def _lines(node: Tag) -> list[str]:
    lines: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if text := _clean("".join(buf)):
            lines.append(text)
        buf.clear()

    for child in node.children:
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            buf.append(str(child))
        elif child.name in _INLINE:
            buf.append(child.get_text())
        elif child.name == "br":
            flush()
        else:
            flush()
            if child.name in _HEADINGS:
                if text := _clean(child.get_text(" ")):
                    lines.append(f"{'#' * int(child.name[1])} {text}")
            elif child.name == "table":
                lines.extend(_table(child))
            elif child.name in ("ul", "ol"):
                for li in child.find_all("li", recursive=False):
                    if text := _clean(li.get_text(" ")):
                        lines.append(f"- {text}")
            elif child.name in ("p", "pre", "blockquote"):
                if text := _clean(child.get_text()):
                    lines.append(text)
            else:
                lines.extend(_lines(child))
    flush()
    return lines


def _infer_publisher(url: str) -> Publisher:
    lower = url.lower()
    if "mim.hus.vnu.edu.vn" in lower:
        return Publisher.MIM
    if "tuyensinh.hus.vnu.edu.vn" in lower:
        return Publisher.TUYENSINH
    return Publisher.HUS


def extract_html(raw: bytes, url: str, fetched_at: str) -> tuple[HUSDocument, list[str]]:
    """Parse HTML, extract main text to markdown, and discover attachment links."""
    soup = BeautifulSoup(raw, "html.parser", from_encoding="utf-8")

    # Discover page navigation links (excluding file attachments)
    page_links = set()
    attachment_urls = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        try:
            target_url = canonicalize_url(urljoin(url, href))
        except CrawlError:
            continue
        pure_path = target_url.split("?")[0].lower()
        if not any(pure_path.endswith(ext) for ext in _ATTACHMENT_EXT):
            page_links.add(target_url)

    published_at = _published(soup)
    og = soup.find("meta", property="og:title")
    page_title = _clean(og["content"]) if og and og.get("content") else ""
    if not page_title and soup.title:
        page_title = _clean(soup.title.get_text()).split(" | ")[0]

    for tag in soup.select(_DROP):
        tag.decompose()

    main = _main(soup)

    # Format attachment links and normal links in body
    attachments: list[HUSAttachment] = []
    for a in main.find_all("a", href=True):
        text = _clean(a.get_text(" "))
        try:
            href = canonicalize_url(urljoin(url, a["href"].strip()))
        except CrawlError:
            a.replace_with(text)
            continue
        pure_href = href.split("?")[0].lower()
        matched_ext = next((ext.lstrip(".") for ext in _ATTACHMENT_EXT if pure_href.endswith(ext)), None)
        if matched_ext:
            attachment_urls.append(href)
            att_id = hashlib.sha256(href.encode()).hexdigest()[:16]
            attachments.append(
                HUSAttachment(
                    attachment_id=att_id,
                    source_url=href,
                    file_type=matched_ext,
                    status=DocumentStatus.ACTIVE,
                )
            )
            a.replace_with(f"[{text or matched_ext.upper()}]({href})")
        else:
            a.replace_with(f"[{text}]({href})" if text else "")

    h1 = main.find("h1")
    title = _clean(h1.get_text(" ")) if h1 else page_title
    content = "\n".join(_lines(main)).strip()
    if not content:
        raise CrawlError(f"empty content: {url}")

    doc = HUSDocument(
        url=url,
        title=title or url,
        published_at=published_at,
        fetched_at=fetched_at,
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        content=content,
        links=sorted(page_links),
        attachments=attachments,
        publisher=_infer_publisher(url),
        document_type=DocumentType.GENERAL_INFO,
        status=DocumentStatus.ACTIVE,
    )
    return doc, sorted(set(attachment_urls))
