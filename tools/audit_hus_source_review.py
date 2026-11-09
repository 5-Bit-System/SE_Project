"""Audit pinned HUS originals/candidate traces offline; never grant academic review."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "data/hus/rag/releases/hus-data-20261031-v3"
UPSTREAM = "a543cf8d1fac273db41a65a14fb7ae0a05b2d965"


class SourceReviewError(ValueError):
    """Evidence is inconsistent or cannot be inspected honestly."""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise SourceReviewError(message)


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_rows(path, values):
    path.write_bytes("".join(json.dumps(v, ensure_ascii=False, sort_keys=True) + "\n" for v in values).encode("utf-8"))


def write_json(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))


def check_binary_hash(raw, expected):
    require(digest(raw) == expected, "binary hash mismatch")
    return True


def compact(text):
    return "".join(c for c in unicodedata.normalize("NFKC", text).casefold() if c.isalnum())


def captured_context(pages, expected_raw_sha256):
    pages = sorted(pages, key=lambda p: p["page"])
    require([p["page"] for p in pages] == list(range(1, len(pages) + 1)), "captured pages not contiguous")
    require(bool(pages), "captured pages missing")
    intervals, offset = [], 0
    for page in pages:
        require(page["raw_sha256"] == expected_raw_sha256, "capture raw hash mismatch")
        require(digest(page["text"].encode("utf-8")) == page["text_sha256"], "capture text hash mismatch")
        intervals.append((offset, offset + len(page["text"]), page["page"]))
        offset += len(page["text"]) + 1
    return {"joined": "\n".join(p["text"] for p in pages), "intervals": intervals,
            "page_count": len(pages), "raw_sha256": expected_raw_sha256}


def audit_span(span, context, physical_page_count, actual_page_texts):
    start, end = span["start_char"], span["end_char"]
    valid_offsets = type(start) is int and type(end) is int and 0 <= start < end <= len(context["joined"])
    owned = [page for first, last, page in context["intervals"] if first < end and last > start] if valid_offsets else []
    declared = span["pdf_pages"]
    valid_pages = (bool(declared) and declared == sorted(set(declared))
                   and all(type(p) is int and 1 <= p <= physical_page_count for p in declared)) if physical_page_count is not None else None
    raw_found = None
    if actual_page_texts is not None and valid_pages:
        window = "\n".join(actual_page_texts[p - 1] for p in declared)
        needle = compact(span["source_quote"])
        raw_found = bool(needle) and needle in compact(window)
    return {"offset_scope_valid": span["offset_scope"] == "joined_source_pages_with_one_newline_each",
            "capture_quote_match": valid_offsets and context["joined"][start:end] == span["source_quote"],
            "capture_pages_match": owned == declared, "computed_pages": owned,
            "physical_pages_valid": valid_pages, "reextracted_quote_found": raw_found,
            "quote_sha256": digest(span["source_quote"].encode("utf-8")),
            "start_char": start, "end_char": end, "declared_pages": declared}


def page_triage(source_sha256, page, text, prior_code_ocr):
    count = sum(not c.isspace() for c in text)
    return {"source_sha256": source_sha256, "pdf_page": page, "non_whitespace_chars": count,
            "text_sha256": digest(text.encode("utf-8")), "needs_visual_or_ocr": count < 50,
            "prior_code_ocr_audit_available": prior_code_ocr, "blank_verified": False,
            "ocr_completed": False, "review_status": "pending",
            "next_step": "inspect image/full text; reuse code-only OCR if applicable" if count < 50 else
                         "not flagged by low-text heuristic; visual/table accuracy still unverified"}


def pdf_texts(raw):
    import pypdfium2 as pdfium

    texts = []
    with pdfium.PdfDocument(raw) as document:
        for index in range(len(document)):
            page = document[index]
            try:
                textpage = page.get_textpage()
                try:
                    texts.append(textpage.get_text_range())
                finally:
                    textpage.close()
            finally:
                page.close()
    return texts


def audit_candidate(candidate, context, page_count, actual_texts, canonical_record):
    reasons = list(candidate["identity_issues"])
    linked = canonical_record is not None
    if not linked:
        reasons.append("no_canonical_identity_link")
    elif (canonical_record["major"] != candidate["source_major"]
          or canonical_record["course_code"] != candidate["course_code_as_printed"]):
        reasons.append("canonical_scope_or_code_mismatch")
    if linked and candidate["source_publication_year"] < canonical_record["scope"]["cohort_year"]:
        reasons.append("older_source_edition")
    decision = candidate["declared_curriculum_decision"]
    if not decision:
        reasons.append("curriculum_decision_not_declared")
    elif linked and decision != canonical_record["scope"]["curriculum_version"]:
        reasons.append("declared_decision_mismatch")
    checks = [{"field": field, "span_index": i, **audit_span(span, context, page_count, actual_texts)}
              for field, spans in candidate["fields"].items() for i, span in enumerate(spans)]
    if page_count is None:
        reasons.append("original_binary_unavailable")
    trace_passed = bool(checks) and all(c["offset_scope_valid"] and c["capture_quote_match"]
                                      and c["capture_pages_match"] and c["physical_pages_valid"] for c in checks)
    if not trace_passed:
        reasons.append("quote_page_trace_not_verified")
    if any(c["reextracted_quote_found"] is not True for c in checks):
        reasons.append("independent_reextraction_requires_visual_check")
    reasons.extend(["student_applicability_unverified", "academic_and_current_validity_review_pending"])
    return {"candidate_id": candidate["candidate_id"], "document_id": candidate["document_id"],
            "raw_sha256": candidate["raw_sha256"], "source_major": candidate["source_major"],
            "source_year": candidate["source_publication_year"], "declared_decision": decision,
            "course_code_as_printed": candidate["course_code_as_printed"],
            "title_as_extracted": candidate["title_as_extracted"],
            "canonical_record_id": candidate["canonical_record_id"], "identity_link_present": linked,
            "identity_issues_from_release": candidate["identity_issues"],
            "technical_capture_trace_passed": trace_passed, "span_checks": checks,
            "fields_present": sorted(field for field, spans in candidate["fields"].items() if spans),
            "fields_missing": sorted(set(["content", "objectives", "assessment"]) - set(candidate["fields"])),
            "blocking_reasons": sorted(set(reasons)), "review_status": "pending_academic_source_review",
            "academic_verified": False, "default_retrieval_enabled": False,
            "current_validity": "unverified", "assessment_weights_published": False,
            "reviewer": None, "reviewed_at": None}


def recover_original(cache, capture):
    expected = capture["sha256"]
    target = cache / f"{expected}.pdf"
    if target.exists():
        raw = target.read_bytes()
        check_binary_hash(raw, expected)
        return target, {"kind": "pinned_git_object_review_cache", "commit": UPSTREAM,
                        "git_path": capture["repository_asset_path"]}
    result = subprocess.run(["git", "-c", "safe.directory=" + ROOT.as_posix(), "show",
                             UPSTREAM + ":" + capture["repository_asset_path"]],
                            cwd=ROOT, capture_output=True)
    require(result.returncode == 0, "pinned Git original unavailable; fetch source commit or supply exact cache")
    check_binary_hash(result.stdout, expected)
    cache.mkdir(parents=True, exist_ok=True)
    target.write_bytes(result.stdout)
    return target, {"kind": "pinned_git_object_review_cache", "commit": UPSTREAM,
                    "git_path": capture["repository_asset_path"]}


def run_audit(out, cache, web_checks=None):
    out, cache = Path(out).resolve(), Path(cache).resolve()
    require(cache.is_relative_to(ROOT / "backups") and cache != ROOT / "backups",
            "cache must be a dedicated directory under backups, outside runtime/source roots")
    require(any(out.is_relative_to(base) and out != base for base in [ROOT / "data/hus/review", ROOT / "backups"]),
            "review output must be a dedicated directory under data/hus/review or backups")
    require(not out.is_relative_to(cache) and not cache.is_relative_to(out), "output and cache must be separate directories")
    require(not out.exists(), "output exists; use a new audit directory")
    require(not out.is_relative_to(RELEASE) and not out.is_relative_to(ROOT / "data/hus/citation_assets"),
            "review output cannot modify runtime sources")
    out.mkdir(parents=True)
    release_manifest = json.loads((RELEASE / "manifest.json").read_bytes())
    pointer = json.loads((ROOT / "data/hus/rag/CURRENT.json").read_bytes())
    require(release_manifest["release_sha256"] == pointer["release_sha256"], "selected release identity mismatch")
    unsigned = {k: v for k, v in release_manifest.items() if k != "release_sha256"}
    require(digest((json.dumps(unsigned, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
            == pointer["release_sha256"], "release manifest signature mismatch")
    for name, pin in release_manifest["files"].items():
        path = (RELEASE / name).resolve()
        require(path.is_relative_to(RELEASE), "release path escapes source root")
        raw = path.read_bytes()
        require(len(raw) == pin["bytes"], "release file size mismatch")
        check_binary_hash(raw, pin["sha256"])
    candidates = read_rows(RELEASE / "source_syllabi.jsonl")
    captured = read_rows(RELEASE / "evidence/recovered_text.jsonl")
    captures = {r["document_id"]: r for r in read_rows(RELEASE / "evidence/recovered_sources.jsonl")}
    f1_sources = {r["source_id"]: r for r in read_rows(RELEASE / "sources.jsonl")}
    records = {r["record_id"]: r for r in read_rows(RELEASE / "f2_records.jsonl")}
    registry_path = ROOT / "data/hus/citation_assets/registry.json"
    registry = json.loads(registry_path.read_bytes())
    inputs = json.loads((RELEASE / "input_manifest.json").read_bytes())
    groups = defaultdict(list)
    for page in captured:
        groups[page["document_id"]].append(page)
    contexts = {cid: captured_context(groups[cid], source["raw_sha256"])
                for cid, source in {c["document_id"]: c for c in candidates}.items()}
    source_inputs = [RELEASE / name for name in ["manifest.json", "source_syllabi.jsonl", "source_syllabi_report.json",
        "source_inventory.jsonl", "syllabus_links.jsonl", "sources.jsonl", "f2_records.jsonl", "f3_records.jsonl",
        "f3_chunks.jsonl", "evidence/recovered_sources.jsonl", "evidence/recovered_text.jsonl", "evidence/pdf_code_page_audit.csv"]]
    source_inputs += [registry_path, ROOT / "data/hus/rag/CURRENT.json", ROOT / "data/hus/corpus/source_manifest.json",
                      ROOT / "data/hus/corpus/review_decisions.json"]
    before = {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in source_inputs}
    assets = {}
    for sha, asset in registry["assets"].items():
        assets[sha] = {"path": ROOT / "data/hus/citation_assets" / asset["path"], "file_type": asset["file_type"],
                       "expected_pages": asset["page_count"], "bindings": ["active_citation_registry"], "origins": asset["origins"]}
    for pdf in inputs["pdfs"]:
        assets.setdefault(pdf["sha256"], {"path": ROOT / pdf["path"], "file_type": "pdf", "expected_pages": None,
                                          "bindings": ["canonical_pdf_reference"], "origins": [{"commit": pdf["origin_commit"], "path": pdf["path"]}]})
    for cid in contexts:
        capture = captures[cid]
        path, origin = recover_original(cache, capture)
        assets[capture["sha256"]] = {"path": path, "file_type": "pdf", "expected_pages": capture["page_count"],
                                      "bindings": ["review_only_syllabus_not_active_registry"], "origins": [origin]}
    with (RELEASE / "evidence/pdf_code_page_audit.csv").open(encoding="utf-8", newline="") as stream:
        old_ocr = list(csv.DictReader(stream))
    ocr_by_sha = defaultdict(set)
    for pdf in inputs["pdfs"]:
        number = pdf["source_ref"].split(".", 1)[0]
        ocr_by_sha[pdf["sha256"]].update(int(row["pdf_page"]) for row in old_ocr if row["pdf_number"] == number)
    asset_rows, page_rows, actual_texts = [], [], {}
    for sha, asset in sorted(assets.items()):
        row = {"sha256": sha, "file_type": asset["file_type"], "bindings": asset["bindings"],
               "origins": asset["origins"], "available": asset["path"].is_file(),
               "hash_verified": False, "physical_pages": None, "academic_verified": False}
        if row["available"]:
            raw = asset["path"].read_bytes()
            check_binary_hash(raw, sha)
            row.update(hash_verified=True, bytes=len(raw))
            if asset["file_type"] == "pdf":
                require(raw.startswith(b"%PDF-"), "expected PDF binary")
                texts = pdf_texts(raw)
                row["physical_pages"] = len(texts)
                require(asset["expected_pages"] is None or len(texts) == asset["expected_pages"], "physical page count mismatch")
                for index, text in enumerate(texts):
                    page_rows.append(page_triage(sha, index + 1, text, index + 1 in ocr_by_sha[sha]))
                actual_texts[sha] = texts
            else:
                with zipfile.ZipFile(asset["path"]) as archive:
                    require("word/document.xml" in archive.namelist(), "DOCX lacks document XML")
        asset_rows.append(row)
    by_asset = {a["sha256"]: a for a in asset_rows}
    candidate_rows = []
    for candidate in candidates:
        require(candidate["academic_verified"] is False and candidate["answer_policy"] == "candidate_not_in_default_retrieval"
                and candidate["assessment_weights_parsed"] is None, "candidate academic policy unexpectedly changed")
        asset = by_asset.get(candidate["raw_sha256"], {})
        candidate_rows.append(audit_candidate(candidate, contexts[candidate["document_id"]],
            asset.get("physical_pages"), actual_texts.get(candidate["raw_sha256"]), records.get(candidate["canonical_record_id"])))
    corpus = json.loads((ROOT / "data/hus/corpus/source_manifest.json").read_bytes())
    pinned = {f["path"]: f for f in corpus["files"]}
    inventory_rows = []
    for original in read_rows(RELEASE / "source_inventory.jsonl"):
        cid = original["document_id"]
        f1 = f1_sources.get(cid)
        source = captures.get(cid) or (f1 or {}).get("recovered_capture")
        asset = by_asset.get(source["sha256"]) if source else None
        available = bool(asset and asset["hash_verified"])
        basis = "verified_binary" if available else None
        raw_path = corpus["documents"].get(cid, {}).get("raw_path")
        source_hash = None
        if not available and raw_path and raw_path in pinned:
            path = ROOT / "data/hus" / raw_path
            if path.is_file():
                raw = path.read_bytes()
                pin = pinned[raw_path]
                normalized = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8") if pin["encoding"] == "utf8-lf" else raw
                available = digest(normalized) == pin["sha256"]
                source_hash = pin["sha256"]
                basis = "archived_utf8_lf_snapshot_not_HTTP_byte_equality" if available else "archive_hash_mismatch"
        if not available and f1 and f1.get("raw_evidence_path"):
            path = RELEASE / f1["raw_evidence_path"]
            if path.is_file():
                available = True
                source_hash = digest(path.read_bytes())
                basis = "release_pinned_raw_evidence"
        inventory_rows.append({**original, "available_in_this_audit": available, "availability_basis": basis,
                               "archive_hash": source_hash, "academic_verified": False, "current_validity": "unverified"})
    old_reviews = json.loads((ROOT / "data/hus/corpus/review_decisions.json").read_bytes())["decisions"]
    historic_ocr = [{"document_id": cid, "historical_status": value["status"],
                    "binary_available_in_this_audit": next((r["available_in_this_audit"] for r in inventory_rows if r["document_id"] == cid), False),
                    "review_status": "pending", "resolved_by_this_audit": False}
                   for cid, value in old_reviews.items() if value["status"] == "pending_ocr"]
    spans = [s for c in candidate_rows for s in c["span_checks"]]
    outputs = {"binary_assets.jsonl": asset_rows, "page_triage.jsonl": page_rows,
               "ocr_queue.jsonl": [p for p in page_rows if p["needs_visual_or_ocr"]],
               "candidate_reviews.jsonl": candidate_rows, "source_inventory_review.jsonl": inventory_rows,
               "missing_sources.jsonl": [r for r in inventory_rows if not r["available_in_this_audit"]],
               "historical_ocr_blockers.jsonl": historic_ocr,
               "web_checks.jsonl": read_rows(web_checks) if web_checks else []}
    for name, values in outputs.items():
        write_rows(out / name, values)
    require(before == {p: digest((ROOT / p).read_bytes()) for p in before}, "source/review changed during audit")
    report = {"schema_version": "1.0", "audit_on": "2026-11-02", "status": "technical_audit_only_academic_review_pending",
              "source_inputs_sha256": before, "source_release": RELEASE.relative_to(ROOT).as_posix(),
              "release_payload_hashes_checked": len(release_manifest["files"]),
              "binary_assets": len(asset_rows), "available_binary_assets": sum(a["hash_verified"] for a in asset_rows),
              "file_types": dict(Counter(a["file_type"] for a in asset_rows)),
              "pdf_pages_triaged": len(page_rows), "low_text_pages": len(outputs["ocr_queue.jsonl"]),
              "prior_code_ocr_rows_reused": len(old_ocr), "tesseract_available": shutil.which("tesseract") is not None,
              "ocr_run": False, "ocr_accuracy_claimed": False,
              "candidate_records": len(candidate_rows), "upstream_identity_issue_counts": dict(Counter(i for c in candidates for i in c["identity_issues"])),
              "candidate_identity_links": sum(c["identity_link_present"] for c in candidate_rows),
              "candidate_capture_trace_passed": sum(c["technical_capture_trace_passed"] for c in candidate_rows),
              "quote_spans": len(spans), "capture_quotes_match": sum(s["capture_quote_match"] for s in spans),
              "capture_page_ranges_match": sum(s["capture_pages_match"] for s in spans),
              "physical_page_ranges_valid": sum(s["physical_pages_valid"] is True for s in spans),
              "independent_reextracted_quotes_found": sum(s["reextracted_quote_found"] is True for s in spans),
              "source_inventory_records": len(inventory_rows), "sources_available": sum(r["available_in_this_audit"] for r in inventory_rows),
              "sources_unavailable": len(outputs["missing_sources.jsonl"]), "historical_pending_ocr": len(historic_ocr),
              "F2_review_status": dict(Counter(r["catalog_review"]["status"] for r in records.values())),
              "academic_verification_added": 0, "current_validity_verified": 0,
              "official_F3_enabled": False, "runtime_registry_changed": False,
              "live_checks": {"attempts": len(outputs["web_checks.jsonl"]), "prove_current_validity": False},
              "limitations": ["Low-text heuristic does not certify blank/scan or table accuracy.",
                              "Independent PDFium text order can differ from captured PyMuPDF; mismatches need visual check.",
                              "Captured quote/hash/page checks do not certify academic correctness or current applicability."],
              "new_RAG_inference": False, "product_database_modified": False, "committed": False, "pushed": False}
    write_json(out / "report.json", report)
    write_json(out / "manifest.json", {"files_sha256": {p.name: digest(p.read_bytes()) for p in out.iterdir() if p.is_file()},
                                       "audit_tool_sha256": digest(Path(__file__).read_bytes()), "source_commit": UPSTREAM})
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=ROOT / "backups/hus_source_review/p13/originals")
    parser.add_argument("--web-checks", type=Path)
    args = parser.parse_args(argv)
    try:
        report = run_audit(args.out, args.cache, args.web_checks)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        print(f"Source review audit failed: {exc}")
        return 1
    print(json.dumps({k: v for k, v in report.items() if k != "source_inputs_sha256"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
