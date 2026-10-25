"""Immutable raw versions and an append-only log of capture/recovery attempts.

The ledger is local acquisition state, not an approval or a substitute for a pinned manifest.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from app.hus.models import RawSourceReference
from app.hus.urls import CrawlError, canonicalize_url


class CaptureEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str
    document_id: str
    source_url: str
    observed_at: str
    kind: Literal["fetched", "not_modified", "local_import", "failed"]
    reference: RawSourceReference | None = None
    reason: str | None = None
    origin_locator: str | None = None


def document_id_for(url: str) -> str:
    return hashlib.sha256(canonicalize_url(url).encode()).hexdigest()[:16]


class RawArchive:
    def __init__(self, root: Path):
        self.root = root
        self.ledger_path = root / "raw/provenance.jsonl"

    def events(self) -> list[CaptureEvent]:
        if not self.ledger_path.exists():
            return []
        try:
            return [CaptureEvent.model_validate(json.loads(line)) for line in
                    self.ledger_path.read_text(encoding="utf-8").splitlines() if line]
        except ValueError as exc:
            raise CrawlError("Invalid raw provenance ledger; refusing to discard history") from exc

    def _append(self, event: CaptureEvent) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        # Validate existing history before appending; never silently replace a broken ledger.
        self.events()
        with self.ledger_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event.model_dump(), ensure_ascii=False, sort_keys=True) + "\n")

    def path_for(self, reference: RawSourceReference) -> Path:
        relative = Path(reference.raw_path)
        path = self.root / relative
        if relative.is_absolute() or ".." in relative.parts or not path.resolve().is_relative_to(
            self.root.resolve()
        ):
            raise CrawlError("Raw provenance path escapes source root")
        return path

    def latest(self, url: str) -> RawSourceReference | None:
        """Never use an older version when the latest known version has disappeared."""
        identity = canonicalize_url(url)
        for event in reversed(self.events()):
            if canonicalize_url(event.source_url) != identity or event.reference is None:
                continue
            ref = event.reference
            path = self.path_for(ref)
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != ref.raw_sha256:
                return None
            return ref
        return None

    def store(
        self, url: str, raw: bytes, directory: Path, filename_prefix: str, ext: str,
        *, document_id: str | None = None, fetched_at: str | None = None,
        content_type: str | None = None, kind: Literal["fetched", "local_import"] = "fetched",
        origin_locator: str | None = None,
    ) -> RawSourceReference:
        self.events()
        if not re.fullmatch(r"[a-z0-9]{1,10}", ext) or kind not in {"fetched", "local_import"}:
            raise CrawlError("Invalid raw file type or capture kind")
        digest = hashlib.sha256(raw).hexdigest()
        path = directory / f"{filename_prefix}--{digest}.{ext}"
        if not path.resolve().is_relative_to(self.root.resolve()):
            raise CrawlError("Raw output escapes source root")
        directory.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as stream:
                stream.write(raw)
        except FileExistsError:
            if path.read_bytes() != raw:
                raise CrawlError(f"Corrupted immutable raw version: {path.name}")
        observed_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        ref = RawSourceReference(
            capture_id=uuid4().hex, document_id=document_id or document_id_for(url), source_url=url,
            raw_path=path.relative_to(self.root).as_posix(), raw_sha256=digest, byte_size=len(raw),
            file_type=ext, content_type=content_type, observed_at=observed_at,
            fetched_at=(fetched_at or observed_at) if kind == "fetched" else None,
            version_status="captured" if kind == "fetched" else "unverified",
        )
        self._append(CaptureEvent(
            event_id=ref.capture_id, document_id=ref.document_id, source_url=url,
            observed_at=observed_at, kind=kind, reference=ref, origin_locator=origin_locator,
        ))
        return ref

    def record_not_modified(self, url: str, observed_at: str) -> RawSourceReference:
        ref = self.latest(url)
        if ref is None:
            raise CrawlError("304 without a usable raw version")
        self._append(CaptureEvent(event_id=uuid4().hex, document_id=ref.document_id,
                                 source_url=url, observed_at=observed_at,
                                 kind="not_modified", reference=ref))
        return ref

    def record_failure(self, url: str, reason: str) -> None:
        self._append(CaptureEvent(
            event_id=uuid4().hex, document_id=document_id_for(url), source_url=url,
            observed_at=datetime.now(timezone.utc).isoformat(timespec="microseconds"),
            kind="failed", reason=reason,
        ))
