"""Offline, deterministic corpus preparation from an explicitly pinned crawl snapshot.

Repository text checksums use UTF-8 with LF line endings (Git/Windows portable).
They are not presented as checksums of the original HTTP response bytes.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import unicodedata
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.hus.models import HUSDocument, ReviewDecision
from app.hus.review import require_review
from app.hus.metadata import ApplicabilityFile, metadata_for, validate_metadata
from app.hus.quality import analyze_source, quality_digest

SCHEMA_VERSION = "1.0"
PIPELINE_VERSION = "1.4"
REVIEW_STATUSES = ("include", "needs_review", "pending_ocr", "exclude")


class CorpusError(ValueError):
    """An input or an existing build failed verification."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SourceFile(StrictModel):
    path: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    encoding: Literal["utf8-lf", "binary"]


class DocumentSource(StrictModel):
    source_url: str
    markdown_path: str
    raw_path: str | None
    source_kind: Literal["web", "attachment"]


class SourceManifest(StrictModel):
    schema_version: Literal["1.0"]
    source_snapshot_id: str = Field(min_length=1)
    source_location: str = Field(min_length=1)
    catalog_path: Literal["processed/catalog.json"]
    document_count: int = Field(ge=1)
    files: list[SourceFile]
    documents: dict[str, DocumentSource]


class ReviewFile(StrictModel):
    schema_version: Literal["1.0"]
    source_snapshot_id: str
    decisions: dict[str, ReviewDecision]


class BuildConfig(StrictModel):
    schema_version: Literal["1.0"]
    pipeline_version: Literal["1.4"]
    source_manifest: str
    review_decisions: str
    normalization: Literal["nfc-lf-trim-trailing-v1"]
    chunking: Literal["utf8-lines-v1"]
    max_chunk_bytes: int = Field(ge=128, le=16000)
    overlap_bytes: Literal[0]
    as_of: str | None = None
    applicability_metadata: str | None = None

    @field_validator("as_of")
    @classmethod
    def build_date(cls, value: str | None) -> str | None:
        return date.fromisoformat(value).isoformat() if value is not None else None


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def jsonl_bytes(rows: list[dict]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode() for row in rows
    )


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_path(root: Path, name: str) -> Path:
    """Reject traversal, Windows drive names, and symlinks escaping the input root."""
    relative = PurePosixPath(name)
    if (
        not name or "\\" in name or ":" in name or relative.is_absolute()
        or ".." in relative.parts or relative.as_posix() != name
    ):
        raise CorpusError(f"Unsafe source path: {name}")
    path = root.joinpath(*relative.parts)
    if not path.resolve().is_relative_to(root.resolve()):
        raise CorpusError(f"Source path escapes input root: {name}")
    return path


def file_bytes(path: Path, encoding: str) -> bytes:
    raw = path.read_bytes()
    if encoding == "utf8-lf":
        return raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode()
    return raw


def normalize(content: str) -> str:
    content = unicodedata.normalize("NFC", content.replace("\r\n", "\n").replace("\r", "\n"))
    return "\n".join(line.rstrip(" \t") for line in content.split("\n")).strip("\n") + "\n"


def load_catalog(root: Path) -> dict[str, HUSDocument]:
    data = read_json(root / "processed/catalog.json")
    if not isinstance(data, dict) or not isinstance(data.get("documents"), dict):
        raise CorpusError("Catalog must contain a documents object")
    documents = {
        key: HUSDocument.model_validate(value) for key, value in data["documents"].items()
    }
    if not documents or data.get("document_count") != len(documents):
        raise CorpusError("Catalog document_count does not match its documents")
    for key, doc in documents.items():
        if not re.fullmatch(r"[0-9a-f]{16}", key) or doc.document_id != key:
            raise CorpusError(f"Invalid document identity: {key}")
        if sha256(doc.content.encode()) != doc.content_hash:
            raise CorpusError(f"Catalog content hash mismatch: {key}")
    return documents


