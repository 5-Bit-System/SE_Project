"""Storage management for raw bytes, processed markdown, and metadata catalog."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from app.hus.models import HUSDocument


class RawStorage:
    """Manages raw byte files (HTML and downloaded documents) idempotently."""

    def __init__(self, root: Path):
        self.root = root
        self.html_dir = root / "raw" / "html"
        self.doc_dir = root / "raw" / "documents"
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.doc_dir.mkdir(parents=True, exist_ok=True)

    def save_raw_html(self, url: str, raw_bytes: bytes) -> Path:
        url_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        content_hash = hashlib.sha256(raw_bytes).hexdigest()[:12]
        filename = f"{url_hash}-{content_hash}.html"
        path = self.html_dir / filename
        if not path.exists():
            path.write_bytes(raw_bytes)
        return path

    def save_raw_document(self, url: str, raw_bytes: bytes, ext: str) -> Path:
        clean_ext = ext.lower().lstrip(".") or "bin"
        url_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        content_hash = hashlib.sha256(raw_bytes).hexdigest()[:12]
        filename = f"{url_hash}-{content_hash}.{clean_ext}"
        path = self.doc_dir / filename
        if not path.exists():
            path.write_bytes(raw_bytes)
        return path


class ProcessedStorage:
    """Manages processed markdown documents and atomic catalog.json index."""

    def __init__(self, root: Path):
        self.root = root
        self.doc_dir = root / "processed" / "documents"
        self.catalog_path = root / "processed" / "catalog.json"
        self.doc_dir.mkdir(parents=True, exist_ok=True)
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)
        self.documents: dict[str, dict] = {}
        if self.catalog_path.exists():
            try:
                data = json.loads(self.catalog_path.read_text(encoding="utf-8"))
                self.documents = data.get("documents", {})
            except Exception:
                self.documents = {}

    def save_document(self, doc: HUSDocument) -> str:
        doc_id = doc.document_id or hashlib.sha256(doc.url.encode("utf-8")).hexdigest()[:16]
        doc.document_id = doc_id

        # Write markdown content to disk
        md_file = self.doc_dir / f"{doc_id}.md"
        header = f"---\ntitle: {doc.title}\nurl: {doc.url}\npublisher: {doc.publisher.value}\ntype: {doc.document_type.value}\n---\n\n"
        md_file.write_text(header + doc.content, encoding="utf-8")

        # Update in-memory catalog
        self.documents[doc_id] = doc.model_dump()
        return doc_id

    def commit(self) -> None:
        """Atomically commit catalog.json using temporary file rename."""
        tmp_path = self.catalog_path.with_suffix(".tmp")
        payload = {
            "version": "1.0",
            "document_count": len(self.documents),
            "documents": self.documents,
        }
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.catalog_path)
