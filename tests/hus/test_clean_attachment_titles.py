"""Tests for tools/clean_attachment_titles.py."""

from __future__ import annotations

import json
from pathlib import Path

from app.hus.models import HUSDocument
from app.hus.storage import ProcessedStorage
from tools.clean_attachment_titles import clean_attachment_titles


def test_clean_attachment_titles(tmp_path: Path) -> None:
    storage = ProcessedStorage(tmp_path)
    doc = HUSDocument(
        url="https://mim.hus.vnu.edu.vn/sites/default/files/4.%20KCT%C4%90T-CLC%20MTKHTT%2010082020_0.pdf",
        title="Tài liệu đính kèm: 4.%20KCT%C4%90T-CLC%20MTKHTT%2010082020_0.pdf",
        content="Test attachment content",
        content_hash="dummyhash123",
        fetched_at="2026-10-24T00:00:00+00:00",
        major="computer_science",
    )
    doc_id = storage.save_document(doc)
    storage.commit()

    old_files = list(storage.doc_dir.glob("*/*.md"))
    assert len(old_files) == 1
    assert "-20kct-c4-90t" in old_files[0].name

    # Dry run should not modify files on disk
    count, ids = clean_attachment_titles(tmp_path, dry_run=True)
    assert count == 1
    assert ids == [doc_id]
    files_after_dry_run = list(storage.doc_dir.glob("*/*.md"))
    assert len(files_after_dry_run) == 1
    assert "-20kct-c4-90t" in files_after_dry_run[0].name

    # Real run
    count, ids = clean_attachment_titles(tmp_path, dry_run=False)
    assert count == 1
    assert ids == [doc_id]

    # Verify catalog updated
    catalog = json.loads((tmp_path / "processed" / "catalog.json").read_text(encoding="utf-8"))
    updated_doc = catalog["documents"][doc_id]
    assert updated_doc["title"] == "Tài liệu đính kèm: 4. KCTĐT-CLC MTKHTT 10082020_0.pdf"
    assert "%20" not in updated_doc["title"]
    assert "%C4" not in updated_doc["title"]

    # Verify markdown file renamed and old file deleted
    new_files = list(storage.doc_dir.glob("*/*.md"))
    assert len(new_files) == 1
    assert "4-kctdt-clc-mtkhtt" in new_files[0].name
    assert "-20kct-c4-90t" not in new_files[0].name

    # Re-running on already cleaned storage changes nothing
    count2, ids2 = clean_attachment_titles(tmp_path, dry_run=False)
    assert count2 == 0
    assert ids2 == []
