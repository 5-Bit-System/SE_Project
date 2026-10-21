"""Tests for CLI runner tools/run_hus_crawler.py."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import httpx
import pytest

from tools.run_hus_crawler import main

_MINIMAL_CONFIG = {
    "user_agent": "HUSCrawler/0.1",
    "max_pages": 5,
    "max_depth": 2,
    "delay_seconds": 0.0,
    "retry_attempts": 1,
    "sources": [
        {
            "host": "mim.hus.vnu.edu.vn",
            "path_prefixes": ["/vi/"],
            "exclude_prefixes": [],
            "seeds": ["https://mim.hus.vnu.edu.vn/vi/dao-tao"],
        }
    ],
    "excluded_hosts": ["chem.hus.vnu.edu.vn"],
}


def test_cli_dry_run_prints_rules_and_exits_zero(tmp_path: Path, capsys) -> None:
    config_file = tmp_path / "sources.json"
    config_file.write_text(json.dumps(_MINIMAL_CONFIG), encoding="utf-8")

    exit_code = main(["--config", str(config_file), "--dry-run"])
    assert exit_code == 0

    captured = capsys.readouterr().out
    assert "DRY-RUN MODE" in captured
    assert "mim.hus.vnu.edu.vn" in captured
    assert "chem.hus.vnu.edu.vn" in captured
    assert "https://mim.hus.vnu.edu.vn/vi/dao-tao" in captured


def test_cli_dry_run_missing_config_returns_error(capsys) -> None:
    exit_code = main(["--config", "nonexistent_config_file_12345.json", "--dry-run"])
    assert exit_code != 0
    captured = capsys.readouterr().err
    assert "not found" in captured.lower() or "error" in captured.lower()


def test_cli_normal_run_with_mocked_network(tmp_path: Path, monkeypatch) -> None:
    config_file = tmp_path / "sources.json"
    config_file.write_text(json.dumps(_MINIMAL_CONFIG), encoding="utf-8")
    out_dir = tmp_path / "data_out"

    html_bytes = b"""<!DOCTYPE html><html><head><title>Test</title></head>
<body><article><h1>Bai viet</h1><p>Noi dung day du.</p></article></body></html>"""

    def mock_transport(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, content=b"User-agent: *\nAllow: /\n")
        if request.url.path == "/vi/dao-tao":
            return httpx.Response(200, content=html_bytes, headers={"content-type": "text/html"})
        return httpx.Response(404)

    # Patch httpx.Client in pipeline to use mock transport
    original_client_init = httpx.Client.__init__

    def patched_init(self, *args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(mock_transport)
        original_client_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "__init__", patched_init)

    exit_code = main(["--config", str(config_file), "--out", str(out_dir), "--max-pages", "2"])
    assert exit_code == 0

    # Verify directories and catalog created
    catalog_path = out_dir / "processed" / "catalog.json"
    assert catalog_path.exists()
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert data["document_count"] >= 1


def test_cli_reports_skipped_attachments_with_url_and_reason(tmp_path, monkeypatch, capsys):
    config_file = tmp_path / "sources.json"
    config_file.write_text(json.dumps(_MINIMAL_CONFIG), encoding="utf-8")
    blocked_url = "https://chem.hus.vnu.edu.vn/files/rules.pdf"

    def handler(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /\n")
        assert str(request.url) == _MINIMAL_CONFIG["sources"][0]["seeds"][0]
        return httpx.Response(200, text='<main><h1>Notice</h1>'
                              f'<a href="{blocked_url}">Rules</a></main>',
                              headers={"content-type": "text/html"})

    original_init = httpx.Client.__init__

    def patched_init(self, *args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "__init__", patched_init)
    assert main(["--config", str(config_file), "--out", str(tmp_path / "out")]) == 0
    output = capsys.readouterr().out
    assert "Attachments skipped  : 1" in output
    assert "[Skipped Attachments Detail]" in output
    assert blocked_url in output
    assert "excluded faculty host" in output
    assert "Errors encountered   : 0" in output
