"""F1 evidence units from fully reviewed crawled documents, plus a blocked-source inventory."""

from collections import Counter
import json
from pathlib import Path
import re

from app.hus.corpus import (
    BuildConfig, ReviewFile, SourceManifest, build_artifacts, file_bytes,
    json_bytes, jsonl_bytes, read_json, sha256, verify_sources,
)
from app.hus.metadata import ApplicabilityFile
from app.hus.scope_audit import evidence_lines, fold

F1_FIELDS = {"introduction", "objectives", "careers", "further_study"}

# These are concrete source findings, not filename/keyword guesses or approvals.
CANDIDATES = {
    "23a0c1df14a5708a": ("mathematics_informatics", "standard", "2015"),
    "1e3ad5f9915aa051": ("computer_science", "standard", "2015"),
    "89d4b39494d72217": ("mathematics", "standard", "2015"),
    "d4fae066858f0b94": ("mathematics", "talent", "2015"),
    "1c16ddf8a6f1f409": ("computer_science", "high_quality", "2019"),
    "8afffd3cada3d048": ("computer_science", "high_quality", "unknown"),
    "f7f470e712738589": ("computer_science", "standard", "2023"),
    "0dd9aaaeefcbd7d7": ("mathematics_informatics", "unknown", "unknown"),
    "31b55b4ee6f451a6": ("computer_science", "standard", "unknown"),
    "d006f60211246633": ("mathematics", "advanced", "2008"),
    "1f6ad01008734152": ("general", "unknown", "unknown"),
}


def line_spans(content: str) -> list[tuple[int, int]]:
    result, start = [], 0
    for line in content.splitlines(keepends=True):
        result.append((start, start + len(line.rstrip("\r\n"))))
        start += len(line)
    return result


def selected_spans(content: str, selection: dict) -> list[tuple[int, int]]:
    start, end = line_spans(content)[selection["line"]]
    text = content[start:end]
    if selection.get("before"):
        end = start + text.index(selection["before"])
        text = content[start:end]
    if selection.get("after"):
        start += text.index(selection["after"]) + len(selection["after"])
        text = content[start:end]
    if selection.get("from"):
        start += text.index(selection["from"])
        text = content[start:end]
    split = selection.get("split", "none")
    if split == "sentences":
        # Every result remains an exact contiguous source span. Do not synthesize prose.
        boundaries = [0] + [m.start(1) for m in re.finditer(r"[.!?]\s+(\S)", text)
                            if m.group(1).isupper()] + [len(text)]
    elif split == "semicolons":
        boundaries = [0] + [m.end() for m in re.finditer(r";\s*", text)] + [len(text)]
    elif split == "none":
        boundaries = [0, len(text)]
    else:
        raise ValueError("Unknown F1 semantic split method")
    result = []
    for a, b in zip(boundaries, boundaries[1:]):
        while a < b and text[a].isspace():
            a += 1
        while b > a and text[b-1].isspace():
            b -= 1
        if a < b:
            result.append((start+a, start+b))
    return result


def pending_units(document_id: str, doc) -> list[dict]:
    """Locate program sections, keeping all such excerpts outside the answer corpus."""
    if document_id == "1f6ad01008734152":
        return [{"field": "careers", "start": e["start"], "end": e["end"], "quote": e["quote"]}
                for e in evidence_lines(doc.content, r"^- nganh (?:toan hoc|toan - tin|may tinh)")]
    if document_id in {"0dd9aaaeefcbd7d7", "31b55b4ee6f451a6"}:
        return [{"field": "objectives", "start": 0, "end": len(doc.content), "quote": doc.content}]
    headings = evidence_lines(doc.content, r"muc tieu (?:dao tao|cua chuong trinh)|vi tri viec lam|cac vi tri cong tac|kha nang hoc tap")
    units = []
    for e in headings:
        # Heading only, no TOC page number or course-level goals.
        text = fold(e["quote"].strip()).lstrip("# ")
        if not re.match(r"(?:\d+\.\s*)?(?:muc tieu|vi tri|cac vi tri|kha nang)", text):
            continue
        if not re.match(r"\d+\.\s+", text):
            continue
        if re.search(r"\s\d+$", text):
            continue
        following = doc.content[e["end"]:]
        match = re.search(r"\n\s*(?:#{1,4}\s*)?[3-9]\.\s+[^\n]+", following)
        end = e["end"] + match.start() if match else min(len(doc.content), e["end"] + 1800)
        field = "objectives" if "muc tieu" in text else "further_study" if "kha nang" in text else "careers"
        units.append({"field": field, "start": e["start"], "end": end,
                      "quote": doc.content[e["start"]:end]})
    return units


