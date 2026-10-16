"""Allowlisted, robots-aware fetching for HTML and attachments."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import time
from urllib import robotparser
from urllib.parse import urljoin, urlsplit

import httpx

from app.hus.allowlist import Allowlist, check_allowed
from app.hus.cleaning import extract_document
from app.hus.models import HUSDocument
from app.hus.urls import CrawlError, is_private_host

MAX_HTML_BYTES = 2 * 1024 * 1024         # 2 MB for HTML
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024  # 20 MB for PDF/DOCX/XLSX
MAX_BYTES = MAX_HTML_BYTES               # backward compatibility
MAX_REDIRECTS = 3
_TRANSIENT = {429, 500, 502, 503, 504}
_REDIRECTS = {301, 302, 303, 307, 308}


class Robots:
    """robots.txt per host. 4xx = allow all; 5xx, redirect or network error = disallow all."""

    def __init__(self, client: httpx.Client, user_agent: str):
        self.client, self.user_agent = client, user_agent
        self._cache: dict[str, robotparser.RobotFileParser] = {}

    def allows(self, url: str) -> bool:
        host = urlsplit(url).hostname or ""
        if host not in self._cache:
            self._cache[host] = self._load(host)
        return self._cache[host].can_fetch(self.user_agent, url)

    def _load(self, host: str) -> robotparser.RobotFileParser:
        parser = robotparser.RobotFileParser()
        try:
            response = self.client.get(f"https://{host}/robots.txt", follow_redirects=False)
        except httpx.HTTPError:
            parser.disallow_all = True
            return parser
        if response.status_code == 200:
            parser.parse(response.text.splitlines())
        elif 400 <= response.status_code < 500:
            parser.allow_all = True
        else:
            parser.disallow_all = True
        return parser


def _get(
    client: httpx.Client,
    url: str,
    attempts: int,
    backoff: float,
    sleep,
    max_bytes: int = MAX_HTML_BYTES,
    headers: dict[str, str] | None = None,
) -> tuple[int, httpx.Headers, bytes]:
    last = "no attempt"
    req_headers = dict(headers or {})
    for attempt in range(attempts):
        try:
            with client.stream("GET", url, headers=req_headers, follow_redirects=False) as response:
                status, resp_headers, body = response.status_code, response.headers, bytearray()
                if status == 200:
                    for part in response.iter_bytes():
                        body += part
                        if len(body) > max_bytes:
                            raise CrawlError(f"response over {max_bytes} bytes: {url}")
            if status not in _TRANSIENT:
                return status, resp_headers, bytes(body)
            last = f"HTTP {status}"
        except httpx.TransportError as exc:
            last = type(exc).__name__
        if attempt < attempts - 1:
            sleep(backoff * 2**attempt)
    raise CrawlError(f"gave up after {attempts} attempts ({last}): {url}")


def fetch_html(
    url: str,
    allowlist: Allowlist,
    client: httpx.Client,
    robots: Robots,
    *,
    sleep=time.sleep,
    headers: dict[str, str] | None = None,
) -> tuple[str, httpx.Headers, bytes]:
    """Fetch one HTML page, re-checking allowlist and robots on every redirect hop."""
    current, hops = check_allowed(url, allowlist), 0
    while True:
        if not robots.allows(current):
            raise CrawlError(f"robots.txt disallows {current}")
        status, resp_headers, body = _get(
            client,
            current,
            allowlist.retry_attempts,
            allowlist.delay_seconds,
            sleep,
            max_bytes=MAX_HTML_BYTES,
            headers=headers,
        )
        if status in _REDIRECTS:
            hops += 1
            if hops > MAX_REDIRECTS or "location" not in resp_headers:
                raise CrawlError(f"bad redirect from {current}")
            current = check_allowed(urljoin(current, resp_headers["location"]), allowlist)
            continue
        if status == 304:
            return current, resp_headers, b""
        if status != 200:
            raise CrawlError(f"HTTP {status}: {current}")
        if "html" not in resp_headers.get("content-type", "").lower():
            raise CrawlError(f"not HTML: {current}")
        return current, resp_headers, body


def fetch_attachment(
    url: str,
    allowlist: Allowlist,
    client: httpx.Client,
    robots: Robots,
    *,
    sleep=time.sleep,
    headers: dict[str, str] | None = None,
) -> tuple[str, httpx.Headers, bytes]:
    """Fetch one binary attachment up to MAX_ATTACHMENT_BYTES (20MB) safely."""
    current, hops = check_allowed(url, allowlist), 0
    while True:
        if not robots.allows(current):
            raise CrawlError(f"robots.txt disallows {current}")
        status, resp_headers, body = _get(
            client,
            current,
            allowlist.retry_attempts,
            allowlist.delay_seconds,
            sleep,
            max_bytes=MAX_ATTACHMENT_BYTES,
            headers=headers,
        )
        if status in _REDIRECTS:
            hops += 1
            if hops > MAX_REDIRECTS or "location" not in resp_headers:
                raise CrawlError(f"bad redirect from {current}")
            current = check_allowed(urljoin(current, resp_headers["location"]), allowlist)
            continue
        if status == 304:
            return current, resp_headers, b""
        if status != 200:
            raise CrawlError(f"HTTP {status}: {current}")
        return current, resp_headers, body


def crawl_document(
    url: str, allowlist: Allowlist, client: httpx.Client, robots: Robots, *, sleep=time.sleep
) -> tuple[HUSDocument, bytes]:
    final, _headers, raw = fetch_html(url, allowlist, client, robots, sleep=sleep)
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return extract_document(raw, final, fetched_at), raw


def crawl(
    allowlist: Allowlist, client: httpx.Client, *, sleep=time.sleep
) -> tuple[list[tuple[HUSDocument, bytes]], dict[str, str]]:
    """Breadth-first from seeds. Preserved for backward compatibility."""
    robots = Robots(client, allowlist.user_agent)
    queue = deque((seed, 0) for seed in allowlist.seeds)
    seen: set[str] = set()
    documents: list[tuple[HUSDocument, bytes]] = []
    failures: dict[str, str] = {}
    while queue and len(documents) < allowlist.max_pages:
        url, depth = queue.popleft()
        try:
            url = check_allowed(url, allowlist)
            if url in seen:
                continue
            seen.add(url)
            document, raw = crawl_document(url, allowlist, client, robots, sleep=sleep)
        except CrawlError as exc:
            failures[url] = str(exc)
            continue
        if document.url in seen and document.url != url:
            continue
        seen.add(document.url)
        documents.append((document, raw))
        if depth < allowlist.max_depth:
            for link in document.links:
                try:
                    queue.append((check_allowed(link, allowlist), depth + 1))
                except CrawlError:
                    pass
        sleep(allowlist.delay_seconds)
    return documents, failures