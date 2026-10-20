"""Allowlist and scope filtering engine for HUS crawler."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from app.hus.models import AllowlistSourceConfig
from app.hus.urls import CrawlError, canonicalize_url, is_private_host, is_spider_trap


def _prefix(path: str) -> str:
    return quote(unquote(path), safe="/")


def _matches_prefix(path: str, prefix: str) -> bool:
    prefix = prefix.rstrip("/") or "/"
    p_lower, pref_lower = path.lower(), prefix.lower()
    return pref_lower == "/" or p_lower == pref_lower or p_lower.startswith(pref_lower + "/")


class Allowlist:
    """Rules engine for hosts, approved path prefixes, and explicit exclusions."""

    def __init__(
        self,
        sources: list[dict] | tuple = (),
        *,
        excluded_hosts: list[str] | tuple = (),
        user_agent: str = "HUSCrawler/0.1",
        max_pages: int = 200,
        max_depth: int = 3,
        delay_seconds: float = 2.0,
        retry_attempts: int = 3,
    ):
        if max_pages < 1 or max_depth < 0 or delay_seconds < 0 or retry_attempts < 1:
            raise ValueError("max_pages/retries must be positive; depth/delay must be non-negative")
        self.sources = [
            AllowlistSourceConfig.model_validate(source).model_dump() for source in sources
        ]
        self.excluded_hosts = {h.lower() for h in excluded_hosts}
        self.user_agent = user_agent
        self.max_pages, self.max_depth = max_pages, max_depth
        self.delay_seconds, self.retry_attempts = delay_seconds, retry_attempts

        self.rules: dict[str, tuple[str, ...]] = {}
        self.exclusions: dict[str, tuple[str, ...]] = {}

        for source in self.sources:
            host = source["host"].lower()
            prefixes = tuple(_prefix(p) for p in source.get("path_prefixes", []))
            self.rules[host] = self.rules.get(host, ()) + prefixes

            exc = tuple(_prefix(p) for p in source.get("exclude_prefixes", []))
            self.exclusions[host] = self.exclusions.get(host, ()) + exc

        self.seeds = [seed for source in self.sources for seed in source.get("seeds", [])]
        for seed in self.seeds:
            check_allowed(seed, self)

    @classmethod
    def load(cls, path: Path) -> Allowlist:
        data = json.loads(path.read_text(encoding="utf-8"))
        sources = data.pop("sources", [])
        return cls(sources, **data)


def check_allowed(url: str, allowlist: Allowlist) -> str:
    """Return the canonical URL, or raise CrawlError if outside scope or in exclusion."""
    canonical = canonicalize_url(url)
    if is_spider_trap(canonical):
        raise CrawlError(f"spider trap rejected: {canonical}")

    parts = urlsplit(canonical)
    host = (parts.hostname or "").lower()

    if is_private_host(host):
        raise CrawlError(f"private/local address refused: {canonical}")

    if host in allowlist.excluded_hosts:
        raise CrawlError(f"excluded faculty host: {canonical}")

    prefixes = allowlist.rules.get(host)
    if prefixes is None or not any(_matches_prefix(parts.path, prefix) for prefix in prefixes):
        raise CrawlError(f"outside allowlist: {canonical}")

    exc_prefixes = allowlist.exclusions.get(host, ())
    if exc_prefixes and any(_matches_prefix(parts.path, prefix) for prefix in exc_prefixes):
        raise CrawlError(f"excluded path prefix: {canonical}")

    return canonical
