"""New technical review worksheet; preserves every previous source/review byte."""

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
OLD = ROOT / "data/hus/review/p13_followup_v1"
AUDIT = ROOT / "data/hus/review/p13_source_audit_v1"
RELEASE = ROOT / "data/hus/rag/releases/hus-data-20261031-v3"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def write_json(name, value):
    with (OUT / name).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def write_rows(name, values):
    with (OUT / name).open("x", encoding="utf-8", newline="\n") as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")


def decision():
    return {"human_decision": "pending", "reviewer": None, "reviewed_at": None,
            "academic_verified": False, "current_validity_verified": False,
            "default_release_promotion_authorized": False}


inputs = [p for directory in [OLD, AUDIT, ROOT / "data/hus/review/p13_ocr_v1",
                              ROOT / "data/hus/review/p13_syllabus_supplement_v1",
                              ROOT / "data/hus/review/p13_source_retry_v1", RELEASE]
          for p in directory.rglob("*") if p.is_file()]
inputs += [ROOT / "data/hus/rag/CURRENT.json", ROOT / "data/hus/citation_assets/registry.json"]
# The current registry filename is selected without changing it.
inputs = [p for p in inputs if p.is_file()]
pins = {p.relative_to(ROOT).as_posix(): sha(p) for p in inputs}

missing = rows(OLD / "missing_source_priorities.jsonl")
scope_by_missing_category = {
    "postgraduate_archive_outside_current_undergraduate_scope": "proposed_defer_outside_undergraduate_release",
    "seminar_outside_F123": "proposed_defer_outside_F123",
    "admissions_separate_year_and_scope": "separate_admissions_scope_not_current_release",
    "curriculum_outcome_matrix_or_map": "candidate_pending_original_and_edition_review",
    "undergraduate_scan_possible_alias": "candidate_pending_original_binding_not_active",
}
decisions = []
for source in missing:
    category = source["proposed_category"]
    if category.startswith("postgraduate") or category.startswith("seminar"):
        needed = "Xác nhận ngoài phạm vi release cử nhân F1/F2/F3 hiện tại; giữ archive, không cần thu hồi trước release nếu phạm vi không đổi."
    elif category.startswith("admissions"):
        needed = "Xác nhận tách tuyển sinh/năm hiệu lực khỏi release CTĐT2022; chỉ ưu tiên thu hồi nếu mở phạm vi tuyển sinh riêng."
    elif category.startswith("curriculum"):
        needed = "Cần bản gốc ma trận/sơ đồ, hash, quyết định/edition/cohort và chỉ rõ trường nào bổ sung; không suy từ Markdown."
    else:
        needed = "Cần chứng minh URL/document_id này gắn với binary nào; PDF liên quan và OCR không chứng minh byte gốc hay nguồn alias."
    decisions.append({**source, **decision(), "scope_recommendation": scope_by_missing_category[category],
                      "required_human_evidence_or_decision": needed,
                      "new_original_recovered": False, "not_a_runtime_blocker_for_existing_F1": True})
write_rows("missing_raw_decisions.jsonl", decisions)

missing_index = {r["document_id"]: r for r in decisions}
sources = {r["source_id"]: r for r in rows(RELEASE / "sources.jsonl")}
inventory = []
for source in rows(AUDIT / "source_inventory_review.jsonl"):
    sid = source["document_id"]
    if source["used_in_default_F1"]:
        scope = "already_active_F1_descriptive_only_keep_existing_review"
        needed = "Giữ review gốc và cảnh báo hiệu lực; sự có mặt hiện tại không cấp xác minh học vụ mới."
    elif sid in missing_index:
        scope = missing_index[sid]["scope_recommendation"]
        needed = missing_index[sid]["required_human_evidence_or_decision"]
    elif sid in {"098df9e79c1391af", "bc0a1f59b7ab202c"}:
        scope = "syllabus_candidate_pending_identity_edition_and_human_review"
        needed = "Cần xác nhận edition/cohort/hiệu lực và identity; không index official F3 hoặc suy tỷ lệ thi đang áp dụng."
    else:
        scope = "available_original_not_selected_pending_scope_review"
        needed = "Chỉ xem xét release mới nếu nguồn bổ sung field thực sự thiếu và đúng scope; không index trùng hoặc tự cấp duyệt."
    inventory.append({**source, **decision(), "scope_recommendation": scope,
                      "existing_source_review": sources.get(sid, {}).get("review_status"),
                      "required_human_evidence_or_decision": needed})
