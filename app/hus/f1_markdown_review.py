"""Explicitly authorized, Markdown-only F1 section approval; not original-source verification."""

from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.hus.corpus import (
    SourceManifest, file_bytes, json_bytes, jsonl_bytes, read_json, sha256, source_path,
    split_chunks, verify_sources,
)
from app.hus.f1_corpus import CANDIDATES, build_f1

EXCLUDED_ID = "1f6ad01008734152"
AUTHORIZED_IDS = set(CANDIDATES) - {EXCLUDED_ID}
POLICY = "user_authorized_descriptive_F1_from_markdown"


class SectionReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: Literal["introduction", "objectives", "careers", "further_study"]
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    quote_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def valid_span(self):
        if self.end <= self.start:
            raise ValueError("Empty Markdown review span")
        return self


class MarkdownDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["include_markdown"]
    scope: Literal["selected_F1_sections"]
    review_basis: Literal["extracted_markdown"]
    source_url: str
    source_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    markdown_path: str
    markdown_sha256_utf8_lf: str = Field(pattern=r"^[0-9a-f]{64}$")
    major: Literal["mathematics", "mathematics_informatics", "computer_science", "data_science"]
    program_variant: Literal["unknown", "standard", "high_quality", "talent", "advanced"]
    version_as_stated_in_markdown: str
    raw_original_verified: Literal[False]
    current_validity_verified: Literal[False]
    reviewer: str = Field(min_length=1)
    reviewed_at: str
    reason: str = Field(min_length=1)
    sections: list[SectionReview] = Field(min_length=1)
    extraction_notes: list[str]

    @field_validator("reviewer", "reason")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Review evidence cannot be blank")
        return value

    @field_validator("reviewed_at")
    @classmethod
    def aware_timestamp(cls, value: str) -> str:
        if datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is None:
            raise ValueError("Markdown review timestamp must include timezone")
        return value


class MarkdownReviewFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"]
    source_snapshot_id: str
    policy: Literal["user_authorized_descriptive_F1_from_markdown"]
    authorization_instruction: str = Field(min_length=1)
    excluded_document_ids: list[str]
    decisions: dict[str, MarkdownDecision]


def clean_display(quote: str) -> str:
    """Only omit extraction page markers/numbers; retain all substantive wording and glyphs."""
    lines = [line for line in quote.splitlines()
             if not re.fullmatch(r"\s*(?:<!--\s*Page\s+\d+\s*-->|\d{1,3})\s*", line)]
    return "\n".join(lines).strip()


