"""Reproducible F1/F2/F3 triage, never an authority to approve source documents."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import unicodedata

from app.hus.cleaning import infer_major
from app.hus.corpus import (
    BuildConfig, ReviewFile, SourceManifest, build_artifacts, file_bytes,
    json_bytes, jsonl_bytes, read_json, sha256, source_path, verify_sources,
)
from app.hus.metadata import ApplicabilityFile
from app.hus.models import HUSDocument

MAJORS = ("mathematics", "mathematics_informatics", "computer_science", "data_science")
MAJOR_NAMES = dict(zip(MAJORS, ("Toán học", "Toán tin", "Khoa học máy tính và thông tin", "Khoa học dữ liệu")))
FIELDS = {
    "F1": ("introduction", "objectives", "careers"),
    "F2": ("framework", "courses", "credits", "prerequisites"),
    "F3": ("content", "objectives", "assessment"),
}
PATTERNS = {
    "introduction": r"chuong trinh dao tao|nganh dao tao|nganh khoa hoc du lieu",
    "objectives": r"muc tieu(?: dao tao| hoc phan| chung| cu the)?|chuan dau ra",
    "careers": r"vi tri viec lam|co hoi viec lam|nghe nghiep",
    "framework": r"khung chuong trinh|khoi kien thuc",
    "courses": r"ma hoc phan|ma hp|ma mon hoc",
    "credits": r"so tin chi",
    "prerequisites": r"tien quyet|hoc truoc|song hanh",
    "content": r"(?:tom tat )?noi dung (?:chi tiet )?(?:cua )?hoc phan",
    "assessment": r"phuong (?:phap|thuc).*(?:kiem tra|danh gia)|hinh thuc.*danh gia",
}
CODE = r"[A-Z]{3}\d{4}[A-Z]?"


def fold(value: str) -> str:
    value = value.lower().replace("đ", "d").replace("ƣ", "u").replace("Ƣ", "u")
    return "".join(c for c in unicodedata.normalize("NFKD", value)
                   if not unicodedata.combining(c))


def evidence_lines(text: str, pattern: str, *, narrative: bool = False) -> list[dict]:
    """Exact content offsets; ignore link-only discoveries and TOC dot leaders."""
    rows, start = [], 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        discovery = stripped.startswith(("- [", "[", "<!--")) or "...." in line
        if (not discovery and (not narrative or not stripped.startswith("|"))
                and re.search(pattern, fold(line))):
            rows.append({"field": "content_markdown", "start": start,
                         "end": start + len(line.rstrip("\r\n")),
                         "quote": line.rstrip("\r\n")})
        start += len(line)
    return rows


def classify(doc: HUSDocument) -> dict:
    """Content and heading context jointly decide triage; unknown remains unverified."""
    body = doc.content
    # Cover/lead only: later references to further study do not change degree level.
    lead = body[:1800]
    lead_plain = "\n".join(line for line in lead.splitlines() if "](" not in line)
    # Evidence offsets refer to the original body, not the filtered lead.
    level_evidence = evidence_lines(body, r"trinh do (?:dai hoc|thac si|tien si)|cu nhan")[:4]
    normalized = fold(lead_plain)
    if re.search(r"trinh do thac si|dao tao thac si", normalized):
        level = "master"
    elif re.search(r"trinh do tien si|dao tao tien si", normalized):
        level = "doctoral"
    elif re.search(r"trinh do dai hoc|cu nhan|dao tao dai hoc|bac dai hoc", normalized):
        level = "undergraduate"
    else:
        level = "unknown"
    # Explicit graduate-only landing pages, with narrative corroboration.
    if re.search(r"thac si|tien si|sau dai hoc", fold(doc.title)) and (
        "cao hoc" in fold(body) or "thac si" in fold(body) or "tien si" in fold(body)
    ):
        level = "doctoral" if "tien si" in fold(doc.title) else "master"
    major = infer_major(doc.title, doc.url, body).value
    signals = {name: evidence_lines(body, pattern) for name, pattern in PATTERNS.items()}
    groups = []
    if level == "undergraduate" and any(signals[n] for n in FIELDS["F1"]):
        groups.append("F1")
    # A link to a curriculum is discovery, not curriculum data.
    has_courses = bool(re.search(rf"\|\s*{CODE}\s*\||[Mm]ã học phần\s*:", body))
    if level not in {"master", "doctoral"} and has_courses and signals["credits"]:
        groups.append("F2")
    if level not in {"master", "doctoral"} and has_courses and signals["content"]:
        groups.append("F3")
    if (level not in {"master", "doctoral"} and "F2" not in groups
        and len(re.findall(CODE, body)) >= 3
        and (("hoc ki" in fold(body[:300]) and "curriculummap" in doc.url.lower())
             or ("ma tran chuan dau ra" in fold(body[:500]) and signals["courses"]))):
        groups.append("F2")
    # Explicit scope from a cover must not be inherited from a filename alone.
    if groups and level == "unknown":
        disposition, reason = "quarantine", "degree_unverified_content_candidates_only"
    elif major not in MAJORS and groups:
        disposition, reason = "quarantine", "unknown_or_shared_major_needs_applicability_review"
    elif level in {"master", "doctoral"}:
        disposition, reason = "exclude", "graduate_program_outside_undergraduate_F1_F3"
    elif major == "out_of_scope":
        disposition, reason = "exclude", "unrelated_major"
    elif groups:
        disposition, reason = "retain_candidate", "undergraduate_content_evidence_requires_review"
    elif doc.status.value == "pending_ocr":
        disposition, reason = "quarantine", "scan_no_readable_content_or_degree_version_evidence"
    else:
        disposition, reason = "exclude", "no_substantive_undergraduate_F1_F2_F3_evidence"
    if re.search(r"^(su menh|triet ly|loi chao|gioi thieu$|bac dao tao$)", fold(doc.title)):
        disposition, reason = "exclude", "institutional_information_not_major_program_evidence"
        groups = []
    # A full page with distinct program variants/degree descriptions cannot be sliced here.
    mixed = len(set(re.findall(r"trinh do (dai hoc|thac si|tien si)", fold(body[:3000])))) > 1
    if mixed and groups:
        disposition, reason = "quarantine", "mixed_degree_document_whole_document_gate"
    version_evidence = evidence_lines(lead, r"ha noi[^\n]{0,15}20\d{2}")
    years = re.findall(r"20\d{2}", version_evidence[0]["quote"]) if version_evidence else []
    version = years[-1] if len(set(years)) == 1 else "unknown"
    variant = next((v for p, v in ((r"chuong trinh[^.\n]{0,90}(?:chat luong cao|\bclc\b)", "CLC"),
                                 (r"chuong trinh (?:dao tao )?tien tien", "advanced"),
                                 (r"chuong trinh[^.\n]{0,50}tai nang", "talented"),
                                 (r"chuong trinh dao tao chuan", "standard"))
                    if re.search(p, normalized)), "unknown")
    return {
        "major_proposed": major, "education_level_proposed": level,
        "program_version_proposed": version, "program_variant_proposed": variant,
        "admission_cohort": "unknown", "validity": "unknown", "groups": groups,
        "disposition": disposition, "reason": reason,
        "evidence": {"education_level": level_evidence, "version": version_evidence,
                     **{name: rows[:4] for name, rows in signals.items()}},
        "classification_method": "content_context_v1_proposal_only",
    }


def table_courses(doc: HUSDocument) -> list[dict]:
    """Keep source rows as candidates; do not infer AND/OR or empty prerequisite meaning."""
    result, offset, columns, header = [], 0, None, None
    for line in doc.content.splitlines(keepends=True):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|"):
            normalized = [re.sub(r"\s+", " ", fold(c.replace("<br>", " "))) for c in cells]
            codes = [i for i, c in enumerate(normalized) if c in {"ma hoc phan", "ma hp", "ma mon hoc"}]
            credits = [i for i, c in enumerate(normalized) if c in {"so tin chi", "so tc"}]
            names = [i for i, c in enumerate(normalized) if c in {"hoc phan", "ten hoc phan"}]
            if codes:
                # A CDR/Bloom matrix or foreign-program comparison is not a credit table.
                columns = (codes[0], names[0], credits[0]) if len(codes) == 1 and names and len(credits) == 1 else None
                header = line.rstrip()
            if columns and max(columns) < len(cells):
                code_col, name_col, credit_col = columns
                if re.fullmatch(CODE, cells[code_col]) and re.fullmatch(r"\d+", cells[credit_col]):
                    result.append({"code": cells[code_col], "name_raw": cells[name_col],
                                   "credits_raw": cells[credit_col], "header_raw": header,
                                   "row_raw": line.rstrip(), "start": offset,
                                   "end": offset + len(line.rstrip("\r\n")),
                                   "prerequisite_interpretation": "unknown",
                                   "relation_types_verified": False,
                                   "source_status": "extracted_unverified"})
        elif line.strip() and not line.lstrip().startswith("<!-- Page") and not line.strip().isdigit():
            columns = None
        offset += len(line)
    return result


def syllabus_courses(doc: HUSDocument) -> list[dict]:
    """Field-presence evidence within each explicit course-code section, not verified F3."""
    markers = list(re.finditer(rf"(?im)^[^\n]{{0,30}}Mã (?:học phần|môn học)\s*[:：]\s*({CODE}|\d{{4}})\b", doc.content))
    result = []
    for i, marker in enumerate(markers):
        end = markers[i+1].start() if i+1 < len(markers) else len(doc.content)
        text = doc.content[marker.start():end]
        fields = {}
        for name in FIELDS["F3"]:
            matches = evidence_lines(text, PATTERNS[name])
            # A heading alone is insufficient: record bounded excerpt and leave unreviewed.
            fields[name] = [{**e, "start": e["start"] + marker.start(),
                             "end": e["end"] + marker.start()} for e in matches[:2]]
        result.append({"code": marker.group(1), "start": marker.start(), "end": end,
                       "fields": fields, "source_status": "extracted_unverified",
                       "code_status": "candidate" if re.fullmatch(CODE, marker.group(1)) else "malformed_unresolved",
                       "answer_eligible": False, "program_applicability": "unknown"})
    return result


def catalog_inventory(root: Path) -> list[dict]:
    """Only versioned product catalogs; tests/fixtures are deliberately never searched."""
    result = []
    for path in sorted(root.glob("*/courses.json")):
        envelope = read_json(path)
        curriculum = read_json(path.with_name("curriculum.json"))
        rows = read_json(path.with_name("source_rows.json"))
        courses = envelope["courses"] if isinstance(envelope, dict) else envelope
        by_code = {r["code"]: r for r in rows}
        for i, course in enumerate(courses):
            result.append({
                "program_id": curriculum["program_id"], "catalog_revision": curriculum.get("catalog_revision"),
                "source_path": path.as_posix(), "pointer": f"/courses/{i}",
                "input_sha256_utf8_lf": sha256(file_bytes(path, "utf8-lf")),
                "curriculum_path": path.with_name("curriculum.json").as_posix(),
                "source_rows_path": path.with_name("source_rows.json").as_posix(),
                "code": course["code"], "name": course["name"], "credits": course["credits"],
                "source_page": course.get("source_page"), "source_rows": course.get("source_rows"),
                "prerequisites_raw": course.get("prerequisites_raw"),
                "prerequisites_transcribed": course.get("prerequisites"),
                "prerequisite_answer_status": "unknown",
                "prerequisite_source_status": course.get("prerequisite_status", "unknown"),
                "external_prerequisite_codes": course.get("external_prerequisite_codes", []),
                "source_status": course.get("source_status", "unknown"),
                "source_sha256_claim": curriculum.get("source_sha256"),
                "field_evidence": course.get("field_evidence", {}),
                "row_matches": all(course[n] == by_code.get(course["code"], {}).get(n)
                                   for n in ("code", "name", "credits")),
                "source_issues": curriculum.get("source_issues", []),
                "relation_types_verified": False, "answer_eligible": False,
            })
    return result


def validate_experimental(path: Path, catalog: list[dict]) -> list[dict]:
    """Generated examples have their own evidence contract and can never grant source review."""
    data = read_json(path)
    if (data.get("generation_status") != "inferred" or data.get("verified") is not False
        or data.get("reviewer") is not None or data.get("answer_corpus_eligible") is not False
        or data.get("review_status") != "needs_review" or not data.get("warning")
        or not data.get("method")):
        raise ValueError("Experimental data must remain explicitly inferred and unapproved")
    result = []
    seen = set()
    for example in data["courses"]:
        key = (data["program_id"], example["code"])
        if key in seen:
            raise ValueError("Duplicate experimental course")
        seen.add(key)
        source = next((c for c in catalog if (c["program_id"], c["code"]) == key), None)
        if source is None or any((
            source["source_path"] != data["input_source"],
            source["input_sha256_utf8_lf"] != data["input_sha256_utf8_lf"],
            source["catalog_revision"] != data["catalog_revision"],
            source["pointer"] != example["input_pointer"],
            source["name"] != example["input_name"], source["credits"] != example["input_credits"],
            source["prerequisites_raw"] != example["input_prerequisites_raw"],
        )):
            raise ValueError("Experimental example has stale or foreign F2 inputs")
        if any(example.get(name) is not None for name in
               ("official_content", "official_objectives", "official_assessment")):
            raise ValueError("Inferred example cannot assert official syllabus facts")
        for field in FIELDS["F3"]:
            result.append({"program_id": data["program_id"], "code": example["code"], "field": field,
                           "status": "generated_only" if example.get("inferred_" + field) else "missing_source",
                           "source_label": "inferred", "answer_eligible": False,
                           "input_source": data["input_source"], "input_pointer": example["input_pointer"],
                           "method": data["method"]})
    return result


def audit(root: Path, config_path: Path, catalogs: Path, experimental: Path | None = None) -> dict[str, bytes]:
    config = BuildConfig.model_validate(read_json(config_path))
    manifest = SourceManifest.model_validate(read_json(config_path.parent / config.source_manifest))
    reviews = ReviewFile.model_validate(read_json(config_path.parent / config.review_decisions))
    metadata = (ApplicabilityFile.model_validate(read_json(config_path.parent / config.applicability_metadata))
                if config.applicability_metadata else None)
    docs = verify_sources(root, manifest)
    # Reuse the complete existing review/quality gate and corpus byte reproduction.
    built = build_artifacts(root, manifest, reviews, config, metadata)
    exported = {r["document_id"] for r in read_jsonl_bytes(built["documents.jsonl"])}
    raw_inventory = {r["document_id"]: r for r in read_jsonl_bytes(built["inventory.jsonl"])}
    classifications, f2, f3, filtered = [], [], [], []
    for key, doc in sorted(docs.items()):
        source = manifest.documents[key]
        row = {"document_id": key, "source_url": doc.url, "title": doc.title,
               "content_hash": doc.content_hash, "markdown_path": source.markdown_path,
               "raw_path": source.raw_path, "raw_status": "pinned" if source.raw_path else "missing",
               "review_status": reviews.decisions[key].status,
               "review": reviews.decisions[key].model_dump(),
               "quality_flags": raw_inventory[key]["flags"],
               "quality_report_available": raw_inventory[key]["source_quality_sha256"] is not None,
               "source_comparison_review_recorded": bool(reviews.decisions[key].reviewed_source_sha256),
               "major_verified": raw_inventory[key]["major"],
               **classify(doc)}
        row["answer_eligible"] = (key in exported and row["disposition"] == "retain_candidate"
                                  and row["major_verified"] in MAJORS)
        row["exported_to_candidate_corpus"] = key in exported
        classifications.append(row)
        if row["answer_eligible"]:
            filtered.extend(r for r in read_jsonl_bytes(built["documents.jsonl"]) if r["document_id"] == key)
        shared = {"document_id": key, "source_url": doc.url, "content_hash": doc.content_hash,
                  "major_proposed": row["major_proposed"], "version_proposed": row["program_version_proposed"],
                  "variant_proposed": row["program_variant_proposed"],
                  "markdown_path": source.markdown_path, "review_status": row["review_status"]}
        if "F2" in row["groups"]:
            f2.extend({**shared, **r} for r in table_courses(doc))
        if "F3" in row["groups"]:
            f3.extend({**shared, **r} for r in syllabus_courses(doc))
    catalog = catalog_inventory(catalogs)
    coverage = []
    for major in MAJORS:
        editions = {(r["program_version_proposed"], r["program_variant_proposed"]) for r in classifications
                    if r["major_proposed"] == major and r["disposition"] != "exclude"} | {("unknown", "unknown")}
        if major == "data_science" and catalog:
            editions.add(("2022", "unknown"))
        for version, variant in sorted(editions):
            relevant = [r for r in classifications if r["major_proposed"] == major
                        and r["program_version_proposed"] == version and r["program_variant_proposed"] == variant
                        and r["disposition"] != "exclude"]
            for group, fields in FIELDS.items():
                for field in fields:
                    evidence = [r for r in relevant if group in r["groups"] and r["evidence"][field]]
                    usable = [r for r in evidence if r["answer_eligible"]]
                    cat = catalog if major == "data_science" and version == "2022" and variant == "unknown" and group == "F2" else []
                    status = ("sufficient_verified_source" if usable and group == "F1"
                              else "partial" if usable else "data_not_usable" if evidence or cat else "missing_source")
                    coverage.append({"major": major, "program_version": version, "program_variant": variant, "group": group,
                                     "question_type": field, "status": status,
                                     "document_ids": [r["document_id"] for r in evidence],
                                     "usable_document_ids": [r["document_id"] for r in usable],
                                     "catalog_records": [r["pointer"] for r in cat],
                                     "applicability": "descriptive_only_version_unknown" if version == "unknown" else "edition_proposed_not_cohort_verified",
                                     "coverage_denominator": None,
                                     "denominator_reason": "No reviewed complete canonical course list for this major/edition",
                                     "limitation": "No current rules, offering or cohort applicability verified; empty prerequisites remain unknown"})
    gaps = [{**r, "priority": 1 if r["major"] in {"mathematics_informatics", "data_science"} else 2,
             "next_action": "Retrieve original / verify edition, degree and field evidence, then whole-document review"}
            for r in coverage if r["status"] != "sufficient_verified_source"]
    questions = []
    for major in MAJORS:
        for group, fields in FIELDS.items():
            rows = [r for r in coverage if r["major"] == major and r["group"] == group
                    and r["program_version"] == "unknown" and r["program_variant"] == "unknown"]
            answerable = [r["question_type"] for r in rows if r["usable_document_ids"]]
            question = {
                "F1": f"Ngành {MAJOR_NAMES[major]} đào tạo về gì, có mục tiêu và định hướng nghề nghiệp nào?",
                "F2": f"Khung chương trình ngành {MAJOR_NAMES[major]} gồm những môn, tín chỉ và điều kiện tiên quyết nào; áp dụng phiên bản nào?",
                "F3": f"Có thể tra nội dung, mục tiêu và hình thức đánh giá chính thức của từng học phần ngành {MAJOR_NAMES[major]} chưa?",
            }[group]
            questions.append({"question_id": f"{major}-{group}", "major": major, "version": "unknown",
                              "group": group, "question": question,
                              "source_document_ids": sorted({k for r in rows for k in r["document_ids"]}),
                              "other_edition_candidate_ids": sorted({k for r in coverage
                                  if r["major"] == major and r["group"] == group for k in r["document_ids"]}),
                              "catalog_evidence": ([r["source_path"] + "#" + r["pointer"] for r in catalog]
                                                   if major == "data_science" and group in {"F2", "F3"} else []),
                              "answerable_fields": answerable,
                              "must_disclose_missing": [f for f in fields if f not in answerable],
                              "enough_data": len(answerable) == len(fields),
                              "source_label": "official_source" if answerable else "unavailable_or_unreviewed",
                              "allowed_answer": "Có thể mô tả theo bài giới thiệu đã đối chiếu; không khẳng định phiên bản hoặc hiệu lực hiện tại."
                                  if answerable else "Chưa đủ dữ liệu nguồn được duyệt. Chỉ được báo vị trí và trạng thái của dữ liệu ứng viên, không xác nhận dữ kiện học vụ.",
                              "result": "pass" if all(r["status"] != "sufficient_verified_source" or r["usable_document_ids"] for r in rows) else "fail",
                              "check_method": "offline_evidence_contract_not_retrieval_or_LLM_evaluation"})
    filtered_ids = {r["document_id"] for r in filtered}
    chunks = [r for r in read_jsonl_bytes(built["chunks.jsonl"]) if r["document_id"] in filtered_ids]
    outputs = {"classification.jsonl": jsonl_bytes(classifications),
               "f2_catalog_records.jsonl": jsonl_bytes(catalog), "f2_source_rows.jsonl": jsonl_bytes(f2),
               "f3_source_fields.jsonl": jsonl_bytes(f3), "coverage.jsonl": jsonl_bytes(coverage),
               "source_gaps.jsonl": jsonl_bytes(gaps), "acceptance_questions.jsonl": jsonl_bytes(questions),
               "answer_documents.jsonl": jsonl_bytes(filtered), "answer_chunks.jsonl": jsonl_bytes(chunks)}
    outputs["answer_source_map.jsonl"] = jsonl_bytes([
        row for row in read_jsonl_bytes(built["source_map.jsonl"]) if row["document_id"] in filtered_ids
    ])
    for key in sorted(filtered_ids):
        name = f"normalized/{key}.md"
        outputs[name] = built[name]
    per_course = [{"document_id": r["document_id"], "major_proposed": r["major_proposed"],
                   "version_proposed": r["version_proposed"], "code": r["code"],
                   "field": field, "status": "data_not_usable" if r["fields"][field] else "missing_source",
                   "evidence": r["fields"][field], "answer_eligible": False,
                   "limitation": "Field heading presence only; original/degree/version/whole-document review required"}
                  for r in f3 for field in FIELDS["F3"]]
    per_course.extend({"program_id": r["program_id"], "major_proposed": "data_science",
                       "version_proposed": "2022", "code": r["code"], "field": field,
                       "status": "missing_source", "evidence": [], "answer_eligible": False}
                      for r in catalog for field in FIELDS["F3"])
    mapped = {(r["document_id"], r["code"]) for r in f3}
    classified_by_id = {r["document_id"]: r for r in classifications}
    for doc_id, code in sorted({(r["document_id"], r["code"]) for r in f2} - mapped):
        source = classified_by_id[doc_id]
        for field in FIELDS["F3"]:
            per_course.append({"document_id": doc_id, "major_proposed": source["major_proposed"],
                               "version_proposed": source["program_version_proposed"], "code": code,
                               "field": field, "status": "data_not_usable" if "F3" in source["groups"] else "missing_source",
                               "evidence": [], "answer_eligible": False,
                               "limitation": "F2 course row exists; syllabus field not mapped. This does not prove absence in the original."})
    outputs["f3_course_coverage.jsonl"] = jsonl_bytes(per_course)
    checks = []
    for key in sorted({(r["document_id"], r["code"]) for r in f2}):
        records = [r for r in f2 if (r["document_id"], r["code"]) == key]
        credit_values = sorted({r["credits_raw"] for r in records})
        checks.append({"document_id": key[0], "code": key[1], "occurrences": len(records),
                       "credits_candidates": credit_values, "credit_conflict": len(credit_values) > 1,
                       "name_candidates": sorted({r["name_raw"] for r in records}),
                       "answer_eligible": False, "completeness": "unknown_no_reviewed_denominator"})
    outputs["f2_course_checks.jsonl"] = jsonl_bytes(checks)
    extraction_issues = [{"document_id": r["document_id"], "code_raw": r["code"],
                          "start": r["start"], "end": r["end"], "reason": r["code_status"],
                          "next_action": "Compare original; do not guess code prefix", "answer_eligible": False}
                         for r in f3 if r["code_status"] != "candidate"]
    for row in classifications:
        if "F2" in row["groups"] and not any(r["document_id"] == row["document_id"] for r in f2):
            extraction_issues.append({"document_id": row["document_id"], "reason": "F2_table_not_mapped",
                                      "markdown_path": row["markdown_path"],
                                      "next_action": "Inspect original table headers/rotated text/code layout; do not infer credit columns",
                                      "answer_eligible": False})
    for doc_id, code in sorted({(r["document_id"], r["code"]) for r in f3}):
        entries = [r for r in f3 if (r["document_id"], r["code"]) == (doc_id, code)]
        if len(entries) > 1:
            extraction_issues.append({"document_id": doc_id, "code_raw": code,
                                      "reason": "duplicate_syllabus_code", "occurrences": len(entries),
                                      "next_action": "Compare original; do not merge course identities",
                                      "answer_eligible": False})
    outputs["extraction_issues.jsonl"] = jsonl_bytes(extraction_issues)
    if experimental is not None:
        outputs["experimental_coverage.jsonl"] = jsonl_bytes(validate_experimental(experimental, catalog))
    # Pin every product catalog input, including provenance/schema and source rows.
    inputs = {p.as_posix(): sha256(file_bytes(p, "utf8-lf")) for p in sorted(catalogs.rglob("*.json"))}
    if experimental is not None:
        inputs[experimental.as_posix()] = sha256(file_bytes(experimental, "utf8-lf"))
    report = {"schema_version": "1.0", "source_snapshot_id": manifest.source_snapshot_id,
              "source_location": manifest.source_location, "corpus_build_id": read_json_bytes(built["manifest.json"])["build_id"],
              "classification_counts": dict(Counter(r["disposition"] for r in classifications)),
              "document_count": len(classifications), "catalog_course_count": len(catalog),
              "f2_extracted_rows": len(f2), "f3_extracted_sections": len(f3),
              "answer_documents": len(filtered), "answer_chunks": len(chunks),
              "generated_in_answer_corpus": 0, "active_release": False,
              "question_checks": dict(Counter(r["result"] for r in questions)),
              "inputs": inputs, "implementation_sha256": sha256(file_bytes(Path(__file__), "utf8-lf")),
              "outputs": {k: sha256(v) for k, v in sorted(outputs.items())}}
    outputs["report.json"] = json_bytes(report)
    return outputs


def read_json_bytes(data: bytes) -> dict:
    import json
    return json.loads(data)


def read_jsonl_bytes(data: bytes) -> list[dict]:
    import json
    return [json.loads(line) for line in data.splitlines() if line.strip()]