def build_f1(root: Path, config_path: Path, selections_path: Path) -> dict[str, bytes]:
    config = BuildConfig.model_validate(read_json(config_path))
    manifest = SourceManifest.model_validate(read_json(config_path.parent / config.source_manifest))
    reviews = ReviewFile.model_validate(read_json(config_path.parent / config.review_decisions))
    metadata = ApplicabilityFile.model_validate(read_json(config_path.parent / config.applicability_metadata))
    docs = verify_sources(root, manifest)
    # No partial-document approval or raw/table gate override is introduced here.
    built = build_artifacts(root, manifest, reviews, config, metadata)
    approved = {r["document_id"]: r for r in map(json.loads, built["documents.jsonl"].splitlines())}
    plan = read_json(selections_path)
    if plan["source_snapshot_id"] != manifest.source_snapshot_id:
        raise ValueError("F1 selections belong to a different snapshot")
    plan_ids = {p["document_id"] for p in plan["sources"]}
    if len(plan_ids) != len(plan["sources"]) or plan_ids != set(approved):
        raise ValueError("F1 selection sources must match exactly the whole-document includes")
    units, chunks, mapping, source_documents = [], [], [], []
    selected = {}
    for source in plan["sources"]:
        key = source["document_id"]
        doc = docs[key]
        record = approved[key]
        if source["content_hash"] != doc.content_hash:
            raise ValueError("Stale F1 source selection")
        if record["major"] != source["major"]:
            raise ValueError("F1 source major differs from reviewed metadata")
        selected[key] = source
        used_ranges = []
        for selection in source["selections"]:
            if selection["field"] not in F1_FIELDS:
                raise ValueError("Not a supported program F1 field")
            for part_index, (start, end) in enumerate(selected_spans(doc.content, selection)):
                if any(start < b and a < end for a, b in used_ranges):
                    raise ValueError("Overlapping F1 selections would duplicate source text")
                used_ranges.append((start, end))
                text = doc.content[start:end]
                if not text.strip() or "](" in text or "<!-- Page" in text:
                    raise ValueError("F1 unit must be substantive narrative, not a discovery link")
                variant = selection.get("program_variant", source["program_variant"])
                field = selection.get("field_overrides", {}).get(str(part_index), selection["field"])
                if field not in F1_FIELDS:
                    raise ValueError("Not a supported program F1 field override")
                unit_id = sha256(f"{key}\n{start}\n{end}\n{text}".encode())[:24]
                locator = {"field": "content_markdown", "start_char": start, "end_char": end,
                           "start_line": doc.content.count("\n", 0, start)+1,
                           "end_line": doc.content.count("\n", 0, end-1)+1}
                unit = {"unit_id": unit_id, "document_id": key, "title": doc.title,
                        "source_url": doc.url, "markdown_path": manifest.documents[key].markdown_path,
                        "raw_path": manifest.documents[key].raw_path, "raw_sha256": record["raw_sha256"],
                        "source_content_hash": doc.content_hash, "major": source["major"],
                        "program_variant": variant, "program_version": "unknown", "admission_cohort": "unknown",
                        "field": field, "content_origin": "crawled_source_quote",
                        "review_scope": "whole_document", "review_status": "include", "review": record["review"],
                        "usage_scope": "descriptive", "validity_status": "unknown", "answer_eligible": True,
                        "locator": locator, "text": text}
                units.append(unit)
                context = (f"Nguồn crawl: {doc.title}. Phạm vi ngành: {source['major']}; hệ: {variant}.\n"
                           f"Nội dung F1: {field}. Chỉ mô tả theo nguồn đã lưu; "
                           "chưa xác minh phiên bản, khóa hoặc hiệu lực hiện tại.\n")
                chunk_id = sha256((unit_id + "\n" + context + text).encode())[:24]
                chunks.append({**unit, "chunk_id": chunk_id, "text": context+text,
                               "source_quote": text, "citation_title": doc.title})
                mapping.append({"chunk_id": chunk_id, "unit_id": unit_id, "document_id": key,
                                "source_url": doc.url, "locator": locator,
                                "source_content_hash": doc.content_hash, "raw_sha256": record["raw_sha256"],
                                "review_scope": "whole_document"})
        source_documents.append(record)
    inventory, candidates = [], []
    for key, doc in sorted(docs.items()):
        source = manifest.documents[key]
        if key in selected:
            disposition, reason = "answer_eligible", "whole_document_review_and_F1_locator_verified"
            applicable = [selected[key]["major"]]
        elif key in CANDIDATES:
            disposition = "quarantine"
            reason = "mixed_major_document_includes_out_of_scope_Toan_Co" if key == "1f6ad01008734152" else "original_attachment_missing_whole_document_review_required"
            applicable = (["mathematics", "mathematics_informatics", "computer_science"]
                          if key == "1f6ad01008734152" else [CANDIDATES[key][0]])
            for unit in pending_units(key, doc):
                candidates.append({"document_id": key, "source_url": doc.url, "title": doc.title,
                                   "source_content_hash": doc.content_hash, "markdown_path": source.markdown_path,
                                   "applicable_major_candidates": applicable,
                                   "variant_proposed": CANDIDATES[key][1], "version_proposed": CANDIDATES[key][2],
                                   "review_status": reviews.decisions[key].status, "answer_eligible": False,
                                   "reason": reason, **unit})
        else:
            disposition = "excluded_from_F1"
            reason = ("course_level_objectives_are_F3_not_program_F1" if key in {"bc0a1f59b7ab202c", "098df9e79c1391af"}
                      else "faculty_context_not_program_F1" if key in {"d771d9ef92ec2244", "d75f0faafa5605a4", "cc4a948adb689fd2", "88b416f27e334aec"}
                      else "no_reviewed_program_F1_evidence_news_graduate_discovery_or_unreadable")
            applicable = []
        inventory.append({"document_id": key, "title": doc.title, "source_url": doc.url,
                          "content_hash": doc.content_hash, "markdown_path": source.markdown_path,
                          "raw_path": source.raw_path, "raw_status": "pinned" if source.raw_path else "missing",
                          "disposition": disposition, "reason": reason, "applicable_major_candidates": applicable,
                          "review_status": reviews.decisions[key].status,
                          "answer_eligible": disposition == "answer_eligible"})
    questions = []
    for major in sorted({u["major"] for u in units}):
        for field in sorted(F1_FIELDS):
            evidence = [c for c in chunks if c["major"] == major and c["field"] == field
                        and c["program_variant"] not in {"high_quality", "talent"}]
            questions.append({"question_id": f"{major}:{field}", "major": major, "field": field,
                              "evidence_chunk_ids": [c["chunk_id"] for c in evidence],
                              "answer_mode": "source_cited_descriptive", "current_validity_verified": False,
                              "result": "pass" if evidence else "fail"})
    output = {"documents.jsonl": jsonl_bytes(source_documents), "f1_units.jsonl": jsonl_bytes(units),
              "rag_chunks.jsonl": jsonl_bytes(chunks), "source_map.jsonl": jsonl_bytes(mapping),
              "source_inventory.jsonl": jsonl_bytes(inventory), "pending_F1_sections.jsonl": jsonl_bytes(candidates),
              "acceptance_questions.jsonl": jsonl_bytes(questions)}
    output["manifest.json"] = json_bytes({
        "schema_version": "1.0", "source_snapshot_id": manifest.source_snapshot_id,
        "corpus_build_id": json.loads(built["manifest.json"])["build_id"],
        "source_documents": len(source_documents), "semantic_units": len(units), "rag_chunks": len(chunks),
        "unit_counts_by_major": dict(sorted(Counter(u["major"] for u in units).items())),
        "unit_counts_by_field": dict(sorted(Counter(u["field"] for u in units).items())),
        "inventory_counts": dict(Counter(r["disposition"] for r in inventory)),
        "pending_source_documents": len(CANDIDATES), "pending_sections": len(candidates),
        "generated_F1_units": 0, "active_release": False,
        "selection_plan_sha256": sha256(file_bytes(selections_path, "utf8-lf")),
        "implementation_sha256": sha256(file_bytes(Path(__file__), "utf8-lf")),
        "question_contracts": dict(Counter(q["result"] for q in questions)),
        "outputs": {k: sha256(v) for k, v in sorted(output.items())},
    })
    return output
