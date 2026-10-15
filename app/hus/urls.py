from __future__ import annotations

import ipaddress
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit

_TRACKING = ("utm_", "fbclid", "gclid")


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
    path = quote(unquote(parts.path), safe="/") or "/"
    if len(path) > 1:
        path = path.rstrip("/") or "/"
    query = urlencode(
        sorted((k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith(_TRACKING))
    )
    return urlunsplit(("https", parts.hostname.lower(), path, query, ""))


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