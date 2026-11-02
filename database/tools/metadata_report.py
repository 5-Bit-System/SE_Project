"""Report source-bound metadata coverage without confusing zero with missing data.

python -m database.tools.metadata_report --output reports/hus-metadata-2026-10-21
An optional --baseline-source points to an earlier source export for comparison.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from database.hus_db.catalog_builder import PROGRAM_IDS, build_catalogs
from database.tools.publish_catalogs import SOURCE

FIELDS = ("name_en", "hours", "instruction_language", "year", "suggested_term", "topics",
          "orientation", "difficulty", "workload", "description", "career_paths")


def missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, dict)):
        return len(value) == 0 or (isinstance(value, dict)
                                  and all(v is None for v in value.values()))
    return False


def summarize(bundle: dict) -> dict:
    catalogs = build_catalogs(bundle)
    rows = [course for catalog in catalogs for course in catalog.courses]
    return {
        "catalogs": len(catalogs), "memberships": len(rows),
        "source_occurrences": len(bundle["tables"]["official_curriculum_entries"]),
        "non_missing": {field: sum(not missing(getattr(course, field)) for course in rows)
                        for field in FIELDS},
        "programs": {c.program.program_id: {
            "courses": len(c.courses), "required_credits": c.program.total_credits,
            "non_missing": {f: sum(not missing(getattr(r, f)) for r in c.courses) for f in FIELDS},
        } for c in catalogs},
    }


def row_audit(bundle: dict) -> list[dict]:
    catalogs = {c.program.program_id: {r.code: r for r in c.courses}
                for c in build_catalogs(bundle)}
    curricula = {r["curriculum_id"]: r for r in bundle["tables"]["curricula"]}
    groups = {(r["curriculum_id"], r["group_key"]): r
              for r in bundle["tables"]["official_curriculum_groups"]}
    result = []
    for row in bundle["tables"]["official_curriculum_entries"]:
        curriculum = curricula[row["curriculum_id"]]
        program = PROGRAM_IDS[(curriculum["major_code"], curriculum["cohort_year"],
                               curriculum["curriculum_version"])]
        course = catalogs[program][row["course_code"]]
        group = groups[row["curriculum_id"], row["group_key"]]
        result.append({
            "program_id": program, "course_code": course.code, "name_vi": course.name,
            "name_en": course.name_en, "credits": course.credits,
            "group_key": row["group_key"], "group_title": group["group_title"],
            "course_type": course.source_membership["course_type"],
            "counted_in_total": course.counted_in_total,
            "source_row_number": row["source_row_number"], "pdf_document": row["pdf_document"],
            "pdf_page": row["pdf_page"], "printed_page": row["pdf_page"] - 2,
            "prerequisites_raw": row["prerequisite_source_text"],
            "prerequisite_status": course.prerequisite_status,
            "prerequisites": course.prerequisites,
            "source_prerequisite_rules": course.source_prerequisite_rules,
            "hours": course.hours,
            "metadata_missing_reasons": {field: "Required source not provided; see field-audit report."
                                         for field in FIELDS if missing(getattr(course, field))},
            "core_source_consistency": "matched", "human_review": "pending",
        })
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--baseline-source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bundle = json.loads(args.source.read_text(encoding="utf-8"))
    summary = {"after": summarize(bundle)}
    if args.baseline_source:
        summary["before"] = summarize(json.loads(args.baseline_source.read_text(encoding="utf-8")))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "coverage.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = row_audit(bundle)
    with (args.output / "row-audit.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({key: json.dumps(value, ensure_ascii=False)
                         if isinstance(value, (list, dict)) else value for key, value in row.items()}
                        for row in rows)
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == "__main__":
    main()