write_rows("source_scope_inventory.jsonl", inventory)

# Transcribed by AI visual inspection of actual cached page images in this pass.
# Blank prerequisite/hours cells remain null/empty, never a verified absence.
shared = {
    "PEC1008": (2, [30, 0, 70], ["PHI1006"]),
    "PHI1002": (2, [28, 4, 68], ["PHI1006"]),
    "POL1001": (2, [28, 4, 68], []),
    "FLF1107": (5, [25, 50, 175], []),
    "FLF1207": (5, [25, 50, 175], []),
    "FLF1307": (5, [25, 50, 175], []),
    "FLF1507": (5, [25, 50, 175], []),
    "CME1000": (8, None, []), "PES1000": (4, None, []),
    "MAT2300": (4, [45, 30, 125], []),
    "MAT1201": (3, [15, 60, 75], []),
    "MAT3500": (4, [45, 30, 125], []),
    "MAT1202": (3, [22, 46, 82], ["MAT2505"]),
    "MAT1204": (3, [15, 60, 75], ["MAT3507", "MAT3514"]),
    "MAT1205E": (2, [10, 40, 50], ["FLF1107"]),
    "MAT3550E": (3, [30, 30, 90], ["MAT2505"]),
    "MAT3552E": (3, [30, 30, 90], ["MAT3514"]),
    "MAT1206E": (3, [30, 30, 90], ["MAT3507", "MAT1202"]),
    "MAT1207": (3, [22, 46, 82], ["MAT3374"]),
    "MAT3541E": (3, [30, 30, 90], ["MAT1202"]),
    "MAT1208": (2, [0, 30, 70], ["MAT1202", "MAT3505"]),
    "MAT3554E": (3, [40, 10, 100], ["MAT2505", "MAT3500"]),
    "MAT3562E": (3, [30, 30, 90], ["MAT3533", "MAT2400"]),
    "MAT3561E": (3, [35, 20, 95], ["MAT3533"]),
    "MAT4080": (7, [70, 60, 215], []),
    "MAT1203": (4, [10, 100, 90], ["MAT3374", "MAT3552E", "MAT1207"]),
    "MAT1209": (2, [0, 30, 70], ["MAT3533"]),
}
ocr_index = {(r["source_sha256"], str(r["pdf_page"])): r
             for r in rows(ROOT / "data/hus/review/p13_ocr_v1/ocr_pages.jsonl")}
visual = []
for original in rows(OLD / "code_token_diagnostic.jsonl"):
    if original["code_token_seen_on_page"]:
        continue
    code = original["course_code"]
    credits, hours, prereq = shared[code]
    page = ocr_index[(original["source_sha256"], original["pdf_page"])]
    image = ROOT / page["image_path"]
    assert sha(image) == page["image_sha256"]
    pins[page["image_path"]] = sha(image)
    visual.append({**original, **decision(), "method_this_pass": "AI_assisted_visual_table_row_inspection",
                   "code_visually_seen_in_code_column": True, "observed_code": code,
                   "observed_credits_as_printed": credits,
                   "observed_hours_columns_order": ["theory", "practice", "self_study"],
                   "observed_hours_as_printed": hours,
                   "observed_prerequisite_cell_lines": prereq,
                   "image_path": page["image_path"], "image_sha256": page["image_sha256"],
                   "row_alignment_observed_by_AI": True, "row_alignment_verified_by_human": False,
                   "parsed_prerequisite_edges_created": False,
                   "blank_cell_meaning": "empty in this image; not independently verified prerequisite absence",
                   "limitation": "AI technical observation of 45 selected rows only; not full297 occurrence acceptance or current academic validity."})
