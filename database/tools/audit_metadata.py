"""Offline, reproducible completeness audit of the source-built HUS catalogs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from database.hus_db.catalog_builder import build_catalogs
from database.tools.publish_catalogs import SOURCE

FIELDS = (
    "name", "name_en", "hours", "instruction_language", "year", "suggested_term",
    "topics", "orientation", "difficulty", "workload", "description", "career_paths",
)
MISSING_REASONS = {
    "hours": "Blank hours in source table; do not replace with zero.",
    "instruction_language": "Teaching-language source required; bilingual title is not evidence.",
    "year": "Version-matched semester plan required.",
    "suggested_term": "Version-matched semester plan required.",
    "topics": "Syllabus and reviewed vocabulary mapping required.",
    "orientation": "Syllabus and reviewed mapping rubric required.",
    "difficulty": "Versioned rubric and course assessment evidence required; raw default 2 is not evidence.",
    "workload": "Versioned rubric and workload evidence required.",
    "description": "Version-matched syllabus required, including English content for bilingual summaries.",
    "career_paths": "Learning outcomes and reviewed career mapping required.",
}


def value_state(value: object) -> str:
    """Keep null, blank, empty list, zero and false semantically distinct."""
    if value is None:
        return "null"
    if isinstance(value, str) and not value.strip():
        return "blank_string"
    if isinstance(value, list) and not value:
        return "empty_list"
    if isinstance(value, dict) and all(v is None for v in value.values()):
        return "unknown_object"
    return "present"


def audit_bundle(bundle: dict) -> tuple[dict, list[dict]]:
    catalogs = build_catalogs(bundle)
    summary = {
        "scope": "Offline source-built catalogs; not a live PostgreSQL or full PDF acceptance audit.",
        "source_sha256": hashlib.sha256(
            json.dumps(bundle, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest(),
        "source_counts": {name: len(rows) for name, rows in bundle["tables"].items()},
        "source_manifest": bundle.get("metadata_source_manifest", []),
        "programs": {},
    }
    rows = []
    for catalog in catalogs:
        counts = {field: Counter() for field in FIELDS}
        for course in catalog.courses:
            values = course.model_dump()
            for field in FIELDS:
                status = value_state(values[field])
                counts[field][status] += 1
                evidence = values["field_evidence"].get(field, [])
                rows.append({
                    "program_id": catalog.program.program_id, "code": course.code,
                    "field": field, "value_state": status,
                    "value": json.dumps(values[field], ensure_ascii=False),
                    "evidence": json.dumps(evidence, ensure_ascii=False),
                    "missing_reason": MISSING_REASONS.get(field, "Source transcription required.")
                    if status in {"null", "blank_string", "unknown_object"} else "",
                })
        summary["programs"][catalog.program.program_id] = {
            "courses": len(catalog.courses),
            "source_occurrences": sum(len(c.source_occurrences) for c in catalog.courses),
            "catalog_status": catalog.program.catalog_status,
            "fields": {field: dict(states) for field, states in counts.items()},
            "prerequisite_statuses": dict(Counter(c.prerequisite_status for c in catalog.courses)),
        }
    return summary, rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary, rows = audit_bundle(json.loads(args.source.read_text(encoding="utf-8")))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (args.output / "field_audit.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(summary["programs"], ensure_ascii=False))


if __name__ == "__main__":
    main()