def create_source_manifest(root: Path, snapshot_id: str, location: str) -> SourceManifest:
    """Inventory only the files used by the catalog; never sweep unrelated local files."""
    documents = load_catalog(root)
    files = {"processed/catalog.json": "utf8-lf"}
    sources: dict[str, DocumentSource] = {}
    markdown_files = list((root / "processed/documents").rglob("*.md"))
    for key, doc in sorted(documents.items()):
        matches = [p for p in markdown_files if p.name.endswith(f"--{key[:8]}.md")]
        if len(matches) != 1:
            raise CorpusError(f"Expected one Markdown source for {key}; found {len(matches)}")
        markdown = matches[0].relative_to(root).as_posix()
        files[markdown] = "utf8-lf"
        extension = Path(urlsplit(doc.url).path).suffix.lower()
        attachment = extension in {".pdf", ".docx", ".xlsx", ".xls", ".doc"}
        raw_dir = root / "raw" / ("documents" if attachment else "html")
        url_hash = hashlib.sha1(doc.url.encode()).hexdigest()[:12]
        suffix = extension if attachment else ".html"
        if doc.raw_source:
            ref = doc.raw_source
            raw_file = source_path(root, ref.raw_path)
            if (ref.source_url != doc.url or ref.document_id != key
                or not raw_file.is_file() or sha256(raw_file.read_bytes()) != ref.raw_sha256):
                raise CorpusError(f"Raw provenance does not match document: {key}")
            raw_path = ref.raw_path
        else:
            raw_matches = list(raw_dir.rglob(f"*--{url_hash}{suffix}"))
            if len(raw_matches) > 1:
                raise CorpusError(f"Ambiguous raw source for {key}")
            raw_path = raw_matches[0].relative_to(root).as_posix() if raw_matches else None
        if raw_path:
            files[raw_path] = "binary" if attachment or doc.raw_source else "utf8-lf"
        sources[key] = DocumentSource(
            source_url=doc.url, markdown_path=markdown, raw_path=raw_path,
            source_kind="attachment" if attachment else "web",
        )
    return SourceManifest(
        schema_version=SCHEMA_VERSION, source_snapshot_id=snapshot_id,
        source_location=location, catalog_path="processed/catalog.json",
        document_count=len(documents), documents=sources,
        files=[SourceFile(path=name, sha256=sha256(file_bytes(source_path(root, name), encoding)),
                          encoding=encoding) for name, encoding in sorted(files.items())],
    )


def verify_sources(root: Path, manifest: SourceManifest) -> dict[str, HUSDocument]:
    names = [item.path for item in manifest.files]
    if len(names) != len(set(names)) or manifest.catalog_path not in names:
        raise CorpusError("Manifest contains duplicate paths or lacks the catalog")
    for item in manifest.files:
        path = source_path(root, item.path)
        if not path.is_file() or sha256(file_bytes(path, item.encoding)) != item.sha256:
            raise CorpusError(f"Missing or changed snapshot input: {item.path}")
    documents = load_catalog(root)
    if set(documents) != set(manifest.documents) or len(documents) != manifest.document_count:
        raise CorpusError("Manifest document IDs/count do not match catalog")
    expected_names = {manifest.catalog_path}
    file_index = {item.path: item for item in manifest.files}
    for key, doc in documents.items():
        source = manifest.documents[key]
        if source.source_url != doc.url:
            raise CorpusError(f"Source URL mismatch: {key}")
        if doc.raw_source:
            ref = doc.raw_source
            raw_file = file_index.get(ref.raw_path)
            if (ref.document_id != key or ref.source_url != doc.url
                or source.raw_path != ref.raw_path or raw_file is None
                or raw_file.encoding != "binary" or raw_file.sha256 != ref.raw_sha256):
                raise CorpusError(f"Raw capture reference mismatch: {key}")
        expected_names.add(source.markdown_path)
        if source.raw_path:
            expected_names.add(source.raw_path)
        if not source.markdown_path.startswith("processed/documents/"):
            raise CorpusError(f"Invalid Markdown path: {key}")
        md = source_path(root, source.markdown_path).read_text(encoding="utf-8")
        parts = md.split("---\n", 2)
        if not md.startswith("---\n") or len(parts) != 3 or parts[2].lstrip("\n") != doc.content:
            raise CorpusError(f"Markdown body does not match catalog: {key}")
    if expected_names != set(names):
        raise CorpusError("Manifest file inventory does not match document sources")
    return documents