write_rows("table_visual_observations.jsonl", visual)

identity = []
for original in rows(OLD / "identity_proposals.jsonl"):
    image = ROOT / original["evidence"]["image_path"]
    assert sha(image) == original["evidence"]["image_sha256"]
    pins[original["evidence"]["image_path"]] = sha(image)
    if original.get("canonical_pdf_visual_evidence"):
        ref = original["canonical_pdf_visual_evidence"]
        assert sha(ROOT / ref["image_path"]) == ref["image_sha256"]
        pins[ref["image_path"]] = ref["image_sha256"]
    row = {**original, **decision(), "rechecked_this_pass": True,
           "review_kind": "AI technical comparison; no signature", "proposal_applied": False}
    if original["candidate_id"].endswith(":27:MAT1202"):
        row["additional_cross_reference"] = {
            "status": "unapproved_errata_lead_not_identity_assignment", "possible_intended_code": "MAT1208",
            "canonical_program_pdf_sha256": "bc070d7ae3713f77c36817d960b73dec53dcdeacda5e25e557c37a732abe09ab",
            "physical_page": 12, "printed_table_row": 44,
            "title": "Xây dựng hệ thống nhúng", "credits": 2,
            "hours": [0, 30, 70], "prerequisite_cell_lines": ["MAT1202", "MAT3505"],
            "required_decision": "Reviewer must confirm erratum/identity and applicability; neither code nor syllabus content is remapped automatically."}
    identity.append(row)
write_rows("identity_decisions.jsonl", identity)

blockers = []
for old in rows(OLD / "historical_ocr_followup.jsonl"):
    missing_binding = not old["binary_available_in_this_audit"]
    blockers.append({**old, **decision(), "blocker_closed": False,
                     "new_related_table_visual_evidence": "table_visual_observations.jsonl",
                     "blocking_evidence_still_missing": (
                         "exact historical URL/document_id to original binary binding and human source/edition review"
                         if missing_binding else "human image/table review plus source applicability/current-validity confirmation"),
                     "OCR_alone_closes_blocker": False})
write_rows("blocker_decisions.jsonl", blockers)

editions = [
    {"document_id": "098df9e79c1391af", "source_sha256": "56d751cc897fe12626f05ebaa28842440e3b6402dede058bd280d6f3c1def2d0",
     "source_cover_declares": "QD2385-2024 dated2024-07-31; references curriculum QD3568-2023 dated2023-10-18,standard",
     "canonical_target": "computer_science/cohort2022/QD3568-2023", "scope_status": "candidate_not_active_official_F3",
     "required_evidence": "Confirm signed syllabus decision applies to target cohort/program and check later amendments; matching decision number alone is insufficient."},
    {"document_id": "bc0a1f59b7ab202c", "source_sha256": "6e049389bc467f41ea6d48cffd66182c50bf52e77efdbb57868dbe6f14f33b7b",
     "source_cover_declares": "Toan Tin undergraduate,7460117,Hanoi2021",
     "canonical_target": "mathematics_informatics/cohort2022/QD3567-2023", "scope_status": "candidate_blocked_edition2021_vs2023",
     "required_evidence": "Need cohort/edition applicability decision or matching newer source. Do not overwrite MAT3561 prerequisite MAT3533 with2021 MAT3508/MAT3509."},
]
write_rows("edition_decisions.jsonl", [{**r, **decision()} for r in editions])