def jsonl_rows(raw: bytes) -> list[dict]:
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def apply_markdown_review(base: dict[str, bytes], docs: dict, manifest: SourceManifest,
                          root: Path, decisions: MarkdownReviewFile) -> dict[str, bytes]:
    if decisions.source_snapshot_id != manifest.source_snapshot_id:
        raise ValueError("Markdown approval belongs to another snapshot")
    if set(decisions.decisions) != AUTHORIZED_IDS or decisions.excluded_document_ids != [EXCLUDED_ID]:
        raise ValueError("Markdown approval must cover exactly the ten authorized sources and exclude the careers page")
    if not decisions.authorization_instruction.strip():
        raise ValueError("Missing explicit authorization for Markdown-only F1")
    documents = jsonl_rows(base["documents.jsonl"])
    units = jsonl_rows(base["f1_units.jsonl"])
    chunks = jsonl_rows(base["rag_chunks.jsonl"])
    mapping = jsonl_rows(base["source_map.jsonl"])
    inventory = jsonl_rows(base["source_inventory.jsonl"])
    inventory_by_id = {r["document_id"]: r for r in inventory}
    original_ids = {r["document_id"] for r in documents}
    if original_ids & AUTHORIZED_IDS:
        raise ValueError("Markdown sources already occur in the base corpus")
    seen_content = {}
    merged_duplicates = 0
    for key, decision in sorted(decisions.decisions.items()):
        doc = docs[key]
        source = manifest.documents[key]
        markdown_hash = sha256(file_bytes(source_path(root, source.markdown_path), "utf8-lf"))
        if (decision.source_url != doc.url or decision.source_content_hash != doc.content_hash
            or decision.markdown_path != source.markdown_path or decision.markdown_sha256_utf8_lf != markdown_hash):
            raise ValueError(f"Stale or foreign Markdown approval: {key}")
        if decision.major != CANDIDATES[key][0]:
            raise ValueError("Markdown approval has a foreign major")
        expected_variant = CANDIDATES[key][1]
        if decision.program_variant != expected_variant:
            raise ValueError("Markdown approval has a foreign program variant")
        metadata = {
            "document_id": key, "title": doc.title, "source_url": doc.url,
            "major": decision.major, "program_variant": decision.program_variant,
            "program_version": decision.version_as_stated_in_markdown,
            "version_basis": "as_stated_in_extracted_markdown_not_raw_verified",
            "admission_cohort": "unknown", "validity_status": "unknown", "usage_scope": "descriptive",
            "markdown_path": source.markdown_path, "markdown_sha256_utf8_lf": markdown_hash,
            "raw_path": source.raw_path, "raw_sha256": None, "raw_original_verified": False,
            "source_content_hash": doc.content_hash, "review_status": "include_markdown",
            "review_scope": "selected_F1_sections", "review_basis": "extracted_markdown",
            "review": decision.model_dump(), "academic_verified": False,
            "content_origin": "crawled_markdown_quote", "answer_eligible": True,
        }
        context = (f"Nguồn Markdown đã crawl: {doc.title}. Ngành: {decision.major}; "
                   f"hệ: {decision.program_variant}; phiên bản ghi trong Markdown: {decision.version_as_stated_in_markdown}.\n"
                   "Đã duyệt dùng F1 mô tả theo yêu cầu người dùng; chưa đối chiếu PDF/DOCX gốc; "
                   "hiệu lực hiện tại chưa xác minh.\n")
        ranges, selected_quotes = [], []
        for section in decision.sections:
            start, end = section.start, section.end
            if end > len(doc.content) or any(start < b and a < end for a, b in ranges):
                raise ValueError("Markdown F1 spans exceed the source or overlap")
            ranges.append((start, end))
            quote = doc.content[start:end]
            if sha256(quote.encode()) != section.quote_sha256 or not clean_display(quote):
                raise ValueError("Markdown section text differs from reviewed quote")
            if any(line.lstrip().startswith("|") for line in quote.splitlines()):
                raise ValueError("F1 Markdown approval cannot import F2 tables")
            selected_quotes.append(quote)
            unit_id = sha256(f"{key}\n{start}\n{end}\n{quote}".encode())[:24]
            locator = {"field": "content_markdown", "start_char": start, "end_char": end,
                       "start_line": doc.content.count("\n", 0, start)+1,
                       "end_line": doc.content.count("\n", 0, end-1)+1}
            unit = {**metadata, "unit_id": unit_id, "field": section.field, "locator": locator,
                    "text": clean_display(quote), "source_quote": quote,
                    "display_transform": "omit_page_markers_and_isolated_page_numbers_only"}
            # Two CLC documents have identical F1 narratives; retain both source approvals,
            # index the shared text once within the same major/variant/edition/field.
            dedup_key = (decision.major, decision.program_variant, decision.version_as_stated_in_markdown,
                         section.field, " ".join(clean_display(quote).split()))
            if dedup_key in seen_content:
                first = seen_content[dedup_key]
                unit["retrieval_duplicate_of"] = first["unit_id"]
                alternate = {"document_id": key, "source_url": doc.url, "unit_id": unit_id,
                             "markdown_path": source.markdown_path, "locator": locator,
                             "markdown_sha256_utf8_lf": markdown_hash}
                for chunk in first["chunks"]:
                    chunk.setdefault("alternate_source_provenance", []).append(alternate)
                merged_duplicates += 1
                units.append(unit)
                continue
            units.append(unit)
            section_chunks = []
            for index, (a, b) in enumerate(split_chunks(quote, 2000)):
                raw_part = quote[a:b]
                display = clean_display(raw_part)
                if not display:
                    continue
                chunk_locator = {**locator, "start_char": start+a, "end_char": start+b,
                                 "start_line": doc.content.count("\n", 0, start+a)+1,
                                 "end_line": doc.content.count("\n", 0, start+b-1)+1}
                text = context + f"Nội dung F1: {section.field}.\n" + display
                chunk_id = sha256(f"{unit_id}:{index}\n{text}".encode())[:24]
                chunk = {**metadata, "unit_id": unit_id, "chunk_id": chunk_id, "field": section.field,
                         "text": text, "source_quote": raw_part, "locator": chunk_locator,
                         "citation_title": doc.title,
                         "display_transform": "omit_page_markers_and_isolated_page_numbers_only"}
                chunks.append(chunk)
                section_chunks.append(chunk)
                mapping.append({"chunk_id": chunk_id, "unit_id": unit_id, "document_id": key,
                                "source_url": doc.url, "locator": chunk_locator,
                                "markdown_sha256_utf8_lf": markdown_hash, "raw_original_verified": False,
                                "review_basis": "extracted_markdown", "review_scope": "selected_F1_sections"})
            seen_content[dedup_key] = {"unit_id": unit_id, "chunks": section_chunks}
        selected_text = "\n\n".join(clean_display(q) for q in selected_quotes)
        documents.append({**metadata, "content_markdown": selected_text,
                          "selected_content_sha256": sha256(selected_text.encode()),
                          "representation": "selected_F1_markdown_sections",
                          "selected_spans": [s.model_dump() for s in decision.sections]})
        inventory_by_id[key].update(
            disposition="answer_eligible", reason="user_authorized_F1_markdown_review_original_not_verified",
            review_status="include_markdown", review_basis="extracted_markdown", answer_eligible=True,
            raw_original_verified=False,
        )
    inventory_by_id[EXCLUDED_ID].update(
        disposition="excluded_from_F1", reason="user_requested_remove_mixed_Toan_Co_careers_page",
        review_status="exclude", answer_eligible=False,
    )
    result = {**base, "documents.jsonl": jsonl_bytes(documents), "f1_units.jsonl": jsonl_bytes(units),
              "rag_chunks.jsonl": jsonl_bytes(chunks), "source_map.jsonl": jsonl_bytes(mapping),
              "source_inventory.jsonl": jsonl_bytes(inventory), "pending_F1_sections.jsonl": b"",
              "markdown_review_decisions.json": json_bytes(decisions.model_dump())}
    questions = jsonl_rows(base["acceptance_questions.jsonl"])
    for q in questions:
        q["evidence_chunk_ids"] = [c["chunk_id"] for c in chunks if c["major"] == q["major"]
                                   and c["field"] == q["field"]
                                   and c["program_variant"] not in {"high_quality", "talent"}]
        q["answer_mode"] = "source_cited_descriptive_preserve_markdown_review_basis_and_edition"
        q["result"] = "pass" if q["evidence_chunk_ids"] else "fail"
    result["acceptance_questions.jsonl"] = jsonl_bytes(questions)
    previous_manifest = json.loads(base["manifest.json"])
    report = {**previous_manifest, "schema_version": "1.1", "approval_policy": POLICY,
              "source_documents": len(documents), "source_documents_raw_compared": len(original_ids),
              "source_documents_markdown_reviewed": len(decisions.decisions),
              "semantic_units": len(units), "rag_chunks": len(chunks),
              "pending_source_documents": 0, "pending_sections": 0,
              "excluded_document_ids": [EXCLUDED_ID], "deduplicated_markdown_units": merged_duplicates,
              "unit_counts_by_major": dict(sorted(Counter(u["major"] for u in units).items())),
              "unit_counts_by_field": dict(sorted(Counter(u["field"] for u in units).items())),
              "inventory_counts": dict(Counter(r["disposition"] for r in inventory)),
              "question_contracts": dict(Counter(q["result"] for q in questions)),
              "markdown_reviews_sha256": sha256(result["markdown_review_decisions.json"]),
              "markdown_extension_implementation_sha256": sha256(file_bytes(Path(__file__), "utf8-lf")),
              "outputs": {k: sha256(v) for k, v in sorted(result.items()) if k != "manifest.json"}}
    result["manifest.json"] = json_bytes(report)
    return result


def build_f1_with_markdown(root: Path, config: Path, selections: Path, review_path: Path) -> dict[str, bytes]:
    base = build_f1(root, config, selections)
    config_data = read_json(config)
    manifest = SourceManifest.model_validate(read_json(config.parent / config_data["source_manifest"]))
    docs = verify_sources(root, manifest)
    decisions = MarkdownReviewFile.model_validate(read_json(review_path))
    return apply_markdown_review(base, docs, manifest, root, decisions)
