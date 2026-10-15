from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import hashlib
import re
import unicodedata
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Comment, NavigableString, Tag

from app.hus.models import HUSDocument
from app.hus.urls import CrawlError, canonicalize_url

_DROP = (
    "nav, header, footer, aside, form, script, style, noscript, iframe, svg, "
    "[role=navigation], .breadcrumb, .pager, .menu, .tabs"
)
_MAIN = ("main", "[role=main]", "#content", "#main-content", ".region-content", "article")
_HEADINGS = {f"h{n}" for n in range(1, 7)}
_INLINE = {"a", "span", "strong", "b", "em", "i", "u", "font", "small", "sup", "sub", "code", "abbr"}
_SKIP_EXT = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".rar")
_SKIP_EXT += (".jpg", ".jpeg", ".png", ".gif")  # attachments/images are out of the HTML-only MVP
_DATE_RE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})(?:\s*-\s*(\d{1,2}):(\d{2}))?")
_VN = timezone(timedelta(hours=7))


def _clean(text: str) -> str:
    text = text.replace("\u200b", "")
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", text)).strip()


def _links(soup: BeautifulSoup, base: str) -> list[str]:
    # Collected before cleaning: menus are the only discovery path (no sitemap on the sites).
    found = set()
    for a in soup.find_all("a", href=True):
        try:
            url = canonicalize_url(urljoin(base, a["href"].strip()))
        except CrawlError:
            continue
        if not url.split("?")[0].lower().endswith(_SKIP_EXT):
            found.add(url)
    return sorted(found)


def _valid_iso(value: str) -> str | None:
    try:
        datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    return value.strip()


def _published(soup: BeautifulSoup) -> str | None:
    # Only dedicated date markup counts: a date inside the body may be an effective date.
    meta = soup.find("meta", property="article:published_time")
    if meta and meta.get("content") and (iso := _valid_iso(meta["content"])):
        return iso
    tag = soup.find("time", datetime=True)
    if tag and (iso := _valid_iso(tag["datetime"])):
        return iso
    for el in soup.select(".submitted, .date-display-single, .post-date, .created"):
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
        if el and len(_clean(el.get_text(" "))) >= 80:
            return el
    return soup.body or soup


def _table(table: Tag) -> list[str]:
    rows = []
    for tr in table.find_all("tr"):
        cells = [_clean(c.get_text(" ")).replace("|", "/") for c in tr.find_all(["th", "td"])]
        if any(cells):
            rows.append("| " + " | ".join(cells) + " |")
    if len(rows) > 1:  # shortcut: colspan/rowspan are not expanded, check merged-cell tables
        rows.insert(1, "|" + " --- |" * (rows[0].count("|") - 1))
    return rows


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


def extract_document(raw: bytes, url: str, fetched_at: str) -> HUSDocument:
    soup = BeautifulSoup(raw, "html.parser")
    links = _links(soup, url)
    published_at = _published(soup)
    og = soup.find("meta", property="og:title")
    page_title = _clean(og["content"]) if og and og.get("content") else ""
    if not page_title and soup.title:
        page_title = _clean(soup.title.get_text()).split(" | ")[0]

    for tag in soup.select(_DROP):
        tag.decompose()
    main = _main(soup)
    for a in main.find_all("a", href=True):
        text = _clean(a.get_text(" "))
        try:
            href = canonicalize_url(urljoin(url, a["href"].strip()))
        except CrawlError:
            a.replace_with(text)
            continue
        a.replace_with(f"[{text}]({href})" if text else "")

    h1 = main.find("h1")
    title = _clean(h1.get_text(" ")) if h1 else page_title
    content = "\n".join(_lines(main)).strip()
    if not content:
        raise CrawlError(f"empty content: {url}")
    return HUSDocument(
        url=url,
        title=title or url,
        published_at=published_at,
        fetched_at=fetched_at,
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        content=content,
        links=links,
    )