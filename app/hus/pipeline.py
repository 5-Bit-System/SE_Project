"""End-to-end crawling and extraction pipeline orchestrator."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import time
from urllib.parse import urlsplit

import httpx

from app.hus.allowlist import Allowlist, check_allowed
from app.hus.cleaning import infer_attachment_major, infer_document_type, infer_major
from app.hus.crawler import Robots, fetch_attachment, fetch_html
from app.hus.extractors import extract_attachment
from app.hus.extractors.html import extract_html
from app.hus.models import DocumentStatus, HUSDocument
from app.hus.state import CrawlStateManager
from app.hus.storage import ProcessedStorage, RawStorage
from app.hus.urls import CrawlError, canonicalize_url


@dataclass
class CrawlSummary:
    """Summary statistics returned after a crawl run."""

    new_count: int = 0
    updated_count: int = 0
    unchanged_count: int = 0
    attachment_count: int = 0
    error_count: int = 0
    failures: dict[str, str] = field(default_factory=dict)
    skipped_attachment_count: int = 0
    skipped_attachments: dict[str, str] = field(default_factory=dict)


class HUSPipeline:
    """Orchestrates discovery, fetching, extraction, state check, and storage."""

    def __init__(
        self,
        allowlist: Allowlist,
        raw_storage: RawStorage,
        processed_storage: ProcessedStorage,
        state_manager: CrawlStateManager,
    ):
        self.allowlist = allowlist
        self.raw_storage = raw_storage
        self.processed_storage = processed_storage
        self.state_manager = state_manager

    def run(
        self,
        *,
        client: httpx.Client | None = None,
        sleep=None,
        max_pages: int | None = None,
        max_depth: int | None = None,
        delay_seconds: float | None = None,
        incremental: bool = True,
    ) -> CrawlSummary:
        """Run breadth-first crawl and extraction pipeline."""
        limit = self.allowlist.max_pages if max_pages is None else max_pages
        depth_limit = self.allowlist.max_depth if max_depth is None else max_depth
        delay = self.allowlist.delay_seconds if delay_seconds is None else delay_seconds
        sleep_fn = sleep if sleep is not None else time.sleep

        summary = CrawlSummary()
        queue: deque[tuple[str, int]] = deque((seed, 0) for seed in self.allowlist.seeds)
        seen_urls: set[str] = set()
        seen_attachments: set[str] = set()
        pages_processed = 0

        # Own client if not provided
        client_context = None
        if client is None:
            client_context = httpx.Client(
                timeout=30.0, headers={"User-Agent": self.allowlist.user_agent},
            )
            http_client = client_context
        else:
            http_client = client

        try:
            robots = Robots(
                http_client, self.allowlist.user_agent, delay_seconds=delay, sleep=sleep_fn,
            )

            while queue and pages_processed < limit:
                raw_url, depth = queue.popleft()
                try:
                    url = check_allowed(raw_url, self.allowlist)
                except CrawlError as exc:
                    summary.failures[raw_url] = str(exc)
                    summary.error_count += 1
                    continue

                if url in seen_urls:
                    continue
                seen_urls.add(url)

                fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
                previous = self.state_manager.get_record(url) if incremental else None
                request_url = previous.url if previous else url
                headers = self.state_manager.get_request_headers(request_url) if incremental else {}

                try:
                    final_url, resp_headers, raw_bytes = fetch_html(
                        request_url,
                        self.allowlist,
                        http_client,
                        robots,
                        sleep=sleep_fn,
                        headers=headers,
                    )
                except CrawlError as exc:
                    summary.failures[url] = str(exc)
                    summary.error_count += 1
                    continue

                seen_urls.add(canonicalize_url(final_url))

                # A 304 skips re-extraction, but must not skip child discovery.
                not_modified = not raw_bytes
                if not_modified:
                    record = self.state_manager.get_record(final_url)
                    document_id = record.document_id if record else None
                    identity = canonicalize_url(final_url)
                    document_id = document_id or hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
                    doc = self.processed_storage.get_document(document_id)
                    if doc is None or doc.url != final_url:
                        # State may outlive its catalog entry. Rebuild it once without validators.
                        try:
                            final_url, resp_headers, raw_bytes = fetch_html(
                                final_url, self.allowlist, http_client, robots,
                                sleep=sleep_fn, headers={},
                            )
                            if not raw_bytes:
                                raise CrawlError(
                                    f"not modified response without a usable cached document: {final_url}"
                                )
                        except CrawlError as exc:
                            summary.failures[final_url] = str(exc)
                            summary.error_count += 1
                            continue
                        seen_urls.add(canonicalize_url(final_url))
                        not_modified = False

                if not_modified:
                    attachment_urls = [attachment.source_url for attachment in doc.attachments]
                    summary.unchanged_count += 1
                else:
                    # Parse HTML document and discovered attachment links.
                    try:
                        doc, attachment_urls = extract_html(raw_bytes, final_url, fetched_at)
                        doc.document_type = infer_document_type(doc.title, doc.content)
                        doc.major = infer_major(doc.title, final_url, doc.content)
                    except CrawlError as exc:
                        summary.failures[final_url] = str(exc)
                        summary.error_count += 1
                        continue

                    should_proc, reason = True, "new"
                    if incremental:
                        should_proc, reason = self.state_manager.should_process(
                            final_url, doc.content_hash, status_code=200
                        )
                    if not should_proc:
                        record = self.state_manager.get_record(final_url)
                        document_id = record.document_id if record else None
                        identity = canonicalize_url(final_url)
                        document_id = document_id or hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
                        if not self.processed_storage.refresh_discovery(document_id, doc):
                            should_proc, reason = True, "updated"

                    if not should_proc:
                        summary.unchanged_count += 1
                    else:
                        # Save raw HTML and processed markdown document.
                        self.raw_storage.save_raw_html(final_url, raw_bytes, major=doc.major, title=doc.title)
                        doc_id = self.processed_storage.save_document(doc)
                        self.state_manager.update_record(
                            url=final_url,
                            content_hash=doc.content_hash,
                            last_crawled=fetched_at,
                            etag=resp_headers.get("etag"),
                            last_modified=resp_headers.get("last-modified"),
                            status_code=200,
                            document_id=doc_id,
                        )
                        if reason == "new":
                            summary.new_count += 1
                        else:
                            summary.updated_count += 1

                pages_processed += 1

                # Enqueue child page links if within depth limit
                if depth < depth_limit:
                    for link in doc.links:
                        try:
                            clean_link = check_allowed(link, self.allowlist)
                            if clean_link not in seen_urls:
                                queue.append((clean_link, depth + 1))
                        except CrawlError:
                            pass

                # Process discovered attachments linked in this document
                for att_url in attachment_urls:
                    if att_url in seen_attachments:
                        continue
                    seen_attachments.add(att_url)

                    try:
                        clean_att_url = check_allowed(att_url, self.allowlist)
                    except CrawlError as exc:
                        summary.skipped_attachment_count += 1
                        summary.skipped_attachments[att_url] = str(exc)
                        continue

                    previous_attachment = (
                        self.state_manager.get_record(clean_att_url) if incremental else None
                    )
                    att_request_url = previous_attachment.url if previous_attachment else clean_att_url
                    att_headers = self.state_manager.get_request_headers(att_request_url) if incremental else {}
                    try:
                        att_final, att_resp_headers, att_raw = fetch_attachment(
                            att_request_url,
                            self.allowlist,
                            http_client,
                            robots,
                            sleep=sleep_fn,
                            headers=att_headers,
                        )
                    except CrawlError as exc:
                        summary.failures[clean_att_url] = str(exc)
                        summary.error_count += 1
                        continue

                    if not att_raw:
                        # 304 Not Modified for attachment
                        continue

                    ext = urlsplit(att_final).path.split(".")[-1].lower() if "." in att_final else "bin"
                    att_filename = Path(urlsplit(att_final).path).name or "attachment"

                    # Extract attachment content
                    try:
                        att_content, needs_ocr = extract_attachment(att_raw, ext)
                    except CrawlError as exc:
                        att_major = infer_attachment_major(att_final, parent_major=doc.major)
                        self.raw_storage.save_raw_document(
                            att_final, att_raw, ext, major=att_major, title=att_filename
                        )
                        summary.failures[att_final] = str(exc)
                        summary.error_count += 1
                        continue

                    att_status = DocumentStatus.PENDING_OCR if needs_ocr else DocumentStatus.ACTIVE
                    cleaned_content = att_content.strip() if att_content else f"[Tài liệu đính kèm: {att_final}]"
                    att_hash = hashlib.sha256(cleaned_content.encode("utf-8")).hexdigest()

                    att_major = infer_attachment_major(
                        att_final, cleaned_content, parent_major=doc.major,
                    )
                    self.raw_storage.save_raw_document(
                        att_final, att_raw, ext, major=att_major, title=att_filename
                    )

                    att_doc = HUSDocument(
                        url=att_final,
                        parent_url=final_url,
                        title=f"Tài liệu đính kèm: {att_filename}",
                        content=cleaned_content,
                        content_hash=att_hash,
                        fetched_at=fetched_at,
                        document_type=infer_document_type(att_filename, cleaned_content),
                        publisher=doc.publisher,
                        major=att_major,
                        status=att_status,
                    )
                    att_doc_id = self.processed_storage.save_document(att_doc)
                    self.state_manager.update_record(
                        url=att_final,
                        content_hash=att_hash,
                        last_crawled=fetched_at,
                        etag=att_resp_headers.get("etag"),
                        last_modified=att_resp_headers.get("last-modified"),
                        status_code=200,
                        document_id=att_doc_id,
                    )
                    summary.attachment_count += 1

            # Persist state and catalog atomically at the end of run
            self.processed_storage.commit()
            self.state_manager.save()

        finally:
            if client_context is not None:
                client_context.close()

        return summary
