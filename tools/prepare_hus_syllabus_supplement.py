"""Recover omitted syllabus sections into review-only candidates, with exact quotes."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from app.hus.release_text import fold
from tools.audit_hus_source_review import (
    RELEASE,
    ROOT,
    audit_span,
    captured_context,
    check_binary_hash,
    digest,
    pdf_texts,
    read_rows,
    require,
    write_json,
    write_rows,
)

HEADER = re.compile(r"(?im)^[ \t]*ĐỀ\s+CƯƠNG\s+HỌC\s+PHẦN[ \t]*$")
NUMBERED = re.compile(r"(?m)^[ \t]*(\d{1,2})\.[ \t]*(?:\n[ \t]*)?([^\n\d][^\n]*)")


def course_blocks(text):
    starts = [m.start() for m in HEADER.finditer(text)]
    return [(start, starts[i + 1] if i + 1 < len(starts) else len(text)) for i, start in enumerate(starts)]


def candidate_block(candidate, blocks):
    spans = [s for values in candidate["fields"].values() for s in values]
    require(bool(spans), "candidate lacks an anchor")
    anchor = min(s["start_char"] for s in spans)
    matched = [(a, b) for a, b in blocks if a <= anchor < b]
    require(len(matched) == 1, "candidate course boundary ambiguous")
    a, b = matched[0]
    require(all(a <= s["start_char"] < s["end_char"] <= b for s in spans),
            "existing candidate spans cross course boundary")
    return a, b


def missing_section(context, bounds, field):
    a, b = bounds
    block = context["joined"][a:b]
    headings = list(NUMBERED.finditer(block))
    patterns = {
        "assessment": r"^(?:kiem tra[ ,\-]*danh gia|phuong phap(?:, hinh thuc)? kiem tra[ ,\-]*danh gia)",
        "objectives": r"^muc tieu(?: cua)?(?: hoc phan| cua hoc phan)",
        "content": r"^tom tat noi dung hoc phan",
    }
    matches = [h for h in headings if re.search(patterns[field], fold(h.group(2)))]
    if len(matches) != 1:
        return None, "heading_absent_or_ambiguous"
    head = matches[0]
    successors = [h for h in headings if h.start() > head.start() and int(h.group(1)) == int(head.group(1)) + 1]
    # Without a following section heading, do not absorb the rest of a course.
    if not successors:
        return None, "section_end_not_located"
    end = successors[0].start()
    body = block[head.end():end]
    if sum(c.isalpha() for c in body) < 20:
        return None, "heading_present_but_body_empty_or_insufficient"
    start, finish = a + head.start(), a + end
    while start < finish and context["joined"][start].isspace():
        start += 1
    while finish > start and context["joined"][finish - 1].isspace():
        finish -= 1
    pages = [page for first, last, page in context["intervals"] if first < finish and last > start]
    return {"start_char": start, "end_char": finish, "source_quote": context["joined"][start:finish],
            "pdf_pages": pages, "offset_scope": "joined_source_pages_with_one_newline_each"}, None


def run(out):
    out = Path(out).resolve()
    require(any(out.is_relative_to(base) and out != base for base in [ROOT / "data/hus/review", ROOT / "backups"]),
            "supplement output must be a dedicated review/backups directory")
    require(not out.exists(), "supplement output exists")
    baseline = ROOT / "data/hus/review/p13_source_audit_v1"
    source_pins = json.loads((baseline / "report.json").read_bytes())["source_inputs_sha256"]
    for name, sha in source_pins.items():
        path = (ROOT / name).resolve()
        require(path.is_relative_to(ROOT), "source path escape")
        check_binary_hash(path.read_bytes(), sha)
    groups = defaultdict(list)
    for row in read_rows(RELEASE / "evidence/recovered_text.jsonl"):
        groups[row["document_id"]].append(row)
    candidates = read_rows(RELEASE / "source_syllabi.jsonl")
    contexts, blocks, physical = {}, {}, {}
    for row in candidates:
        cid = row["document_id"]
        if cid in contexts:
            continue
        contexts[cid] = captured_context(groups[cid], row["raw_sha256"])
        blocks[cid] = course_blocks(contexts[cid]["joined"])
        raw = (ROOT / f"backups/hus_source_review/p13/originals/{row['raw_sha256']}.pdf").read_bytes()
        check_binary_hash(raw, row["raw_sha256"])
        physical[cid] = pdf_texts(raw)
    supplements, unresolved, owned = [], [], defaultdict(set)
    before = Counter(field for c in candidates for field in c["fields"])
    for candidate in candidates:
        cid = candidate["document_id"]
        bounds = candidate_block(candidate, blocks[cid])
        require(bounds not in owned[cid], "multiple candidates own one course block")
        owned[cid].add(bounds)
        for field in sorted(set(["content", "objectives", "assessment"]) - set(candidate["fields"])):
            span, reason = missing_section(contexts[cid], bounds, field)
            common = {"candidate_id": candidate["candidate_id"], "document_id": cid,
                      "raw_sha256": candidate["raw_sha256"], "source_major": candidate["source_major"],
                      "source_publication_year": candidate["source_publication_year"], "field": field,
                      "course_code_as_printed": candidate["course_code_as_printed"],
                      "academic_verified": False, "default_retrieval_enabled": False,
                      "assessment_weights_parsed": None, "reviewer": None, "reviewed_at": None}
            if span is None:
                unresolved.append({**common, "reason": reason})
                continue
            check = audit_span(span, contexts[cid], len(physical[cid]), physical[cid])
            require(all(check[k] for k in ["offset_scope_valid", "capture_quote_match", "capture_pages_match", "physical_pages_valid"]),
                    "supplement quote/page trace mismatch")
            supplements.append({**common, "span": span, "trace_check": check,
                                "course_start_char": bounds[0], "course_end_char": bounds[1],
                                "identity_issues": candidate["identity_issues"],
                                "review_status": "source_section_supplement_pending_visual_identity_and_edition_review",
                                "answer_policy": "candidate_not_in_default_retrieval"})
    unmatched = [{"document_id": cid, "start_char": a, "end_char": b,
                  "header_excerpt": contexts[cid]["joined"][a:min(a + 260, b)],
                  "pdf_pages": [page for first, last, page in contexts[cid]["intervals"] if first < b and last > a],
                  "review_status": "unassigned_source_header_requires_inventory_review", "academic_verified": False}
                 for cid, values in blocks.items() for a, b in values if (a, b) not in owned[cid]]
    after = before + Counter(row["field"] for row in supplements)
    for name, sha in source_pins.items():
        check_binary_hash((ROOT / name).read_bytes(), sha)
    out.mkdir(parents=True)
    write_rows(out / "field_supplements.jsonl", supplements)
    write_rows(out / "unresolved_fields.jsonl", unresolved)
    write_rows(out / "unassigned_headers.jsonl", unmatched)
    summary = {"existing_candidates": len(candidates), "source_headers": sum(map(len, blocks.values())),
               "unassigned_headers": len(unmatched), "new_field_quotes": len(supplements),
               "fields_added_for_review": dict(Counter(r["field"] for r in supplements)),
               "original_fields_found": dict(before), "combined_candidate_field_coverage": dict(after),
               "unresolved_field_slots": len(unresolved),
               "PDFium_quote_match": sum(s["trace_check"]["reextracted_quote_found"] is True for s in supplements),
               "academic_reviews_added": 0, "official_F3_enabled": False, "runtime_modified": False}
    write_json(out / "report.json", summary)
    write_json(out / "manifest.json", {"tool_sha256": digest(Path(__file__).read_bytes()),
               "source_inputs_sha256": source_pins,
               "files_sha256": {p.name: digest(p.read_bytes()) for p in out.iterdir() if p.is_file()}})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    print(json.dumps(run(parser.parse_args().out)))
