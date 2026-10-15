"""Chunking and the JSON index. Writes are atomic; a failed crawl never edits existing entries."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import textwrap

from app.hus.models import HUSChunk, HUSDocument


def chunk_document(document: HUSDocument, max_chars: int = 1200) -> list[HUSChunk]:
    """Split at headings and size; ids depend on URL, position and text, so they are stable."""
    chunks: list[HUSChunk] = []
    heading: str | None = None
    buf: list[str] = []

    def flush() -> None:
        if not buf:
            return
        text = "\n".join(buf)
        digest = hashlib.sha256(f"{document.url}\n{len(chunks)}\n{text}".encode()).hexdigest()
        chunks.append(
            HUSChunk(
                chunk_id=digest[:16], url=document.url, title=document.title,
                heading=heading, text=text,
            )
        )
        buf.clear()

    for line in document.content.split("\n"):
        if line.startswith("#"):
            flush()
            heading = line.lstrip("# ").strip()
        for piece in textwrap.wrap(line, max_chars, break_long_words=False) or [line]:
            if buf and sum(len(b) + 1 for b in buf) + len(piece) > max_chars:
                flush()
            buf.append(piece)
    flush()
    return chunks


class HUSIndex:
    def __init__(self, path: Path, raw_dir: Path):
        self.path, self.raw_dir = path, raw_dir
        self.documents: dict[str, dict] = {}
        if path.exists():
            self.documents = json.loads(path.read_text(encoding="utf-8"))["documents"]

    def add(self, document: HUSDocument, raw: bytes) -> str:
        """Store raw bytes and upsert. Returns new / updated / unchanged / duplicate."""
        raw_name = f"{hashlib.sha1(document.url.encode()).hexdigest()[:12]}-"
        raw_name += f"{hashlib.sha256(raw).hexdigest()[:12]}.html"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        raw_file = self.raw_dir / raw_name
        if not raw_file.exists():  # never overwrite an earlier version of the original
            raw_file.write_bytes(raw)

        record = document.model_dump(exclude={"links"})
        record["raw_file"] = raw_name
        existing = self.documents.get(document.url)
        original = next(
            (
                url for url, d in self.documents.items()
                if url != document.url
                and d["content_hash"] == document.content_hash
                and not d.get("duplicate_of")
            ),
            None,
        )
        if original:
            record.update(duplicate_of=original, chunks=[], version=1, history=[])
            status = "duplicate"
        elif existing and existing["content_hash"] == document.content_hash:
            record = {**existing, "fetched_at": document.fetched_at}
            status = "unchanged"
        else:
            record["chunks"] = [c.model_dump() for c in chunk_document(document)]
            record["version"] = existing["version"] + 1 if existing else 1
            record["history"] = (
                existing["history"]
                + [{"content_hash": existing["content_hash"], "fetched_at": existing["fetched_at"]}]
                if existing else []
            )
            status = "updated" if existing else "new"
        self.documents[document.url] = record
        return status

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        payload = {"documents": self.documents}
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8"
        )
        os.replace(tmp, self.path)