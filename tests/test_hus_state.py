import json
from pathlib import Path
import pytest

from app.hus.state import CrawlStateManager


def test_crawl_state_manager_lifecycle(tmp_path: Path):
    state_file = tmp_path / "state" / "crawl_state.json"
    manager = CrawlStateManager(state_file)

    url = "https://mim.hus.vnu.edu.vn/vi/dao-tao"

    # Initially new
    should_proc, reason = manager.should_process(url, new_hash="hash_v1")
    assert should_proc is True
    assert reason == "new"

    # Update record with ETag
    manager.update_record(
        url=url,
        content_hash="hash_v1",
        last_crawled="2026-10-16T09:00:00Z",
        etag='"etag123"',
        document_id="doc-1",
    )
    manager.save()

    assert state_file.exists()
    headers = manager.get_request_headers(url)
    assert headers["If-None-Match"] == '"etag123"'

    # 304 Not Modified
    should_proc, reason = manager.should_process(url, new_hash="ignored", status_code=304)
    assert should_proc is False
    assert reason == "unchanged_not_modified"

    # Unchanged content hash
    should_proc, reason = manager.should_process(url, new_hash="hash_v1", status_code=200)
    assert should_proc is False
    assert reason == "unchanged_content_match"

    # Content changed
    should_proc, reason = manager.should_process(url, new_hash="hash_v2", status_code=200)
    assert should_proc is True
    assert reason == "updated"

    # Reload from disk
    reloaded = CrawlStateManager(state_file)
    assert url in reloaded.records
    assert reloaded.records[url].content_hash == "hash_v1"
