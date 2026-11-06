"""Crawl state management for incremental updates and change detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.hus.models import CrawlRecord
from app.hus.urls import canonicalize_url


class CrawlStateManager:
    """Tracks URL crawl timestamps, ETag, Last-Modified, and content hashes."""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.records: dict[str, CrawlRecord] = {}
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                for url, r_dict in data.get("records", {}).items():
                    self.records[canonicalize_url(url)] = CrawlRecord(**r_dict)
            except Exception:
                self.records = {}

    def get_record(self, url: str) -> CrawlRecord | None:
        """Find a record by stable identity without changing its effective source URL."""
        record = self.records.get(canonicalize_url(url))
        if record and canonicalize_url(record.url) == canonicalize_url(url):
            return record
        return None

    def get_request_headers(self, url: str) -> dict[str, str]:
        """Return conditional HTTP headers (If-None-Match, If-Modified-Since) if cached."""
        headers = {}
        record = self.get_record(url)
        if record and canonicalize_url(record.url, preserve_scheme=True) == canonicalize_url(
            url, preserve_scheme=True,
        ):
            if record.etag:
                headers["If-None-Match"] = record.etag
            if record.last_modified:
                headers["If-Modified-Since"] = record.last_modified
        return headers

    def should_process(self, url: str, new_hash: str, status_code: int = 200) -> tuple[bool, str]:
        """Determine whether content needs re-processing.

        Returns:
            (should_process: bool, reason: str)
            reasons: 'unchanged_not_modified', 'unchanged_content_match', 'updated', 'new'
        """
        if status_code == 304:
            return False, "unchanged_not_modified"

        record = self.get_record(url)
        if not record:
            return True, "new"

        if record.content_hash == new_hash:
            return False, "unchanged_content_match"

        return True, "updated"

    def update_record(
        self,
        url: str,
        content_hash: str,
        last_crawled: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        status_code: int = 200,
        document_id: Optional[str] = None,
    ) -> None:
        """Update or insert crawl record for url."""
        self.records[canonicalize_url(url)] = CrawlRecord(
            url=url,
            content_hash=content_hash,
            etag=etag,
            last_modified=last_modified,
            last_crawled=last_crawled,
            status_code=status_code,
            document_id=document_id,
        )

    def save(self) -> None:
        """Atomically persist crawl state to JSON."""
        tmp_path = self.state_file.with_suffix(".tmp")
        payload = {
            "version": "1.0",
            "url_count": len(self.records),
            "records": {url: rec.model_dump() for url, rec in self.records.items()},
        }
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.state_file)
