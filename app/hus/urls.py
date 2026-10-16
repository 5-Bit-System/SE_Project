from __future__ import annotations

import ipaddress
import re
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

_TRACKING = {"fbclid", "gclid", "sessionid", "ref"}
_TRAP_PATH_PATTERNS = (
    re.compile(r"/(?:calendar|lich|event|events)(?:/|$)", re.IGNORECASE),
    re.compile(r"/(?:search|tim-kiem)(?:/|$)", re.IGNORECASE),
)
_TRAP_QUERY_KEYS = {"date", "day", "month", "calendar"}


class CrawlError(Exception):
    """A URL was refused or failed; the caller records it and leaves the index untouched."""


def canonicalize_url(url: str) -> str:
    """https, lowercase host, decoded-then-requoted path, no fragment/tracking/trailing slash."""
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise CrawlError(f"unsupported URL: {url!r}")
    try:
        port = parts.port
    except ValueError as exc:
        raise CrawlError(f"invalid port: {url!r}") from exc
    if port not in (None, 80, 443):
        raise CrawlError(f"non-standard port refused: {url!r}")
    segments: list[str] = []
    for segment in unquote(parts.path).split("/"):
        if not segment or segment == ".":
            continue
        if segment == "..":
            if segments:
                segments.pop()
            continue
        segments.append(segment)
    path = quote("/" + "/".join(segments), safe="/") or "/"
    if len(path) > 1:
        path = path.rstrip("/") or "/"
    query = urlencode(
        sorted(
            (k, v)
            for k, v in parse_qsl(parts.query)
            if not (k.lower().startswith("utm_") or k.lower() in _TRACKING)
        )
    )
    return urlunsplit(("https", parts.hostname.lower(), path, query, ""))


def is_spider_trap(url: str) -> bool:
    """Detect calendar loops, search queries, repetitive directory segments, and date queries."""
    parts = urlsplit(url)
    path = parts.path.lower()
    for pattern in _TRAP_PATH_PATTERNS:
        if pattern.search(path):
            return True
    if "calendar" in path:
        return True
    if "filter" in path:
        return True
    query_params = {k.lower(): v.lower() for k, v in parse_qsl(parts.query)}
    if query_params.get("task") == "search":
        return True
    if query_params.keys() & _TRAP_QUERY_KEYS or any(
        "filter" in key or "filter" in value for key, value in query_params.items()
    ):
        return True

    segments = [segment for segment in path.split("/") if segment]
    for width in range(1, len(segments) // 2 + 1):
        for start in range(len(segments) - 2 * width + 1):
            if segments[start : start + width] == segments[start + width : start + 2 * width]:
                return True
    return False


def is_private_host(host: str) -> bool:
    # shortcut: literal IPs and localhost only, no DNS lookup; hosts are an explicit allowlist,
    # so upgrade to resolving + checking addresses if wildcard hosts are ever allowed.
    if host == "localhost" or host.endswith(".localhost"):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return not ip.is_global
