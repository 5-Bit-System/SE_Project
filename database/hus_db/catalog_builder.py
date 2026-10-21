"""Deterministic, source-preserving HUS export to AI-07 runtime catalogs.

The rules below are curated from the exported official group notes. They are
deliberately keyed by stable major/cohort/version, never by database row ids.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.catalog_validation import validate_catalog
from app.models import Catalog, Course, Program
from database.hus_db.prerequisites import expression_key, parse_prerequisites

PROGRAM_IDS = {
    ("7460101", 2022, "QD3565-2023"): "toan_hoc_7460101_2022",
    ("7460117", 2022, "QD3567-2023"): "toan_tin_7460117_2022",
    ("7480113QTD", 2022, "QD3568-2023"): "khmtt_7480113qtd_2022",
    ("7460108", 2022, "QD3569-2023"): "khdl_7460108_2022",
}
EXCLUDED = frozenset({"CME1000", "PES1000", "HUS1012"})
LANGUAGES = frozenset({f"FLF1{i}07" for i in range(1, 8)})
BLOCKS = {"I": "general", "II": "field", "III": "discipline", "IV": "group", "V": "major"}
VOCABULARY = {"vocabulary_version": "1.0", "topics": [], "career_paths": [], "enums": {}}


def _unique(rows: list[dict], key: str, table: str) -> dict[Any, dict]:
    result = {}
    for row in rows:
        value = row[key]
        if value in result:
            raise ValueError(f"Duplicate {table}.{key}: {value}")
        result[value] = row
    return result


def _evidence(entry: dict, field: str) -> list[dict]:
    return [{
        "source_ref": entry["pdf_document"],
        "locator": f"page={entry['pdf_page']}; row={entry['source_row_number']}; code={entry['course_code']}",
        "method": "transcription",
        "status": "draft_unverified",
        "note": f"HUS source export: {field}; field-level review scope is recorded in the source bundle.",
    }]


def _indexed(rows: list[dict], keys: tuple[str, ...], table: str) -> dict[tuple, dict]:
    result = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        if key in result:
            raise ValueError(f"Duplicate {table}: {key}")
        result[key] = row
    return result


def build_catalogs(bundle: dict) -> list[Catalog]:
    """Validate the complete export and return four draft catalogs, with no writes."""
    if bundle.get("schema_version") != 1 or not isinstance(bundle.get("tables"), dict):
        raise ValueError("Unsupported HUS source bundle")
    tables = bundle["tables"]
    required_tables = (
        "faculties", "majors", "curricula", "courses", "curriculum_courses",
        "course_prerequisites", "official_curriculum_groups", "official_curriculum_entries",
    )
    if any(not isinstance(tables.get(name), list) for name in required_tables):
        raise ValueError("Incomplete HUS source tables")
    faculties = _unique(tables["faculties"], "faculty_code", "faculties")
    majors = _unique(tables["majors"], "major_code", "majors")
    curricula = _unique(tables["curricula"], "curriculum_id", "curricula")
    courses = _unique(tables["courses"], "course_code", "courses")
    memberships = _indexed(tables["curriculum_courses"], ("curriculum_id", "course_code"), "curriculum_courses")
    groups = _indexed(tables["official_curriculum_groups"], ("curriculum_id", "group_key"), "official_curriculum_groups")
    entries = _unique(tables["official_curriculum_entries"], "entry_id", "official_curriculum_entries")
    prerequisites = _indexed(tables["course_prerequisites"],
                             ("curriculum_id", "course_code", "group_no", "prerequisite_course_code"),
                             "course_prerequisites")
    if len(curricula) != 4 or {(
        c["major_code"], c["cohort_year"], c["curriculum_version"]
    ) for c in curricula.values()} != set(PROGRAM_IDS):
        raise ValueError("Unexpected HUS curriculum identity")
    for major in majors.values():
        if major["faculty_code"] not in faculties:
            raise ValueError("Major references missing faculty")
    for curriculum in curricula.values():
        if curriculum["major_code"] not in majors:
            raise ValueError("Curriculum references missing major")
    for (cid, code), membership in memberships.items():
        if cid not in curricula or code not in courses or not courses[code]["is_active"]:
            raise ValueError(f"Missing curriculum course relationship: {cid}/{code}")
        if (cid, membership["course_group"]) not in groups:
            raise ValueError(f"Membership lacks official group: {cid}/{code}")
    for cid, group_key in groups:
        if cid not in curricula:
            raise ValueError(f"Group references missing curriculum: {cid}/{group_key}")
    entries_by_course: dict[tuple[int, str], list[dict]] = defaultdict(list)
    seen_occurrences = set()
    for entry in entries.values():
        cid, code, group_key = entry["curriculum_id"], entry["course_code"], entry["group_key"]
        if (cid, code) not in memberships or (cid, group_key) not in groups:
            raise ValueError(f"Entry lacks membership or group: {cid}/{code}")
        # A course can occur in more than one official elective orientation;
        # curriculum_courses records only its primary group.
        if entry["credits_in_source"] != courses[code]["credits"]:
            raise ValueError(f"Conflicting source credits: {cid}/{code}")
        occurrence = (cid, group_key, entry["source_row_number"], code)
        if occurrence in seen_occurrences:
            raise ValueError(f"Duplicate source occurrence: {occurrence}")
        seen_occurrences.add(occurrence)
        entries_by_course[(cid, code)].append(entry)
    if set(entries_by_course) != set(memberships):
        raise ValueError("Every curriculum membership needs source occurrence")
    # Enrichment is scoped by stable program identity, never shared course code
    # alone. Keep it inside the hashed source bundle for reproducible publication.
    metadata_rows = bundle.get("course_metadata", [])
    if not isinstance(metadata_rows, list):
        raise ValueError("course_metadata must be a list")
    enrichment_by_key = _indexed(metadata_rows, ("program_id", "code"), "course_metadata")
    expected_metadata_keys = {
        (PROGRAM_IDS[(curricula[cid]["major_code"], curricula[cid]["cohort_year"],
                      curricula[cid]["curriculum_version"])], code)
        for cid, code in memberships
    }
    if set(enrichment_by_key) - expected_metadata_keys:
        raise ValueError("Metadata references a course outside its program")
    enrichment_fields = {"name", "name_en", "hours", "instruction_language", "year", "suggested_term",
                         "topics", "orientation", "difficulty", "workload", "description", "career_paths"}
    for row in enrichment_by_key.values():
        values = row.get("values")
        if not isinstance(values, dict) or set(values) - enrichment_fields:
            raise ValueError("Unsupported course metadata fields")
        if not isinstance(row.get("field_evidence"), dict):
            raise ValueError("Metadata requires field_evidence")
        if set(row["field_evidence"]) - set(values):
            raise ValueError("Metadata evidence must describe supplied values")
        for field, value in values.items():
            if value is not None and not row["field_evidence"].get(field):
                raise ValueError(f"Non-null metadata {field} requires evidence")
    prereq_by_course: dict[tuple[int, str], dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))
    for cid, code, group_no, ref in prerequisites:
        if (cid, code) not in memberships or ref not in courses or not isinstance(group_no, int) or group_no < 1:
            raise ValueError(f"Invalid prerequisite relationship: {cid}/{code}/{ref}")
        if code == ref:
            raise ValueError(f"Self prerequisite: {cid}/{code}")
        prereq_by_course[(cid, code)][group_no].add(ref)
    for key, clauses in prereq_by_course.items():
        if set(clauses) != set(range(1, max(clauses) + 1)):
            raise ValueError(f"Prerequisite group numbering gap: {key}")

    source_rules = {}
    for key, occurrences in entries_by_course.items():
        rules = []
        for entry in occurrences:
            status = entry["prerequisite_parse_status"]
            raw = entry["prerequisite_source_text"]
            if status == "none" and raw and raw.strip():
                raise ValueError(f"Prerequisite text marked as absent: {key}")
            if status not in {"none", "normalized"}:
                continue
            parsed = parse_prerequisites(raw)
            if status == "normalized" and not parsed:
                raise ValueError(f"Normalized prerequisite text is empty: {key}")
            if any(ref not in courses for clause in parsed for ref in clause):
                raise ValueError(f"Normalized prerequisite references missing course: {key}")
            rules.append({"group_key": entry["group_key"], "source_row": entry["source_row_number"],
                          "pdf_page": entry["pdf_page"], "pdf_document": entry["pdf_document"],
                          "prerequisites": parsed})
        source_rules[key] = rules
        # A relational rule must match a complete source variant, never a
        # partial or invented merge. Ambiguous source cells remain blocked.
        if len(rules) == len(occurrences):
            actual = [sorted(refs) for _, refs in sorted(prereq_by_course[key].items())]
            if expression_key(actual) not in {
                expression_key(rule["prerequisites"]) for rule in rules
            }:
                raise ValueError(f"Prerequisite clauses do not match source text: {key}")

    result = []
    for curriculum in sorted(curricula.values(), key=lambda c: PROGRAM_IDS[(c["major_code"], c["cohort_year"], c["curriculum_version"])]):
        cid = curriculum["curriculum_id"]
        identity = (curriculum["major_code"], curriculum["cohort_year"], curriculum["curriculum_version"])
        program_id = PROGRAM_IDS[identity]
        group_rows = {key: row for (group_cid, key), row in groups.items() if group_cid == cid}
        member_rows = {code: row for (member_cid, code), row in memberships.items() if member_cid == cid}
        group_codes = {key: sorted({entry["course_code"] for entry in entries.values()
                                     if entry["curriculum_id"] == cid and entry["group_key"] == key})
                       for key in group_rows}
        source_doc = next(iter(entries_by_course[(cid, code)][0]["pdf_document"] for code in sorted(member_rows)))
        all_entries = [entry for (entry_cid, _), rows in entries_by_course.items() if entry_cid == cid for entry in rows]

        # I: one B1 language; II: five credits; V.2 is either parallel quotas
        # or exactly one orientation, depending on the source major.
        choice_specs = [("language", "Ngoại ngữ B1: chọn một trong bảy", 5, sorted(LANGUAGES), "I")]
        choice_specs.append(("field", group_rows["II"]["group_title"], 5, group_codes["II"], "II"))
        for key in sorted(group_rows):
            if key == "IV.2" or key.startswith("V.2."):
                row = group_rows[key]
                choice_specs.append((key, row["group_title"], row["min_credits_if_selected"], group_codes[key], key))
        choice_groups = [{
            "id": group_id, "name": name, "required_credits": credits,
            "course_codes": codes, "source_group_key": key,
            "source_note": group_rows[key]["group_note"], "selection_mode": "choose_credits",
        } for group_id, name, credits, codes, key in choice_specs]
        track_keys = [key for key in sorted(group_rows) if key.startswith("V.2.")]
        has_tracks = curriculum["major_code"] in {"7460101", "7460117"}
        tracks = [{"id": key, "name": group_rows[key]["group_title"], "choice_group_ids": [key]}
                  for key in track_keys] if has_tracks else []
        path_keys = [key for key in sorted(group_rows) if key.startswith("V.3.")]
        paths = []
        for key in path_keys:
            allowed = []
            if has_tracks and curriculum["major_code"] == "7460101" and key == "V.3.3":
                allowed = ["V.2.3"]
            elif has_tracks and curriculum["major_code"] == "7460101" and key == "V.3.2":
                allowed = ["V.2.1", "V.2.2"]
            paths.append({"id": key, "name": group_rows[key]["group_title"],
                          "course_codes": group_codes[key], "allowed_track_ids": allowed,
                          "source_note": group_rows[key]["group_note"]})
        block_rows = []
        for prefix, block_id in BLOCKS.items():
            keys = [key for key in group_rows if key == prefix or key.startswith(prefix + ".")]
            codes = sorted({code for key in keys for code in group_codes[key]})
            block_rows.append({"id": block_id, "name": prefix, "course_codes": codes,
                               "source_group_keys": sorted(keys), "required_credits": None})
        program = Program(
            program_id=program_id, name=majors[curriculum["major_code"]]["major_name"],
            total_credits=curriculum["credits_required"], catalog_status="draft_unverified",
            source_file=source_doc, source_pages=", ".join(map(str, sorted({e["pdf_page"] for e in all_entries}))),
            notes=[curriculum["note"],
                   "Prerequisite PDF review is recorded in the source bundle; full academic validation remains outstanding."
                   if bundle.get("prerequisite_pdf_review") else
                   "Source export has not been re-reviewed against original PDFs."],
            choice_groups=choice_groups,
            track_selection={"mode": "exactly_one_track" if has_tracks else "not_applicable", "tracks": tracks},
            graduation_selection={"mode": "exactly_one_path", "required_credits": 7, "paths": paths},
            excluded_from_total=sorted(EXCLUDED), blocks=block_rows,
            source_curriculum={k: v for k, v in curriculum.items() if k != "curriculum_id"},
            source_group_rules=[{"group_key": key, **row} for key, row in sorted(group_rows.items())],
        )
        runtime_courses = []
        for code, membership in sorted(member_rows.items()):
            source_course = courses[code]
            occurrences = sorted(entries_by_course[(cid, code)], key=lambda e: (e["pdf_page"], e["source_row_number"], e["entry_id"]))
            statuses = {e["prerequisite_parse_status"] for e in occurrences}
            raw_texts = sorted({e["prerequisite_source_text"] for e in occurrences if e["prerequisite_source_text"]})
            clauses = prereq_by_course.get((cid, code), {})
            expression = [sorted(clauses[n]) for n in sorted(clauses)]
            rules = source_rules[(cid, code)]
            variants = {expression_key(rule["prerequisites"]) for rule in rules}
            conflict = len(variants) > 1
            if conflict:
                prereq_status = "conflict"
            elif statuses - {"none", "normalized"}:
                prereq_status = "unknown"
            elif raw_texts and not expression:
                prereq_status = "unknown"
            else:
                prereq_status = "draft_unverified"
            key = membership["course_group"]
            requirement = "graduation" if key.startswith("V.3.") else ("required_excluded" if code in EXCLUDED else
                          "elective" if code in LANGUAGES or key == "II" or key == "IV.2" or key.startswith("V.2.") else "required")
            first = occurrences[0]
            enrichment = enrichment_by_key.get((program_id, code), {"values": {}, "field_evidence": {}})
            evidence = {field: _evidence(first, field) for field in
                        ("code", "name", "credits", "block", "requirement_type", "counted_in_total",
                         "prerequisites", "source_page", "choice_group_ids", "graduation_path_ids")}
            if conflict:
                evidence["prerequisites"] = [
                    {**item, "status": "conflict"}
                    for entry in occurrences for item in _evidence(entry, "prerequisites")
                ]
            if membership["suggested_semester"] is not None:
                evidence["suggested_term"] = _evidence(first, "suggested_term")
            evidence.update(enrichment["field_evidence"])
            course_values = {"suggested_term": membership["suggested_semester"], **enrichment["values"]}
            applicable_name = course_values.pop("name", source_course["course_name"])
            if (membership["suggested_semester"] is not None
                    and course_values["suggested_term"] != membership["suggested_semester"]):
                raise ValueError(f"Metadata semester conflicts with source membership: {program_id}/{code}")
            runtime_courses.append(Course(
                code=code, name=applicable_name, credits=source_course["credits"],
                block=BLOCKS[key.split(".")[0]], requirement_type=requirement,
                counted_in_total=code not in EXCLUDED, prerequisites=expression,
                prerequisites_raw=" | ".join(raw_texts) or None, prerequisite_status=prereq_status,
                prerequisite_variants=[list(map(list, v)) for v in sorted(variants)] if conflict else [],
                external_prerequisite_codes=sorted({ref for variant in
                    ([expression] + [list(map(list, v)) for v in variants] if conflict else [expression])
                    for clause in variant for ref in clause if ref not in member_rows}),
                choice_group_ids=[group_id for group_id, _, _, codes, _ in choice_specs if code in codes],
                graduation_path_ids=[key] if key.startswith("V.3.") else [],
                source_page=first["pdf_page"], source_rows=sorted({e["source_row_number"] for e in occurrences
                                                                    if e["source_row_number"] is not None}),
                **course_values,
                field_evidence=evidence, source_occurrences=occurrences,
                source_membership=membership, source_course=source_course,
                source_prerequisite_parse_statuses=sorted(statuses),
                source_prerequisite_rules=rules,
            ))
        catalog = Catalog(program=program, courses=runtime_courses,
                          metadata_schema_version="1.0", vocabulary_version="1.0", vocabulary=VOCABULARY,
                          prerequisite_pdf_review=bundle.get("prerequisite_pdf_review"),
                          metadata_source_manifest=bundle.get("metadata_source_manifest", []))
        validate_catalog(catalog)
        result.append(catalog)
    return result
