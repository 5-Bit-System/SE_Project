"""Offline, reproducible HUS preparation; reads snapshots without modifying them."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

VERSION = "hus-preparation-1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_text(text: str) -> str:
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n")).strip()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_rows(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


class Page(HTMLParser):
    def __init__(self, content: str) -> None:
        super().__init__(convert_charrefs=True)
        self.canonical = ""
        self.text: list[str] = []
        self.feed(content)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href") or ""

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def split_markdown(text: str) -> tuple[dict, str]:
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text.replace("\r\n", "\n"), re.S)
    if not match:
        return {}, text
    front = dict(line.split(": ", 1) for line in match[1].splitlines() if ": " in line)
    return front, match[2]


def chunk_spans(text: str, byte_budget: int = 2400) -> list[tuple[int, int]]:
    """Preserve complete lines/paragraphs; never split an oversized condition/table."""
    spans: list[tuple[int, int]] = []
    start = end = 0
    for line in text.splitlines(keepends=True):
        next_end = end + len(line)
        if end > start and len(text[start:next_end].encode()) > byte_budget:
            spans.append((start, end))
            start = end
        end = next_end
    if end > start:
        spans.append((start, end))
    return spans


def prepare(snapshot: Path, output: Path, review_path: Path, cases_path: Path | None = None) -> dict:
    if output.resolve().is_relative_to(snapshot.resolve()):
        raise ValueError("Output must be outside the immutable snapshot")
    if output.exists():
        raise ValueError("Output already exists; use a new build directory")
    catalog_path = snapshot / "processed/catalog.json"
    catalog_bytes = catalog_path.read_bytes()
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8-sig"))
    if digest(catalog_bytes) != manifest["catalog_sha256"]:
        raise ValueError("Catalog hash does not match snapshot manifest")
    catalog = json.loads(catalog_bytes)
    entries = catalog["documents"]
    if len(entries) != catalog["document_count"]:
        raise ValueError("Catalog count mismatch")
    reviews = json.loads(review_path.read_text(encoding="utf-8"))
    unknown = set(reviews) - set(entries)
    if unknown:
        raise ValueError(f"Review contains unknown IDs: {sorted(unknown)}")
    files = sorted(p for p in snapshot.rglob("*") if p.is_file())
    inputs = [{"path": p.relative_to(snapshot).as_posix(), "sha256": digest(p.read_bytes())} for p in files]
    config = {"pipeline_version": VERSION, "review_sha256": digest(review_path.read_bytes()),
              "pipeline_code_sha256": digest(Path(__file__).read_bytes()),
              "input_inventory_sha256": digest(json.dumps(inputs, sort_keys=True).encode()),
              "cases_sha256": digest(cases_path.read_bytes()) if cases_path else None,
              "boundary": "complete_line", "byte_budget": 2400, "tokenizer": None,
              "note": "UTF-8 bytes are not model tokens; no embedding tokenizer selected"}
    build_id = digest((digest(catalog_bytes) + json.dumps(config, sort_keys=True)).encode())[:16]
    output.mkdir(parents=True)
    (output / "normalized").mkdir()
    raw = []
    for p in files:
        if p.suffix == ".html":
            page = Page(p.read_text(encoding="utf-8"))
            raw.append((p, page))
    inventory, decisions, issues, logs, documents, chunks, maps = [], [], [], [], [], [], []
    hashes: dict[str, str] = {}
    for key, item in entries.items():
        source = item["content_markdown"]
        normalized = canonical_text(source)
        candidates = list((snapshot / "processed/documents").rglob(f"*--{key[:8]}.md"))
        flags = []
        front = {}
        if len(candidates) != 1:
            flags.append("markdown_mapping_not_unique")
        else:
            front, body = split_markdown(candidates[0].read_text(encoding="utf-8"))
            if canonical_text(body) != normalized:
                flags.append("markdown_catalog_content_mismatch")
            for field, catalog_field in [("title", "title"), ("url", "source_url"),
                                         ("type", "document_type"), ("major", "major"),
                                         ("publisher", "publisher")]:
                if front.get(field) != item.get(catalog_field):
                    flags.append(f"frontmatter_mismatch:{field}")
        url = item["source_url"]
        path = urlsplit(url).path
        raw_matches = [(p, page) for p, page in raw
                       if urlsplit(page.canonical).path == path]
        raw_paths = [p.relative_to(snapshot).as_posix() for p, _ in raw_matches]
        paths = ["processed/catalog.json"] + [p.relative_to(snapshot).as_posix() for p in candidates] + raw_paths
        if not raw_paths:
            flags.append("raw_html_unmapped")
        if urlsplit(url).path.lower().endswith((".pdf", ".docx")):
            flags.append("original_attachment_binary_not_in_snapshot")
        if "| ---" in source:
            flags.append("table_requires_review")
        if "\ufffd" in source:
            flags.append("replacement_character")
        review = reviews.get(key, {})
        decision = review.get("decision", "pending_ocr" if item["status"] == "pending_ocr" else "needs_review")
        reason = review.get("reason", "OCR/source file required" if decision == "pending_ocr" else "Content/scope not yet reviewed")
        if review and review.get("content_sha256") != digest(source.encode()):
            raise ValueError(f"Stale review: {key}")
        duplicate_of = hashes.get(digest(normalized.encode()))
        # Identical text can be an extraction placeholder, not identical source files.
        hashes.setdefault(digest(normalized.encode()), key)
        if duplicate_of:
            flags.append("identical_text_candidate_not_source_deduplicated")
        if decision not in {"include", "exclude", "needs_review", "pending_ocr"}:
            raise ValueError(f"Invalid review decision: {key}")
        if decision == "include" and (flags or not review.get("evidence")):
            raise ValueError(f"Included source has unresolved checks: {key}: {flags}")
        record = {"document_id": key, "title": item["title"], "source_url": url,
                  "source_paths": paths, "source_hashes": {p: digest((snapshot / p).read_bytes()) for p in paths},
                  "catalog_content_sha256": digest(source.encode()), "frontmatter": front,
                  "crawler_type": item["document_type"], "crawler_major": item["major"],
                  "crawler_status": item["status"], "flags": flags,
                  "same_text_as": duplicate_of, "characters": len(source)}
        inventory.append(record)
        decisions.append({"document_id": key, "title": item["title"], "decision": decision,
                          "reason": reason, "reviewer": review.get("reviewer", "unreviewed"),
                          "reviewed_at": review.get("reviewed_at", ""),
                          "crawler_major": item["major"], "crawler_type": item["document_type"],
                          "reviewed_scope": review.get("scope", "unknown"),
                          "reviewed_major": review.get("major", ""),
                          "candidate_topic": review.get("candidate_topic", ""),
                          "proposed_education_level": review.get("proposed_education_level", ""),
                          "evidence": review.get("evidence", ""), "flags": ";".join(flags)})
        if flags or decision != "include":
            issues.append({"document_id": key, "decision": decision, "reason": reason, "flags": flags})
        # Conservative normalization only; no automatic rewriting of source facts.
        (output / "normalized" / f"{key}.md").write_text(normalized, encoding="utf-8")
        logs.append({"document_id": key, "operations": ["NFC", "CRLF_to_LF", "strip_outer_whitespace"],
                     "before_hash": digest(source.encode()), "after_hash": digest(normalized.encode()),
                     "used_for_chunks": decision == "include"})
        if decision != "include":
            continue
        # Confirm review quotations against both Markdown body and saved HTML text.
        for quote in review.get("source_quotes", []):
            def compact(s: str) -> str:
                return re.sub(r"\s+", " ", s).strip()
            if quote not in source or not any(compact(quote) in compact(" ".join(page.text)) for _, page in raw_matches):
                raise ValueError(f"Review evidence not found in source/HTML: {key}: {quote}")
        doc = {"document_id": key, "source_document_ids": [key], "title": item["title"],
               "canonical_url": url, "alternate_urls": [], "parent_document_id": None,
               "parent_url": item["parent_url"], "publisher": item["publisher"],
               "source_paths": paths, "source_hashes": record["source_hashes"],
               "published_at": item["published_at"], "fetched_at": item["fetched_at"],
               "document_type": review["document_type"], "education_level": review.get("education_level"),
               "majors": [review["major"]] if review.get("major") else [], "scope": review["scope"],
               "academic_year": None, "admission_cohort": None, "effective_from": None, "effective_to": None,
               "validity_status": "unknown", "usage_limit": "Source description only; not proof of current academic rules",
               "review_decision": "include", "reviewer": review["reviewer"], "reviewed_at": review["reviewed_at"],
               "review_note": reason, "metadata_evidence": review["evidence"],
               "extraction_status": "markdown_body_matched", "build_id": build_id,
               "source_snapshot_id": snapshot.name, "pipeline_version": VERSION,
               "normalized_content_hash": digest(normalized.encode()), "text": normalized}
        documents.append(doc)
        for start, end in chunk_spans(normalized):
            text = normalized[start:end]
            chunk_id = key + ":" + digest((VERSION + str(start) + text).encode())[:16]
            chunk = {"chunk_id": chunk_id, "document_id": key, "build_id": build_id,
                     "source_snapshot_id": snapshot.name, "text": text, "content_hash": digest(text.encode()),
                     "heading_path": [item["title"]], "parent_section_id": key,
                     "source_url": url, "source_locator": {"catalog_pointer": f"/documents/{key}/content_markdown",
                        "source_char_span": [len(source) - len(source.lstrip()) + start,
                                             len(source) - len(source.lstrip()) + end]
                        if normalized == source.strip() else None},
                     "normalized_span": [start, end], "scope": doc["scope"], "majors": doc["majors"],
                     "academic_year": None, "validity_status": "unknown"}
            # NFC can change offsets: cite the entire source field plus exact normalized span.
            chunks.append(chunk)
            maps.append({"chunk_id": chunk_id, "source_paths": paths, "source_hashes": record["source_hashes"],
                         "catalog_pointer": chunk["source_locator"]["catalog_pointer"],
                         "normalized_span": [start, end], "mapping": "NFC/line-ending transform; original field retained"})
    for name, rows in [("inventory", inventory), ("issues", issues), ("normalization_log", logs),
                       ("documents", documents), ("chunks", chunks), ("source_map", maps)]:
        write_rows(output / f"{name}.jsonl", rows)
    with (output / "document_review.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(decisions[0]))
        writer.writeheader()
        writer.writerows(decisions)
    write_json(output / "input_manifest.json", {"files": inputs, "source_snapshot_id": snapshot.name})
    write_json(output / "build_config.json", config)
    evaluation = []
    if cases_path:
        for index, (key, line_index, question) in enumerate(json.loads(cases_path.read_text(encoding="utf-8"))):
            case = {"case_id": f"hus-prep-{index + 1:02}", "question": question,
                    "split": "heldout" if key in {"1b525683101bf943", "ce8df97fe49665e9"} or index >= 35 else "development",
                    "reviewer": "codex_source_review", "independent_human_review": False}
            if key:
                doc = next(d for d in documents if d["document_id"] == key)
                quote = doc["text"].splitlines()[line_index]
                supporting = [c for c in chunks if c["document_id"] == key and quote in c["text"]]
                if not quote or not supporting:
                    raise ValueError(f"Case evidence lost during chunking: {question}")
                case.update(document_id=key, evidence=quote, chunk_ids=[c["chunk_id"] for c in supporting],
                            source_locator=supporting[0]["source_locator"], expected_status="source_description")
            else:
                case.update(document_id=None, evidence=None, expected_status="insufficient_evidence_or_business_route",
                            reason="Not supported as current/personal academic facts by the six descriptive documents; links do not prove attachment content")
            evaluation.append(case)
    write_rows(output / "evaluation_cases.jsonl", evaluation)
    sample_ids = {"d75f0faafa5605a4", "d771d9ef92ec2244", "d6370261338de29f", "055c47bf412172c0",
                  "1b525683101bf943", "ce8df97fe49665e9", "a9fcdce2bed71e1f", "d73edbb5ad3fc8e5",
                  "d36d82c967372433", "a090bd625a439d9b", "8afffd3cada3d048", "07a9ebfa5d941de0",
                  "098df9e79c1391af", "bc0a1f59b7ab202c", "87a01b93d4cceb22"}
    write_rows(output / "sample_review.jsonl", [
        {"document_id": r["document_id"], "decision": r["decision"], "flags": r["flags"],
         "comparison": "Only NFC, CRLF and outer whitespace; no source facts rewritten",
         "before": entries[r["document_id"]]["content_markdown"][:1200],
         "after": canonical_text(entries[r["document_id"]]["content_markdown"])[:1200],
         "review_depth": "full Markdown read plus HTML quote check" if r["decision"] == "include" else "screening/sample only"}
        for r in decisions if r["document_id"] in sample_ids])
    # Check every span/hash, complete coverage, and review isolation.
    by_id = {d["document_id"]: d for d in documents}
    assert len({c["chunk_id"] for c in chunks}) == len(chunks)
    for d in documents:
        assert "".join(c["text"] for c in chunks if c["document_id"] == d["document_id"]) == d["text"]
    for c in chunks:
        a, b = c["normalized_span"]
        assert by_id[c["document_id"]]["text"][a:b] == c["text"]
        assert digest(c["text"].encode()) == c["content_hash"]
    assert inputs == [{"path": p.relative_to(snapshot).as_posix(), "sha256": digest(p.read_bytes())} for p in files]
    counts = dict(Counter(d["decision"] for d in decisions))
    validation = {"passed": True, "inventory": len(inventory), "documents": len(documents),
                  "chunks": len(chunks), "decisions": counts, "source_unchanged": True,
                  "evaluation_cases": len(evaluation), "evidence_cases": sum(c["document_id"] is not None for c in evaluation),
                  "oversized_chunks": sum(len(c["text"].encode()) > 2400 for c in chunks),
                  "human_academic_signoff": False, "retrieval_evaluated": False}
    write_json(output / "validation_report.json", validation)
    (output / "preparation_report.md").write_text(
        "# HUS preparation build\n\n" + json.dumps(validation, ensure_ascii=False, indent=2)
        + "\n\nSelected descriptive documents are a limited prepared subset. Full source review, PDF/OCR resolution, "
        "human academic sign-off and retrieval evaluation remain separate. See issues.jsonl.\n", encoding="utf-8")
    artifacts = {p.relative_to(output).as_posix(): digest(p.read_bytes()) for p in sorted(output.rglob("*")) if p.is_file()}
    write_json(output / "manifest.json", {"status": "prepared_candidate", "build_id": build_id,
                                          "pipeline_version": VERSION, "artifacts": artifacts, "statistics": validation})
    return validation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--cases", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.snapshot, args.output, args.review, args.cases), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
