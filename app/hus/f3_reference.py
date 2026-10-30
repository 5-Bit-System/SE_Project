"""Source-bound, explicitly generated F3 data for a separate experimental RAG corpus."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re

from app.hus.corpus import file_bytes, json_bytes, jsonl_bytes, sha256, split_chunks

SOURCE_COMMIT = "cfb2ec4c7f3f8e80428abc3db535dad0cc5db41d"
SOURCE_BLOB = "79dd58bc54998def1f0f5fe60016d068affc0433"
SOURCE_URL = f"https://github.com/5-Bit-System/SE_Project/blob/{SOURCE_COMMIT}/database/data/hus_source.json"
DATASET_KIND = "generated_f3_reference"
METHOD = "codex_authored_concept_blueprints_v1"
WARNING = "Nội dung tham khảo do AI sinh từ F2, không phải đề cương, chuẩn đầu ra hay quy định đánh giá chính thức của HUS."
PROGRAMS = {
    "7460101": ("toan_hoc_7460101_2022", "mathematics", "QD3565-2023", 90),
    "7460117": ("toan_tin_7460117_2022", "mathematics_informatics", "QD3567-2023", 68),
    "7480113QTD": ("khmtt_7480113qtd_2022", "computer_science", "QD3568-2023", 67),
    "7460108": ("khdl_7460108_2022", "data_science", "QD3569-2023", 65),
}
SECTIONS = ("content", "objectives", "suggested_assessment")


def load_inputs(inputs: Path) -> tuple[dict, dict[str, dict], dict]:
    raw = file_bytes(inputs / "hus_source.json", "utf8-lf")
    digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if digest != SOURCE_BLOB:
        raise ValueError("F2 source differs from the pinned main Git blob")
    bundle = json.loads(raw)
    profiles_text = file_bytes(inputs / "blueprints.psv", "utf8-lf")
    rows = list(csv.DictReader(io.StringIO(profiles_text.decode()), delimiter="|"))
    profiles = {}
    for position, row in enumerate(rows, 2):
        if set(row) != {"codes", "topics", "objectives", "assessment_tasks", "assessment_criteria"}:
            raise ValueError(f"Invalid blueprint columns: line {position}")
        payload = {}
        for field in ("topics", "objectives", "assessment_tasks", "assessment_criteria"):
            values = [v.strip() for v in row[field].split(";")]
            if len(values) < 2 or any(len(v) < 15 for v in values) or len(values) != len(set(values)):
                raise ValueError(f"Empty, repetitive or underspecified blueprint: line {position}/{field}")
            payload[field] = values
        if len(payload["topics"]) < 3:
            raise ValueError("Each course needs at least three proposed content topics")
        for code in row["codes"].split(","):
            if not re.fullmatch(r"[A-Z]{3}\d{4}[A-Z]?", code) or code in profiles:
                raise ValueError(f"Invalid or repeated blueprint code: {code}")
            profiles[code] = {**payload, "blueprint_line": position,
                              "blueprint_sha256": sha256(json_bytes(row))}
    tables = bundle["tables"]
    expected = {r["course_code"] for r in tables["curriculum_courses"]}
    if set(profiles) != expected:
        raise ValueError(f"Blueprint coverage differs from F2: missing={sorted(expected-set(profiles))}; "
                         f"extra={sorted(set(profiles)-expected)}")
    return bundle, profiles, {"source_git_blob": digest, "source_sha256_utf8_lf": sha256(raw),
                              "blueprints_sha256_utf8_lf": sha256(profiles_text)}


def candidate_syllabi(root: Path | None) -> tuple[dict[tuple[str, str], list[dict]], str | None]:
    """Keep pointers to previously extracted syllabi, without promoting them to official F3."""
    result = defaultdict(list)
    if root is None:
        return result, None
    path = root / "f3_source_fields.jsonl"
    raw = file_bytes(path, "utf8-lf")
    for line in raw.splitlines():
        row = json.loads(line)
        result[row["major_proposed"], row["code"]].append({
            "document_id": row["document_id"], "url": row["source_url"],
            "content_hash": row["content_hash"], "version_proposed": row["version_proposed"],
            "markdown_path": row["markdown_path"], "start": row["start"], "end": row["end"],
            "status": "unverified_source_candidate", "official_answer_eligible": False,
            "limitation": "Raw/edition/course identity/whole-document review still required; this is not the source of generated F3.",
        })
    return result, sha256(raw)


def records_from_inputs(bundle: dict, profiles: dict[str, dict], identity: dict,
                        candidates: dict) -> list[dict]:
    tables = bundle["tables"]
    courses = {c["course_code"]: c for c in tables["courses"]}
    curricula = {c["curriculum_id"]: c for c in tables["curricula"]}
    majors = {m["major_code"]: m for m in tables["majors"]}
    if len(curricula) != 4 or {c["major_code"] for c in curricula.values()} != set(PROGRAMS):
        raise ValueError("Exactly four source curricula are required")
    result = []
    seen = set()
    for membership in tables["curriculum_courses"]:
        cid, code = membership["curriculum_id"], membership["course_code"]
        curriculum = curricula[cid]
        program, major, version, _ = PROGRAMS[curriculum["major_code"]]
        if curriculum["cohort_year"] != 2022 or curriculum["curriculum_version"] != version:
            raise ValueError("Unexpected cohort or curriculum version")
        if (program, code) in seen:
            raise ValueError("Repeated course within a program")
        seen.add((program, code))
        course, profile = courses[code], profiles[code]
        occurrences = [(i, e) for i, e in enumerate(tables["official_curriculum_entries"])
                       if e["curriculum_id"] == cid and e["course_code"] == code]
        if not occurrences or any(e["credits_in_source"] != course["credits"] for _, e in occurrences):
            raise ValueError("Course lacks consistent source credit occurrences")
        if any(not e["pdf_document"] or not e["pdf_page"] for _, e in occurrences):
            raise ValueError("Source occurrence lacks PDF locator")
        facts = {
            "course_name": course["course_name"], "credits_transcribed": course["credits"],
            "source_status": "draft_unverified", "source_group": membership["course_group"],
            "prerequisite_occurrences": [{
                "entry_id": e["entry_id"], "raw": e["prerequisite_source_text"],
                "parse_status_from_source": e["prerequisite_parse_status"],
            } for _, e in occurrences],
            "prerequisite_options_from_source": [p for p in tables["course_prerequisites"]
                                                  if p["curriculum_id"] == cid and p["course_code"] == code],
            "prerequisite_answer_status": "not_revalidated_here",
        }
        result.append({
            "record_id": f"{program}:{code}", "program_id": program, "major": major,
            "major_name": majors[curriculum["major_code"]]["major_name"],
            "course_code": code, "course_name": course["course_name"],
            "curriculum_version": version, "cohort_year": 2022,
            "cohort_applicability_status": "as_declared_in_F2_not_independently_revalidated",
            "f2": facts,
            "content_origin": "generated", "dataset_kind": DATASET_KIND,
            "generation_method": METHOD, "authored_by": "Codex", "reviewer": None,
            "review_status": "needs_review", "academic_verified": False,
            "usage_scope": "reference_only", "disclosure_required": True, "warning": WARNING,
            "generated_content": {
                "summary": f"Phương án nội dung tham khảo cho học phần {course['course_name']}: "
                           + "; ".join(profile["topics"]) + ". Các chủ đề này do AI đề xuất, chưa đối chiếu đề cương chính thức.",
                "topics": profile["topics"],
            },
            "generated_objectives": profile["objectives"],
            "suggested_assessment": {
                "status": "suggested_not_official", "tasks": profile["assessment_tasks"],
                "criteria": profile["assessment_criteria"], "weights_percent": None,
                "official_exam_format": None,
            },
            "official_content": None, "official_objectives": None, "official_assessment": None,
            "unknown_official_fields": ["Nội dung áp dụng thực tế", "Chuẩn đầu ra chính thức",
                                         "Hình thức và tỷ lệ điểm", "Giáo trình", "Lịch học"],
            "provenance": {
                "f2_source_url": SOURCE_URL, "f2_source_commit": SOURCE_COMMIT,
                "f2_source_git_blob": SOURCE_BLOB,
                "f2_source_sha256_utf8_lf": identity["source_sha256_utf8_lf"],
                "f2_source_role": "identity_credits_prerequisite_inputs_only_not_evidence_of_generated_syllabus",
                "f2_pointers": [f"/tables/official_curriculum_entries/{i}" for i, _ in occurrences],
                "pdf_locators": [{"document": e["pdf_document"], "page": e["pdf_page"],
                                  "row": e["source_row_number"], "group": e["group_key"]} for _, e in occurrences],
                "blueprint_path": "inputs/blueprints.psv", "blueprint_line": profile["blueprint_line"],
                "blueprint_sha256": profile["blueprint_sha256"],
            },
            "official_source_candidates": candidates.get((major, code), []),
        })
    counts = Counter(r["program_id"] for r in result)
    if counts != Counter({v[0]: v[3] for v in PROGRAMS.values()}):
        raise ValueError("Generated record counts differ from the four F2 catalogs")
    return sorted(result, key=lambda r: r["record_id"])


def validate_record(record: dict) -> None:
    if (record["dataset_kind"] != DATASET_KIND or record["content_origin"] != "generated"
        or record["academic_verified"] is not False or record["reviewer"] is not None
        or record["review_status"] != "needs_review" or record["usage_scope"] != "reference_only"
        or record["disclosure_required"] is not True or record["warning"] != WARNING):
        raise ValueError("Generated F3 cannot acquire official review/usage status")
    if any(record[k] is not None for k in ("official_content", "official_objectives", "official_assessment")):
        raise ValueError("Generated F3 cannot assert official syllabus fields")
    assessment = record["suggested_assessment"]
    if (assessment["status"] != "suggested_not_official" or assessment["weights_percent"] is not None
        or assessment["official_exam_format"] is not None):
        raise ValueError("Generated assessment cannot assert official weights or exam format")
    if len(record["generated_content"]["topics"]) < 3 or len(record["generated_objectives"]) < 2:
        raise ValueError("Incomplete generated content/objectives")
    if len(assessment["tasks"]) < 2 or len(assessment["criteria"]) < 2:
        raise ValueError("Incomplete assessment suggestions")


def section_texts(record: dict) -> dict[str, str]:
    return {
        "content": record["generated_content"]["summary"],
        "objectives": "Mục tiêu tham khảo do AI đề xuất:\n" + "\n".join("- " + v for v in record["generated_objectives"]),
        "suggested_assessment": "Gợi ý đánh giá để thử nghiệm, chưa phải hình thức thi chính thức:\n"
            + "\n".join("- " + v for v in record["suggested_assessment"]["tasks"])
            + "\nTiêu chí gợi ý:\n" + "\n".join("- " + v for v in record["suggested_assessment"]["criteria"])
            + "\nTỷ lệ điểm và hình thức thi chính thức: chưa có thông tin đã xác minh.",
    }


def export_records(records: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    documents, chunks, mapping = [], [], []
    for record in records:
        validate_record(record)
        texts = section_texts(record)
        context = (f"Học phần: {record['course_code']} — {record['course_name']}.\n"
                   f"Ngành: {record['major_name']}; phiên bản F2: {record['curriculum_version']}; khóa: 2022.\n"
                   f"Số tín chỉ theo bản chép F2 chưa thẩm định: {record['f2']['credits_transcribed']}.\n")
        metadata = {key: record[key] for key in (
            "record_id", "program_id", "major", "major_name", "course_code", "course_name",
            "curriculum_version", "cohort_year", "dataset_kind", "content_origin", "usage_scope",
            "academic_verified", "review_status", "disclosure_required",
        )}
        full_text = context + "\n" + "\n\n".join(texts.values())
        documents.append({**metadata, "text": full_text, "provenance": record["provenance"],
                          "document_sha256": sha256(full_text.encode())})
        for field, text in texts.items():
            # Every standalone part retains generation metadata and major/version identity.
            for pos, (start, end) in enumerate(split_chunks(text, 4000)):
                chunk_text = context + text[start:end]
                chunk_id = sha256((record["record_id"] + ":" + field + ":" + str(pos) + "\n" + chunk_text).encode())[:24]
                locator = {"record_id": record["record_id"], "field": field, "start_char": start,
                           "end_char": end, "offset_scope": "rendered_field_text_excluding_repeated_context"}
                chunks.append({**metadata, "chunk_id": chunk_id, "field": field, "text": chunk_text,
                               "citation_label": f"{record['course_code']} — {record['major_name']}",
                               "provenance": record["provenance"], "locator": locator})
                mapping.append({"chunk_id": chunk_id, "locator": locator, "content_origin": "generated",
                                "is_official_F3_citation": False,
                                "blueprint_line": record["provenance"]["blueprint_line"]})
    return documents, chunks, mapping


def build_reference(inputs: Path, candidate_audit: Path | None = None) -> dict[str, bytes]:
    bundle, profiles, identity = load_inputs(inputs)
    candidates, candidate_sha = candidate_syllabi(candidate_audit)
    records = records_from_inputs(bundle, profiles, identity, candidates)
    documents, chunks, mapping = export_records(records)
    coverage = [{"program_id": r["program_id"], "course_code": r["course_code"],
                 "curriculum_version": r["curriculum_version"], "cohort_year": r["cohort_year"],
                 "content": "generated_reference", "objectives": "generated_reference",
                 "assessment": "suggested_not_official", "official_F3_verified": False,
                 "unverified_source_candidates": len(r["official_source_candidates"])} for r in records]
    questions = []
    examples = {"mathematics": "MAT3300", "mathematics_informatics": "MAT3539",
                "computer_science": "MAT3507", "data_science": "MAT3533"}
    for major, code in examples.items():
        r = next(r for r in records if r["major"] == major and r["course_code"] == code)
        for field, prompt in (("content", "Học phần có thể học những chủ đề gì?"),
                              ("objectives", "Mục tiêu học tập tham khảo là gì?"),
                              ("suggested_assessment", "Có thể đánh giá bằng hoạt động nào?"),
                              ("official_assessment", "Thi cuối kỳ chính thức chiếm bao nhiêu phần trăm?")):
            evidence = [c["chunk_id"] for c in chunks if c["record_id"] == r["record_id"]
                        and c["field"] == ("suggested_assessment" if field == "official_assessment" else field)]
            questions.append({"question_id": r["program_id"] + ":" + field,
                              "question": f"{r['course_name']} ({code}), ngành {r['major_name']}: {prompt}",
                              "program_id": r["program_id"], "course_code": code,
                              "evidence_chunk_ids": evidence, "source_label": "generated_reference",
                              "expected_answer_mode": "disclose_official_unknown" if field == "official_assessment" else "disclosed_generated_reference",
                              "official_answer_available": False, "disclosure_required": True,
                              "result": "pass" if evidence and r["official_assessment"] is None else "fail",
                              "check_method": "offline_data_contract_not_LLM_or_retrieval_evaluation"})
    output = {"records.jsonl": jsonl_bytes(records), "rag_documents.jsonl": jsonl_bytes(documents),
              "rag_chunks.jsonl": jsonl_bytes(chunks), "source_map.jsonl": jsonl_bytes(mapping),
              "coverage.jsonl": jsonl_bytes(coverage), "acceptance_questions.jsonl": jsonl_bytes(questions)}
    report = {
        "schema_version": "1.0", "dataset_kind": DATASET_KIND, "method": METHOD,
        "source_commit": SOURCE_COMMIT, "source_url": SOURCE_URL, **identity,
        "candidate_syllabus_inventory_sha256": candidate_sha,
        "program_counts": dict(sorted(Counter(r["program_id"] for r in records).items())),
        "records": len(records), "distinct_course_codes": len(profiles),
        "blueprints": len({p["blueprint_line"] for p in profiles.values()}),
        "rag_documents": len(documents), "rag_chunks": len(chunks),
        "generated_field_coverage": {f: len(records) for f in SECTIONS},
        "official_F3_verified": 0, "official_corpus_modified": False, "active_release": False,
        "question_contracts": dict(Counter(q["result"] for q in questions)),
        "implementation_sha256": sha256(file_bytes(Path(__file__), "utf8-lf")),
        "outputs": {k: sha256(v) for k, v in sorted(output.items())},
    }
    output["manifest.json"] = json_bytes(report)
    return output
