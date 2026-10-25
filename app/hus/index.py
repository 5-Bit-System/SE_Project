"""Review-gated chunking and JSON index. Stored approvals are never trusted on reload."""

from __future__ import annotations

import hashlib
from datetime import date
import json
import os
from pathlib import Path
import textwrap

from app.hus.models import HUSChunk, HUSDocument, ReviewDecision
from app.hus.metadata import metadata_for
from app.hus.review import ReviewGateError, require_review, source_digest
from app.hus.urls import canonicalize_url


def chunk_document(
    document: HUSDocument, max_chars: int = 1200, *, review: ReviewDecision | None = None,
    raw: bytes | None = None, as_of: date | None = None,
) -> list[HUSChunk]:
    """Split at headings and size; ids depend on URL, position and text, so they are stable."""
    review = require_review(
        document, review,
        source_digest(raw, review.source_checksum_encoding) if raw is not None and review else None,
        source_encoding=review.source_checksum_encoding if review else "binary", as_of=as_of,
    )
    applicability = metadata_for(document)
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    chunks: list[HUSChunk] = []
    heading: str | None = None
    buf: list[str] = []

    def flush() -> None:
        if not buf:
            return
        text = "\n".join(buf)
        identity = canonicalize_url(document.url)
        digest = hashlib.sha256(f"{identity}\n{len(chunks)}\n{text}".encode()).hexdigest()
        chunks.append(
            HUSChunk(
                chunk_id=digest[:16], url=document.url, title=document.title,
                heading=heading, text=text, review_status="include", review=review,
                review_as_of=as_of.isoformat() if as_of else None,
                applicability=applicability,
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
    def __init__(
        self, path: Path, raw_dir: Path, *, reviews: dict[str, ReviewDecision] | None = None,
        as_of: date | None = None,
    ):
        self.path, self.raw_dir = path, raw_dir
        self.reviews = reviews if reviews is not None else {}
        self.as_of = as_of
        self.documents: dict[str, dict] = {}
        if path.exists():
            self.documents = json.loads(path.read_text(encoding="utf-8"))["documents"]
        self._refresh_approved()

    def _review_for(self, document: HUSDocument) -> ReviewDecision | None:
        """Index callers supply current decisions keyed by canonical URL, not cached metadata."""
        identity = canonicalize_url(document.url)
        return self.reviews.get(identity)

    def _refresh_approved(self) -> None:
        """Remove revoked/stale records and rebuild cached chunks before reading or saving."""
        approved = {}
        for identity, record in self.documents.items():
            try:
                doc = HUSDocument.model_validate({
                    key: value for key, value in record.items() if key in HUSDocument.model_fields
                })
                if identity != canonicalize_url(doc.url):
                    raise ReviewGateError("Index identity does not match document")
                raw_path = self.raw_dir / record["raw_file"]
                if not raw_path.resolve().is_relative_to(self.raw_dir.resolve()):
                    raise ReviewGateError("Raw file escapes index source directory")
                chunks = chunk_document(
                    doc, review=self._review_for(doc), raw=raw_path.read_bytes(), as_of=self.as_of,
                )
                approved[identity] = {
                    **record, "review_status": "include",
                    "review": chunks[0].review.model_dump(),
                    "review_as_of": chunks[0].review_as_of,
                    "applicability": chunks[0].applicability.model_dump(),
                    "major": chunks[0].applicability.major.verified,
                    "proposed_major": chunks[0].applicability.major.proposed,
                    "chunks": [chunk.model_dump() for chunk in chunks],
                }
            except (ValueError, OSError, KeyError):
                continue
        for record in approved.values():
            if record.get("duplicate_of") in approved:
                record["chunks"] = []
            else:
                record.pop("duplicate_of", None)
        self.documents = approved

    def add(
        self, document: HUSDocument, raw: bytes, *, review: ReviewDecision | None = None,
    ) -> str:
        """Store raw bytes and upsert. Returns new / updated / unchanged / duplicate."""
        identity = canonicalize_url(document.url)
        self._refresh_approved()
        if review is not None:
            self.reviews[identity] = review
        try:
            chunks = chunk_document(
                document, review=self._review_for(document), raw=raw, as_of=self.as_of,
            )
        except ValueError:
            self.documents.pop(identity, None)
            raise
        raw_name = f"{hashlib.sha1(document.url.encode()).hexdigest()[:12]}-"
        raw_name += f"{hashlib.sha256(raw).hexdigest()[:12]}.html"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        raw_file = self.raw_dir / raw_name
        if not raw_file.exists():  # never overwrite an earlier version of the original
            raw_file.write_bytes(raw)

        record = document.model_dump(exclude={"links"})
        record["raw_file"] = raw_name
        record.update(review_status="include", review=chunks[0].review.model_dump(),
                      review_as_of=chunks[0].review_as_of,
                      applicability=chunks[0].applicability.model_dump(),
                      legacy_crawler_major=document.major.value,
                      major=chunks[0].applicability.major.verified,
                      proposed_major=chunks[0].applicability.major.proposed)
        existing = self.documents.get(identity)
        original = next(
            (
                url for url, d in self.documents.items()
                if url != identity
                and d["content_hash"] == document.content_hash
                and not d.get("duplicate_of")
            ),
            None,
        )
        if original:
            record.update(duplicate_of=original, chunks=[], version=1, history=[])
            status = "duplicate"
        elif existing and existing["content_hash"] == document.content_hash:
            record = {**existing, **record, "chunks": [c.model_dump() for c in chunks]}
            status = "unchanged"
        else:
            record["chunks"] = [c.model_dump() for c in chunks]
            record["version"] = existing["version"] + 1 if existing else 1
            record["history"] = (
                existing["history"]
                + [{"content_hash": existing["content_hash"], "fetched_at": existing["fetched_at"]}]
                if existing else []
            )
            status = "updated" if existing else "new"
        self.documents[identity] = record
        return status

    def save(self) -> None:
        self._refresh_approved()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        payload = {"documents": self.documents}
        tmp.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8"
        )
        os.replace(tmp, self.path)
