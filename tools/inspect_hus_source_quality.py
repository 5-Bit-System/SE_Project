"""Offline quality/OCR/table reports from pinned sources plus explicit recovery candidates."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from app.hus.corpus import (
    SourceManifest,
    json_bytes,
    jsonl_bytes,
    read_json,
    source_path,
    verify_sources,
)
from app.hus.quality import analyze_source, quality_digest


def inspect(root: Path, manifest_path: Path, recovery: Path | None, out: Path) -> dict:
    if out.exists():
        raise ValueError("Quality output already exists; use a new run")
    manifest = SourceManifest.model_validate(read_json(manifest_path))
    docs = verify_sources(root, manifest)
    files = {entry.path: entry for entry in manifest.files}
    recovered = {}
    if recovery:
        for line in recovery.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("raw_path"):
                if row["document_id"] in recovered:
                    raise ValueError("Duplicate recovery document ID")
                recovered[row["document_id"]] = row
        if not set(recovered).issubset(docs):
            raise ValueError("Recovery references documents outside snapshot")
    reports, pages, tables, queue, blockers, review_queue = [], [], [], [], [], []
    for key, doc in sorted(docs.items()):
        source = manifest.documents[key]
        candidate = recovered.get(key)
        path, encoding = (
            source.raw_path,
            files[source.raw_path].encoding if source.raw_path else "binary",
        )
        if not path and candidate:
            if candidate["source_url"] != doc.url:
                raise ValueError("Recovery source URL mismatch")
            path = candidate["raw_path"]
            raw = source_path(root, path).read_bytes()
            if hashlib.sha256(raw).hexdigest() != candidate["raw_sha256"]:
                raise ValueError("Recovery raw checksum mismatch")
        if not path:
            blockers.append(
                {
                    "document_id": key,
                    "source_url": doc.url,
                    "reason": "raw_source_missing",
                    "crawler_status": doc.status.value,
                    "page_count": None,
                }
            )
            continue
        raw = source_path(root, path).read_bytes()
        try:
            report = analyze_source(raw, doc.url, doc.fetched_at, encoding)
        except Exception as exc:
            blockers.append(
                {
                    "document_id": key,
                    "source_url": doc.url,
                    "reason": "quality_extraction_failed",
                    "detail": str(exc),
                }
            )
            continue
        report_hash = quality_digest(report)
        reports.append(
            {
                "document_id": key,
                "raw_path": path,
                "report_sha256": report_hash,
                "source_version_status": candidate.get("version_status", "unverified")
                if candidate
                else "pinned_snapshot",
                "content_matches_catalog": report.display_content_sha256 == doc.content_hash,
                "review_status": "needs_review",
                "report": report.model_dump(),
            }
        )
        pages.extend({"document_id": key, **page.model_dump()} for page in report.pages)
        tables.extend(
            {"document_id": key, "source_sha256": report.source_sha256, **table.model_dump()}
            for table in report.tables
        )
        for unit_kind, units in (
            ("page", report.pages),
            ("table", report.tables),
            (
                "cell",
                [
                    cell
                    for table in report.tables
                    for cell in table.cells
                    if cell.presence != "covered"
                ],
            ),
        ):
            for unit in units:
                review_queue.append(
                    {
                        "document_id": key,
                        "unit_kind": unit_kind,
                        "unit_id": getattr(unit, f"{unit_kind}_id"),
                        "expected_sha256": quality_digest(unit),
                        "locator": unit.locator,
                        "report_sha256": report_hash,
                        "status": "needs_review",
                    }
                )
        queue.extend(
            {
                "document_id": key,
                "source_url": doc.url,
                "page_id": page.page_id,
                "page": page.page_number,
                "source_sha256": report.source_sha256,
                "reasons": page.reasons,
                "status": "needs_visual_or_ocr_review",
            }
            for page in report.pages
            if page.needs_ocr
        )
    summary = {
        "schema_version": "1.0",
        "source_snapshot_id": manifest.source_snapshot_id,
        "document_count": len(docs),
        "quality_reports": len(reports),
        "pdf_pages": len(pages),
        "tables": len(tables),
        "ocr_pages": len(queue),
        "source_blockers": len(blockers),
        "blocker_counts": dict(Counter(row["reason"] for row in blockers)),
        "verified_pages": 0,
        "verified_cells": 0,
        "active_release": False,
    }
    summary["content_mismatches"] = sum(not row["content_matches_catalog"] for row in reports)
    summary["unverified_recovered_versions"] = sum(
        row["source_version_status"] == "unverified" for row in reports
    )
    summary["tables_with_issues"] = sum(bool(table["issues"]) for table in tables)
    summary["cell_presence_counts"] = dict(
        Counter(cell["presence"] for table in tables for cell in table["cells"])
    )
    summary["review_units"] = len(review_queue)
    summary["pending_ocr_documents_without_raw"] = sum(
        row.get("crawler_status") == "pending_ocr" for row in blockers
    )
    summary["inputs"] = {
        "source_manifest_sha256": hashlib.sha256(json_bytes(manifest.model_dump())).hexdigest(),
        "recovery_inventory_sha256": hashlib.sha256(
            recovery.read_text(encoding="utf-8").encode()
        ).hexdigest()
        if recovery
        else None,
    }
    repo = Path(__file__).resolve().parents[1]
    summary["implementation_sha256"] = {
        name: hashlib.sha256((repo / name).read_text(encoding="utf-8").encode()).hexdigest()
        for name in (
            "tools/inspect_hus_source_quality.py",
            "app/hus/quality.py",
            "app/hus/quality_models.py",
            "app/hus/corpus.py",
            "app/hus/models.py",
            "app/hus/cleaning.py",
            "app/hus/extractors/pdf.py",
            "app/hus/extractors/html.py",
            "app/hus/extractors/docx.py",
            "app/hus/extractors/excel.py",
        )
    }
    out.mkdir(parents=True)
    summary["outputs_sha256"] = {}
    for name, rows in (
        ("source_quality", reports),
        ("page_quality", pages),
        ("tables", tables),
        ("ocr_queue", queue),
        ("source_blockers", blockers),
        ("review_queue", review_queue),
    ):
        data = jsonl_bytes(rows)
        (out / f"{name}.jsonl").write_bytes(data)
        summary["outputs_sha256"][f"{name}.jsonl"] = hashlib.sha256(data).hexdigest()
    (out / "report.json").write_bytes(json_bytes(summary))
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/hus"))
    parser.add_argument(
        "--manifest", type=Path, default=Path("data/hus/corpus/source_manifest.json")
    )
    parser.add_argument("--recovery", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(
            json.dumps(
                inspect(args.root, args.manifest, args.recovery, args.out),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Quality inspection failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