def initial_reviews(root: Path, manifest: SourceManifest) -> ReviewFile:
    return ReviewFile(
        schema_version=SCHEMA_VERSION, source_snapshot_id=manifest.source_snapshot_id,
        decisions={key: ReviewDecision(
            content_hash=doc.content_hash, source_url=doc.url,
            status="pending_ocr" if doc.status.value == "pending_ocr" else "needs_review",
            reason="Awaiting source extraction/OCR review" if doc.status.value == "pending_ocr"
            else "Awaiting source comparison and applicability review; not imported from build07",
        ) for key, doc in sorted(verify_sources(root, manifest).items())},
    )


def split_chunks(text: str, limit: int) -> list[tuple[int, int]]:
    """Contiguous, lossless character spans; prefer lines, split oversized lines by UTF-8 bytes."""
    spans: list[tuple[int, int]] = []
    start = end = size = 0
    for line in text.splitlines(keepends=True):
        line_size = len(line.encode())
        if size and size + line_size > limit:
            spans.append((start, end))
            start, size = end, 0
        for char in line:
            char_size = len(char.encode())
            if size + char_size > limit:
                spans.append((start, end))
                start, size = end, 0
            end += 1
            size += char_size
    if end > start:
        spans.append((start, end))
    return spans


def build_artifacts(
    root: Path, manifest: SourceManifest, reviews: ReviewFile, config: BuildConfig,
    applicability: ApplicabilityFile | None = None,
) -> dict[str, bytes]:
    documents = verify_sources(root, manifest)
    if config.applicability_metadata and applicability is None:
        raise CorpusError("Configured applicability metadata must be supplied to the build API")
    as_of = date.fromisoformat(config.as_of) if config.as_of is not None else None
    if reviews.source_snapshot_id != manifest.source_snapshot_id:
        raise CorpusError("Review decisions belong to a different snapshot")
    if set(reviews.decisions) != set(documents):
        raise CorpusError("Review decisions must cover exactly the snapshot document IDs")
    if applicability is not None and (
        applicability.source_snapshot_id != manifest.source_snapshot_id
        or set(applicability.documents) != set(documents)
    ):
        raise CorpusError("Applicability metadata must match exactly the source snapshot IDs")
    selected_metadata = {}
    source_files = {item.path: item for item in manifest.files}
    artifacts: dict[str, bytes] = {}
    inventory, review_rows, corpus, chunks, source_map = [], [], [], [], []
    quality_reports, ocr_queue, quality_blockers = [], [], []
    hash_groups: dict[str, list[str]] = defaultdict(list)
    for key, doc in documents.items():
        hash_groups[doc.content_hash].append(key)
    for key, doc in sorted(documents.items()):
        try:
            selected = validate_metadata(doc, applicability.documents[key]) if applicability else metadata_for(doc)
        except ValueError as exc:
            raise CorpusError(f"Invalid applicability metadata for {key}: {exc}") from exc
        selected_metadata[key] = selected
        doc = doc.model_copy(update={"applicability": selected})
        source = manifest.documents[key]
        decision = reviews.decisions[key]
        if decision.content_hash != doc.content_hash:
            raise CorpusError(f"Stale review content hash: {key}")
        flags = []
        if not source.raw_path:
            flags.append("original_attachment_missing" if source.source_kind == "attachment"
                         else "raw_html_unmapped")
        if any(line.lstrip().startswith("|") for line in doc.content.splitlines()):
            flags.append("table_requires_review")
        if len(hash_groups[doc.content_hash]) > 1:
            flags.append("identical_text_candidate_not_source_deduplicated")
        if not doc.academic_year:
            flags.append("academic_year_unknown")
        if not doc.published_at:
            flags.append("published_at_unknown")
        if doc.status.value == "pending_ocr":
            flags.append("pending_ocr")
        if selected.major.proposed == "out_of_scope":
            flags.append("outside_supported_majors")
        if selected.major.verified == "unknown":
            flags.append("applicability_unverified")
        raw_file = source_files[source.raw_path] if source.raw_path else None
        raw = source_path(root, source.raw_path).read_bytes() if source.raw_path else None
        quality = None
        if raw_file is not None:
            try:
                quality = analyze_source(raw, doc.url, doc.fetched_at, raw_file.encoding)
                quality_reports.append({"document_id": key, "report_sha256": quality_digest(quality),
                                        "report": quality.model_dump()})
                ocr_queue.extend({"document_id": key, "source_url": doc.url, "page_id": page.page_id,
                                  "page": page.page_number, "reasons": page.reasons,
                                  "source_sha256": quality.source_sha256} for page in quality.pages if page.needs_ocr)
            except Exception as exc:
                if decision.status == "include":
                    raise CorpusError(f"Cannot assess source quality for {key}: {exc}") from exc
                quality_blockers.append({"document_id": key, "reason": "quality_extraction_failed", "detail": str(exc)})
        else:
            quality_blockers.append({"document_id": key, "reason": "raw_source_missing", "source_url": doc.url})
        if decision.status == "include":
            try:
                decision = require_review(
                    doc, decision, raw_file.sha256 if raw_file else None,
                    source_encoding=raw_file.encoding if raw_file else "binary", as_of=as_of,
                    raw=raw,
                )
            except ValueError as exc:
                raise CorpusError(f"Include lacks valid review evidence: {key}: {exc}") from exc
        text = normalize(doc.content)
        normalized_path = f"normalized/{key}.md"
        artifacts[normalized_path] = text.encode()
        metadata = {
            "document_id": key, "source_url": doc.url, "title": doc.title,
            "major": selected.major.verified, "proposed_major": selected.major.proposed,
            "legacy_crawler_major": doc.major.value, "document_type": doc.document_type.value,
            "applicability": selected.model_dump(),
            "publisher": doc.publisher.value, "academic_year": doc.academic_year,
            "published_at": doc.published_at, "fetched_at": doc.fetched_at,
            "source_content_hash": doc.content_hash, "normalized_sha256": sha256(text.encode()),
            "markdown_path": source.markdown_path, "raw_path": source.raw_path,
            "raw_sha256": source_files[source.raw_path].sha256 if source.raw_path else None,
            "raw_checksum_encoding": source_files[source.raw_path].encoding if source.raw_path else None,
            "review_status": decision.status, "review": decision.model_dump(),
            "review_as_of": config.as_of,
            "raw_capture": doc.raw_source.model_dump() if doc.raw_source else None,
            "source_quality_sha256": quality_digest(quality) if quality else None,
            "source_unit_ids": ([page.page_id for page in quality.pages] + [table.table_id for table in quality.tables]
                                if quality and decision.status == "include" else []),
        }
        inventory.append({**metadata, "crawler_status": doc.status.value,
                          "review_status": decision.status, "flags": sorted(flags),
                          "normalized_path": normalized_path,
                          "identical_text_candidates": sorted(
                              i for i in hash_groups[doc.content_hash] if i != key)})
        review_rows.append({"document_id": key, **decision.model_dump()})
        if decision.status != "include":
            continue
        corpus.append({**metadata, "content_markdown": text})
        for position, (start, end) in enumerate(split_chunks(text, config.max_chunk_bytes)):
            chunk_text = text[start:end]
            chunk_id = sha256(f"{key}\n{position}\n{chunk_text}".encode())[:24]
            locator = {"normalized_path": normalized_path, "start_char": start,
                       "end_char": end, "start_line": text.count("\n", 0, start) + 1,
                       "end_line": text.count("\n", 0, end - 1) + 1,
                       "scope": "normalized_markdown"}
            chunks.append({**metadata, "chunk_id": chunk_id, "text": chunk_text,
                           "position": position, "locator": locator})
            source_map.append({"chunk_id": chunk_id, "document_id": key,
                               "source_url": doc.url, "locator": locator,
                               "review_evidence_locator": decision.evidence_locator,
                               "source_quality_sha256": metadata["source_quality_sha256"],
                               "source_unit_ids": metadata["source_unit_ids"], "quality_scope": "whole_document"})
    counts = dict(Counter(row["review_status"] for row in inventory))
    report = {
        "schema_version": SCHEMA_VERSION, "document_count": len(documents),
        "review_counts": {status: counts.get(status, 0) for status in REVIEW_STATUSES},
        "flag_counts": dict(sorted(Counter(f for row in inventory for f in row["flags"]).items())),
        "source_files_verified": len(manifest.files), "included_documents": len(corpus),
        "chunk_count": len(chunks), "candidate_only": True, "active_release": False,
        "academic_validity_verified_by_pipeline": False,
        "source_quality_reports": len(quality_reports), "ocr_page_count": len(ocr_queue),
        "quality_blocker_count": len(quality_blockers),
    }
    artifacts.update({
        "source_manifest.json": json_bytes(manifest.model_dump()),
        "build_config.json": json_bytes(config.model_dump()),
        "review_decisions.json": json_bytes(reviews.model_dump()),
        "applicability.json": json_bytes(ApplicabilityFile(
            source_snapshot_id=manifest.source_snapshot_id, documents=selected_metadata,
        ).model_dump()),
        "inventory.jsonl": jsonl_bytes(inventory), "document_review.jsonl": jsonl_bytes(review_rows),
        "documents.jsonl": jsonl_bytes(corpus), "chunks.jsonl": jsonl_bytes(chunks),
        "source_map.jsonl": jsonl_bytes(source_map), "validation_report.json": json_bytes(report),
        "source_quality.jsonl": jsonl_bytes(quality_reports), "ocr_queue.jsonl": jsonl_bytes(ocr_queue),
        "quality_blockers.jsonl": jsonl_bytes(quality_blockers),
    })
    repo_root = Path(__file__).resolve().parents[2]
    implementations = {name: sha256(file_bytes(repo_root / name, "utf8-lf")) for name in (
        "app/hus/corpus.py", "app/hus/models.py", "tools/prepare_hus_corpus.py",
        "app/hus/review.py",
        "app/hus/metadata.py", "app/hus/cleaning.py",
        "app/hus/quality.py", "app/hus/quality_models.py", "app/hus/extractors/pdf.py",
        "app/hus/extractors/docx.py", "app/hus/extractors/excel.py", "app/hus/extractors/html.py",
    )}
    output_hashes = {name: sha256(data) for name, data in sorted(artifacts.items())}
    identity = {"pipeline_version": PIPELINE_VERSION, "implementation_sha256": implementations,
                "source_manifest_sha256": output_hashes["source_manifest.json"],
                "build_config_sha256": output_hashes["build_config.json"],
                "review_decisions_sha256": output_hashes["review_decisions.json"]}
    identity["applicability_sha256"] = output_hashes["applicability.json"]
    artifacts["manifest.json"] = json_bytes({
        **identity, "schema_version": SCHEMA_VERSION, "build_id": sha256(json_bytes(identity)),
        "source_snapshot_id": manifest.source_snapshot_id, "outputs": output_hashes,
    })
    return artifacts


def verify_artifacts(out: Path, expected: dict[str, bytes]) -> None:
    actual_names = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
    if actual_names != set(expected):
        raise CorpusError("Build file inventory differs from the reproduced build")
    for name, data in expected.items():
        if source_path(out, name).read_bytes() != data:
            raise CorpusError(f"Build differs from reproduction: {name}")