web = {
    "checked_on": "2026-11-03", "method": "bounded_official_domain_web_search", "exhaustive": False,
    "queries": ['site:hus.vnu.edu.vn "3568" "2023" "Máy tính"',
                'site:hus.vnu.edu.vn "3567" "2023" "Toán"',
                'site:mim.hus.vnu.edu.vn "2385" "2024"',
                'site:hus.vnu.edu.vn "chương trình đào tạo" "Toán tin" "2026"'],
    "selected_leads": [
        {"url": "https://hus.vnu.edu.vn/thong-bao/dao-tao-tuyen-sinh/thong-bao-xet-tuyen-sinh-vien-vao-cac-chuong-trinh-dao-tao-dac-biet-nam-2026-ap-dung-cho-doi-tuong-sinh-vien-da-trung-tuyen-vao-truong-145802",
         "page_date": "2026-08-14", "meaning": "2026 special-program admissions includes integrated talented bachelor/master STEM Data Science; separate program/year, not evidence for cohort2022/QD3569 or QD3567/3568 applicability"},
        {"url": "https://hus.vnu.edu.vn/mot-vong-quanh-hus/dien-dan-thay-va-tro/truong-dai-hoc-khoa-hoc-tu-nhien-gap-mat-tan-145879",
         "page_date": "2026-09-19", "event_date": "2026-09-18", "meaning": "QH2026 cohort event; cannot certify historical2021/2023 syllabus applicability or absence of amendments"}],
    "new_originals_recovered": 0, "current_validity_confirmed": 0,
    "original_URLs_retried_this_pass": 0,
    "prior_timeout_records": "data/hus/review/p13_source_retry_v1/attempts.jsonl",
    "limits": "No complete authoritative amendment chain was established. Search absence or old fetch timeout is not proof of404, withdrawal or invalidity."}
write_json("source_search_notes.json", web)

assert len(visual) == 45 and len({(r["source_sha256"], r["pdf_page"]) for r in visual}) == 13
assert len(identity) == 5 and sum(bool(r["proposed_canonical_record_id"]) for r in identity) == 4
assert len(decisions) == 37 and len(blockers) == 6 and len(inventory) == 106
assert sum(r["used_in_default_F1"] for r in inventory) == 15
assert all(not r["used_in_default_F1"] for r in decisions)
assert all(sha(ROOT / path) == value for path, value in pins.items())
report = {
    "created_on": "2026-11-03", "status": "technical_review_followup_pending_real_human_decisions",
    "active_F1_sources_retained": 15, "historical_source_inventory": 106,
    "source_scope_recommendations": dict(Counter(r["scope_recommendation"] for r in inventory)),
    "missing_raw": 37, "missing_scope_categories": dict(Counter(r["proposed_category"] for r in decisions)),
    "historical_blockers": 6, "blockers_closed": 0,
    "table_images_inspected_this_pass": 13, "OCR_missed_occurrences_AI_visually_observed": 45,
    "total_images_inspected_this_pass_including_rechecks": 19,
    "full_297_occurrence_row_acceptance": False, "identity_cases_rechecked": 5,
    "existing_identity_link_proposals_not_applied": 4, "new_errata_cross_reference_not_applied": 1,
    "new_originals_recovered": 0, "new_human_approvals": 0, "current_validity_confirmed": 0,
    "human_reviewer_volunteered": "user indicated intention to review; identity/signature not recorded here",
    "reviewer": None, "reviewed_at": None, "official_F3_enabled": False,
    "runtime_changed": False, "release_changed": False, "CURRENT_changed": False,
    "input_hashes_preserved": True, "inputs_sha256": pins,
}
write_json("report.json", report)
write_json("manifest.json", {"schema_version": "1.0", "files_sha256": {
    p.name: sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "manifest.json"},
    "inputs_sha256": pins, "status": "review_only_no_promotion"})
print(json.dumps({"table_rows_observed": 45, "table_pages": 13, "inventory": 106,
                  "missing_raw": 37, "blockers_closed": 0, "official_F3_enabled": False}))
