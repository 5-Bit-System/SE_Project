"""Storage management for raw bytes, processed markdown, and metadata catalog."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import ValidationError

from app.hus.cleaning import slugify
from app.hus.models import HUSDocument, MajorCategory
from app.hus.provenance import RawArchive
from app.hus.urls import canonicalize_url


def _normalize_major(major: MajorCategory | str | None) -> str:
    if major is None:
        return MajorCategory.GENERAL.value
    if isinstance(major, MajorCategory):
        return major.value
    val = str(major).strip()
    try:
        return MajorCategory(val).value
    except ValueError:
        return val.lower() or MajorCategory.GENERAL.value


def _escape_yaml_str(val: str) -> str:
    return json.dumps(str(val), ensure_ascii=False)


class RawStorage:
    """Manages raw byte files (HTML and downloaded documents) idempotently."""

    def __init__(self, root: Path):
        self.root = root
        self.archive = RawArchive(root)
        self.html_dir = root / "raw" / "html"
        self.doc_dir = root / "raw" / "documents"
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.doc_dir.mkdir(parents=True, exist_ok=True)

    def save_raw_html(
        self,
        url: str,
        raw_bytes: bytes,
        major: MajorCategory | str = "general",
        title: str = "",
        *, document_id: str | None = None, fetched_at: str | None = None,
        content_type: str | None = "text/html",
    ) -> Path:
        major_str = _normalize_major(major)
        url_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
        if not title:
            path_stem = Path(urlsplit(url).path).stem
            title = path_stem if path_stem and path_stem not in ("/", "\\") else "document"

        slug = slugify(title) or "document"
        dest_dir = self.html_dir / major_str
        ref = self.archive.store(url, raw_bytes, dest_dir, f"{slug}--{url_hash}", "html",
                                 document_id=document_id, fetched_at=fetched_at,
                                 content_type=content_type)
        return self.archive.path_for(ref)

    def save_raw_document(
        self,
        url: str,
        raw_bytes: bytes,
        ext: str,
        major: MajorCategory | str = "general",
        title: str = "",
        *, document_id: str | None = None, fetched_at: str | None = None,
        content_type: str | None = None, kind: Literal["fetched", "local_import"] = "fetched",
        origin_locator: str | None = None,
    ) -> Path:
        clean_ext = ext.lower().lstrip(".") or "bin"
        major_str = _normalize_major(major)
        url_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]

        if not title:
            path_stem = Path(urlsplit(url).path).stem
            title = path_stem if path_stem and path_stem not in ("/", "\\") else "document"
        elif clean_ext and title.lower().endswith(f".{clean_ext}"):
            title = title[: -len(clean_ext) - 1]

        slug = slugify(title) or "document"
        dest_dir = self.doc_dir / major_str
        ref = self.archive.store(url, raw_bytes, dest_dir, f"{slug}--{url_hash}", clean_ext,
                                 document_id=document_id, fetched_at=fetched_at,
                                 content_type=content_type, kind=kind, origin_locator=origin_locator)
        return self.archive.path_for(ref)

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

    def get_document(self, document_id: str) -> HUSDocument | None:
        """Load validated metadata for discovery after an HTTP 304 response."""
        record = self.documents.get(document_id)
        if record is None:
            return None
        try:
            return HUSDocument.model_validate(record)
        except ValidationError:
            return None

    def refresh_discovery(self, document_id: str, doc: HUSDocument) -> bool:
        """Refresh links without rewriting unchanged Markdown; False requires a rebuild."""
        cached = self.get_document(document_id)
        if cached is None or cached.url != doc.url:
            return False
        self.documents[document_id]["links"] = list(doc.links)
        self.documents[document_id]["attachments"] = [item.model_dump() for item in doc.attachments]
        return True

    def link_attachment(self, parent_id: str, url: str, raw_path: str) -> None:
        record = self.documents.get(parent_id)
        if record:
            for attachment in record.get("attachments", []):
                if canonicalize_url(attachment["source_url"]) == canonicalize_url(url):
                    attachment["raw_path"] = raw_path

    def save_document(self, doc: HUSDocument) -> str:
        identity = canonicalize_url(doc.url)
        doc_id = doc.document_id or hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
        doc.document_id = doc_id

        major_str = _normalize_major(doc.major)
        slug = slugify(doc.title) or "document"

        # Write markdown content to disk
        dest_dir = self.doc_dir / major_str
        dest_dir.mkdir(parents=True, exist_ok=True)
        md_file = dest_dir / f"{slug}--{doc_id[:8]}.md"

        publisher_val = doc.publisher.value if hasattr(doc.publisher, "value") else str(doc.publisher)
        type_val = doc.document_type.value if hasattr(doc.document_type, "value") else str(doc.document_type)

        header = (
            "---\n"
            f"title: {_escape_yaml_str(doc.title)}\n"
            f"url: {_escape_yaml_str(doc.url)}\n"
            f"publisher: {_escape_yaml_str(publisher_val)}\n"
            f"type: {_escape_yaml_str(type_val)}\n"
            f"major: {_escape_yaml_str(major_str)}\n"
            "---\n\n"
        )
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
