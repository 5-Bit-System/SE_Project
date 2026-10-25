"""Public, source-backed curriculum lookup. Never derives student outcomes."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from app.catalog_contracts import digest
from database.hus_db.catalog_builder import build_catalogs
from database.hus_db.prerequisites import parse_prerequisites

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "database/data/hus_source.json"
TALENT = ROOT / "data/reference_curricula/mathematics_talented_2022.json"
PDF_ROOT = ROOT / "docs/pdf"
MIN_COHORT = 67
MIN_YEAR = 2022
EXCLUDED = {"CME1000", "PES1000", "HUS1012"}


class ReferenceError(ValueError):
    pass


def current_cohort() -> int:
    year = datetime.now(timezone(timedelta(hours=7))).year
    return MIN_COHORT + max(0, year - MIN_YEAR)


def validate_cohort(cohort: int) -> None:
    if not MIN_COHORT <= cohort <= current_cohort():
        raise ReferenceError("cohort_outside_source_scope")


def _talented(doc: dict) -> dict:
    courses = {}
    for ordinal, code, name, credits, group, raw, page in doc["rows"]:
        parsed = parse_prerequisites(raw)
        if code not in courses:
            courses[code] = {
                "code": code, "name": name, "name_en": None, "credits": credits,
                "requirement_type": "graduation" if group == "graduation" else (
                    "required_excluded" if code in EXCLUDED else "elective" if group in {
                        "language_b1", "language_b2", "field", "group_elective",
                        "theory", "applied", "mechanics"} else "required"),
                "counted_in_total": code not in EXCLUDED,
                "prerequisites": parsed, "prerequisites_raw": raw or None,
                "prerequisite_status": "draft_unverified", "prerequisite_variants": [],
                "group_ids": [], "source_occurrences": [], "hours": None,
            }
        course = courses[code]
        if (course["name"], course["credits"], course["prerequisites"]) != (name, credits, parsed):
            raise ReferenceError("talented_duplicate_source_conflict")
        if group not in course["group_ids"]:
            course["group_ids"].append(group)
        course["source_occurrences"].append({"pdf_page": page, "source_row_number": ordinal,
                                              "group_key": group})
    for course in courses.values():
        course["external_prerequisite_codes"] = sorted({
            code for clause in course["prerequisites"] for code in clause if code not in courses
        })
    limits = {"language_b1", "language_b2", "field", "group_elective",
              "theory", "applied", "mechanics"}
    return {
        "program_id": doc["program_id"], "name": doc["name"], "major": doc["major"],
        "total_credits": doc["total_credits"], "decision": doc["decision"],
        "source_file": doc["source_file"], "source_sha256": doc["source_sha256"],
        "groups": doc["groups"], "courses": list(courses.values()),
        "planning_groups": [{**group, "exclusive": group["id"].startswith("language_")}
                            for group in doc["groups"] if group["id"] in limits],
        "tracks": [], "graduation_paths": [], "issues": doc["issues"],
        "source_occurrence_count": len(doc["rows"]),
    }


@lru_cache(maxsize=1)
def _references() -> dict[str, dict]:
    bundle = json.loads(SOURCE.read_text(encoding="utf-8"))
    manifest = {item["source_ref"]: item for item in bundle["metadata_source_archive"]["documents"]}
    result = {}
    for catalog in build_catalogs(bundle):
        program = catalog.program
        source_groups = program.source_group_rules
        rows = []
        for course in catalog.courses:
            value = course.model_dump(mode="json", include={
                "code", "name", "name_en", "credits", "requirement_type", "counted_in_total",
                "hours", "prerequisites", "prerequisites_raw", "prerequisite_status",
                "prerequisite_variants", "external_prerequisite_codes", "source_occurrences",
            })
            value["group_ids"] = list(dict.fromkeys(
                occurrence["group_key"] for occurrence in value["source_occurrences"]))
            rows.append(value)
        issues = []
        if any(course.prerequisite_status in {"unknown", "conflict"} for course in catalog.courses):
            issues.append("Có tiên quyết thiếu định nghĩa hoặc mâu thuẫn; xem cảnh báo ở từng môn và PDF.")
        if program.program_id.startswith("khdl_"):
            issues.append("Nhóm V.2 ghi 28/63; tổng số tín chỉ chào của các nhóm con là 57. Giữ nguyên số liệu PDF.")
        result[program.program_id] = {
            "program_id": program.program_id, "name": program.name + " — chương trình chuẩn",
            "major": program.name, "total_credits": program.total_credits,
            "decision": program.source_curriculum["curriculum_version"],
            "source_file": program.source_file,
            "source_sha256": manifest[program.source_file]["sha256"],
            "groups": [{"id": group["group_key"], "name": group["group_title"],
                        "required_credits": group["min_credits_if_selected"],
                        "offered_credits": group["offered_credits"], "note": group["group_note"]}
                       for group in source_groups],
            "courses": rows, "issues": issues,
            "planning_groups": [{"id": group.id, "name": group.name,
                                 "required_credits": group.required_credits,
                                 "course_codes": group.course_codes,
                                 "exclusive": group.id == "language"}
                                for group in program.choice_groups],
            "tracks": [track.model_dump() for track in program.track_selection.tracks],
            "graduation_paths": [path.model_dump() for path in program.graduation_selection.paths],
            "source_occurrence_count": sum(len(c["source_occurrences"]) for c in rows),
        }
    talent = _talented(json.loads(TALENT.read_text(encoding="utf-8")))
    result[talent["program_id"]] = talent
    for value in result.values():
        value["catalog_status"] = "draft_unverified"
        value["reference_revision"] = digest(value)
        value["source_url"] = f"/curricula/reference/{value['program_id']}/source"
        value["course_count"] = len(value["courses"])
        value["applicability"] = {
            "from_cohort": MIN_COHORT, "from_admission_year": MIN_YEAR,
            "source_version": 2023, "later_amendments_reviewed": False,
        }
    return result


def list_references() -> dict:
    fields = {"program_id", "name", "major", "total_credits", "decision", "source_file",
              "source_sha256", "source_url", "course_count", "source_occurrence_count",
              "applicability", "catalog_status", "reference_revision"}
    programs = [{key: copy.deepcopy(value) for key, value in ref.items() if key in fields}
                for ref in _references().values()]
    programs.sort(key=lambda value: value["program_id"])
    return {"programs": programs,
            "cohorts": [{"number": number, "admission_year": MIN_YEAR + number - MIN_COHORT}
                        for number in range(MIN_COHORT, current_cohort() + 1)],
            "default_max_credits": 20, "max_planning_credits": 30}


def reference(program_id: str, cohort: int = MIN_COHORT) -> dict:
    validate_cohort(cohort)
    value = _references().get(program_id)
    if value is None:
        raise ReferenceError("reference_program_not_found")
    return {**copy.deepcopy(value), "cohort": cohort,
            "admission_year": MIN_YEAR + cohort - MIN_COHORT,
            "mode": "reference", "academic_eligibility": "not_evaluated"}


def source_pdf(program_id: str) -> Path:
    value = reference(program_id)
    # Allowlisted documents only. Never construct a path from a request filename.
    matches = [path for path in PDF_ROOT.glob("*.pdf")
               if hashlib.sha256(path.read_bytes()).hexdigest() == value["source_sha256"]]
    if len(matches) != 1:
        raise ReferenceError("reference_source_unavailable")
    return matches[0]


def plan_reference(program_id: str, *, cohort: int = MIN_COHORT, max_credits: int = 20,
                   course_codes: list[str] | None = None, suggest: bool = False) -> dict:
    """A hypothetical bundle, never a completed set or an eligibility decision."""
    if not 1 <= max_credits <= 30:
        raise ReferenceError("invalid_planning_budget")
    ref = reference(program_id, cohort)
    courses = {course["code"]: course for course in ref["courses"]}
    codes = list(course_codes or [])
    if len(codes) != len(set(codes)):
        raise ReferenceError("duplicate_planned_course")
    if set(codes) - courses.keys():
        raise ReferenceError("planned_course_outside_program")
    if suggest and codes:
        raise ReferenceError("suggestion_cannot_include_selected_courses")
    groups = ref["planning_groups"]

    def members(group):
        return set(group.get("course_codes", [course["code"] for course in courses.values()
                   if group["id"] in course["group_ids"]]))

    if suggest:
        # Only source-declared, prerequisite-free foundation courses. No transcript assumed.
        candidates = sorted(courses.values(), key=lambda c: (c["requirement_type"] != "required",
                            min(row["source_row_number"] or 999 for row in c["source_occurrences"]),
                            c["code"]))
        for course in candidates:
            if (course["prerequisites"] or course["prerequisites_raw"]
                    or course["prerequisite_status"] in {"conflict", "unknown", "source_conflict"}
                    or course["requirement_type"] in {"graduation", "required_excluded"}):
                continue
            if sum(courses[code]["credits"] for code in codes) + course["credits"] > max_credits:
                continue
            memberships = [g for g in groups if course["code"] in members(g)]
            if any(sum(courses[code]["credits"] for code in codes if code in members(g))
                   >= g["required_credits"] for g in memberships):
                continue
            codes.append(course["code"])
    total = sum(courses[code]["credits"] for code in codes)
    if total > max_credits:
        raise ReferenceError("planning_budget_exceeded")
    warnings = []
    for code in codes:
        course = courses[code]
        if course["prerequisites"]:
            warnings.append({"code": "prerequisites_not_verified", "course_code": code,
                             "prerequisites": course["prerequisites"]})
        if course["prerequisite_status"] in {"conflict", "unknown", "source_conflict"}:
            warnings.append({"code": "source_prerequisite_unresolved", "course_code": code})
        if course["requirement_type"] == "graduation":
            warnings.append({"code": "graduation_requirements_not_verified", "course_code": code})
    summaries = []
    for group in groups:
        selected = [code for code in codes if code in members(group)]
        selected_credits = sum(courses[code]["credits"] for code in selected)
        if group["exclusive"] and len(selected) > 1:
            raise ReferenceError("multiple_languages_in_same_level")
        if selected_credits > group["required_credits"]:
            warnings.append({"code": "group_target_exceeded", "group_id": group["id"]})
        if selected:
            summaries.append({"id": group["id"], "name": group["name"],
                              "required_credits": group["required_credits"],
                              "planned_credits": selected_credits})
    return {"mode": "reference", "academic_eligibility": "not_evaluated",
            "program_id": program_id, "cohort": cohort,
            "reference_revision": ref["reference_revision"], "max_credits": max_credits,
            "selected_credits": total, "remaining_budget": max_credits - total,
            "course_codes": codes, "groups": summaries, "warnings": warnings,
            "offering_status": "unknown"}
