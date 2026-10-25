"""Compare/import explicitly supplied local originals and queue missing attachments, offline."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path

import pdfplumber

from app.hus.corpus import json_bytes, jsonl_bytes, load_catalog
from app.hus.extractors import extract_attachment
from app.hus.storage import RawStorage


def recover(root: Path, candidate_manifest: Path, out: Path) -> dict:
    root, candidate_manifest, out = root.resolve(), candidate_manifest.resolve(), out.resolve()
    if out.exists():
        raise ValueError("Recovery report directory already exists; use a new run")
    if not candidate_manifest.is_relative_to(root):
        raise ValueError("Candidate acquisition record must be inside source root")
    documents = load_catalog(root)
    candidates = json.loads(candidate_manifest.read_text(encoding="utf-8"))
    by_url = {}
    for candidate in candidates:
        url = candidate["final_url"]
        if url in by_url:
            raise ValueError(f"Ambiguous local candidates for {url}")
        by_url[url] = candidate
    if not set(by_url).issubset({doc.url for doc in documents.values()}):
        raise ValueError("Candidate URL is not in the catalog")
    storage = RawStorage(root)
    inventory, queue, comparisons = [], [], []
    # Stage all comparisons before recording imports; no changes to catalog/Markdown/review.
    staged = []
    for key, doc in sorted(documents.items()):
        ext = Path(doc.url.split("?")[0]).suffix.lower().lstrip(".")
        if ext not in {"pdf", "docx", "xlsx", "xls", "doc"}:
            continue
        row = {"document_id": key, "source_url": doc.url, "file_type": ext,
               "source_content_hash": doc.content_hash, "expected_original_sha256": None,
               "version_status": "unverified", "review_status": "needs_review"}
        candidate = by_url.get(doc.url)
        if candidate is None:
            row.update(status="queued", blocker_codes=["original_missing", "original_version_unverified"],
                       next_action="Retrieve without validators, store immutable bytes, compare exact version")
            queue.append(row)
        else:
            path = Path(candidate["raw_path"])
            # Only explicit files from this project input tree are eligible; never sweep test caches.
            if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
                raise ValueError(f"Local candidate is missing or outside source root: {key}")
            raw = path.read_bytes()
            if len(raw) != candidate["bytes"]:
                raise ValueError(f"Candidate byte size differs from its acquisition record: {key}")
            digest = hashlib.sha256(raw).hexdigest()
            # Historical capture filenames contain the first 12 hash digits.
            if not path.stem.endswith(digest[:12]):
                raise ValueError(f"Candidate hash differs from its capture filename: {key}")
            text, needs_ocr = extract_attachment(raw, ext)
            exact = text.strip() == doc.content
            page_count = None
            if ext == "pdf":
                with pdfplumber.open(path) as pdf:
                    page_count = len(pdf.pages)
            row.update(status="recovered_candidate", raw_sha256=digest, byte_size=len(raw),
                       exact_extracted_text_match=exact, needs_ocr=needs_ocr, page_count=page_count,
                       original_fetched_at=None, origin_locator=path.relative_to(root).as_posix(),
                       blocker_codes=["original_version_unverified", "source_review_required"])
            row["draft_marker_present"] = "DỰ THẢO" in text
            if not exact:
                row["blocker_codes"].append("extracted_text_mismatch")
            comparisons.append({"document_id": key, "extracted_sha256": hashlib.sha256(text.strip().encode()).hexdigest(),
                                "catalog_content_hash": doc.content_hash,
                                "exact_extracted_text_match": exact, "page_count": page_count,
                                "diff": "".join(difflib.unified_diff(doc.content.splitlines(True), text.strip().splitlines(True),
                                                                     fromfile="catalog", tofile="recovered_extraction"))})
            staged.append((row, doc, raw, path))
        inventory.append(row)
    for row, doc, raw, path in staged:
        storage.save_raw_document(
            doc.url, raw, row["file_type"], major=doc.major, title=doc.title,
            document_id=row["document_id"], content_type="application/pdf" if row["file_type"] == "pdf" else None,
            kind="local_import", origin_locator=path.relative_to(root).as_posix(),
        )
        ref = storage.archive.latest(doc.url)
        row.update(raw_path=ref.raw_path, capture_id=ref.capture_id)
    report = {
        "schema_version": "1.0", "observed_at": datetime.now(timezone.utc).isoformat(),
        "catalog_sha256_utf8_lf": hashlib.sha256((root / "processed/catalog.json").read_text(encoding="utf-8").encode()).hexdigest(),
        "comparison_implementation_sha256": {
            name: hashlib.sha256((Path(__file__).resolve().parents[1] / name).read_text(encoding="utf-8").encode()).hexdigest()
            for name in ("tools/recover_hus_sources.py", "app/hus/extractors/pdf.py", "app/hus/cleaning.py")
        },
        "candidate_manifest_sha256": hashlib.sha256(candidate_manifest.read_bytes()).hexdigest(),
        "attachment_count": len(inventory), "recovered_candidates": len(staged),
        "queued_missing_sources": len(queue), "verified_original_versions": 0,
        "academic_review_completed": 0, "catalog_modified": False,
        "candidate_manifest": candidate_manifest.relative_to(root).as_posix(),
    }
    out.mkdir(parents=True)
    (out / "report.json").write_bytes(json_bytes(report))
    (out / "inventory.jsonl").write_bytes(jsonl_bytes(inventory))
    (out / "recovery_queue.jsonl").write_bytes(jsonl_bytes(queue))
    (out / "comparisons.jsonl").write_bytes(jsonl_bytes(comparisons))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/hus"))
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(recover(args.root, args.candidates, args.out), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(1, f"Recovery failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
