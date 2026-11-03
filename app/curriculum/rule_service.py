"""Service for editing prerequisite rules and constructing dependency graphs."""

import copy
from typing import Any

from app.curriculum.import_service import detect_prerequisite_cycles


def normalize_prerequisites(raw: list[Any]) -> list[list[str]]:
    """Ensure prerequisites are in list[list[str]] format (AND of OR groups)."""
    normalized = []
    for item in raw:
        if isinstance(item, str):
            clean = item.strip().upper()
            if clean:
                normalized.append([clean])
        elif isinstance(item, (list, tuple)):
            sub = [str(x).strip().upper() for x in item if str(x).strip()]
            if sub:
                normalized.append(sub)
    return normalized


def extract_flat_prereqs(prereqs: list[list[str]]) -> list[str]:
    """Flatten prerequisites list into unique course codes."""
    res = set()
    for group in prereqs:
        for code in group:
            res.add(code)
    return sorted(res)


def validate_prerequisite_rules(
    target_code: str,
    new_prerequisites: list[list[str]],
    all_courses: list[dict[str, Any]],
) -> tuple[bool, list[str]]:
    """Validate prerequisite rules for a course: check self-reference, cycles, missing targets."""
    errors = []
    target_code = target_code.upper()
    existing_codes = {c["code"].upper() for c in all_courses}

    flat_prereqs = extract_flat_prereqs(new_prerequisites)

    # 1. Self reference check
    if target_code in flat_prereqs:
        errors.append(f"Môn học '{target_code}' không thể tự làm tiên quyết cho chính mình.")

    # 2. Build prerequisite graph with this tentative change
    graph: dict[str, list[str]] = {}
    for c in all_courses:
        code = c["code"].upper()
        if code == target_code:
            graph[code] = flat_prereqs
        else:
            raw = c.get("prerequisites", [])
            # Normalize whatever format existing courses have
            if isinstance(raw, list):
                if raw and isinstance(raw[0], list):
                    graph[code] = extract_flat_prereqs(raw)
                else:
                    graph[code] = [str(x).upper() for x in raw]
            else:
                graph[code] = []

    # 3. Check for cycles
    has_cycle, cycle_path = detect_prerequisite_cycles(graph)
    if has_cycle:
        errors.append(f"Phát hiện Chu trình tiên quyết: {' -> '.join(cycle_path)}")

    # 4. Check for missing targets (soft warning or note)
    missing = [p for p in flat_prereqs if p not in existing_codes]
    if missing:
        errors.append(f"Môn tiên quyết '{', '.join(missing)}' không nằm trong chương trình này.")

    return len(errors) == 0, errors


def build_prerequisite_graph(courses: list[dict[str, Any]]) -> dict[str, Any]:
    """Construct nodes and edges for dependency graph visualization."""
    nodes = []
    edges = []
    edge_set = set()

    for c in courses:
        code = c["code"].upper()
        nodes.append(
            {
                "id": code,
                "label": c.get("name", code),
                "credits": c.get("credits", 0),
                "block": c.get("block", "Chưa phân loại"),
                "suggested_term": c.get("suggested_term"),
            }
        )

        raw_prereqs = c.get("prerequisites", [])
        if isinstance(raw_prereqs, list):
            for item in raw_prereqs:
                if isinstance(item, list):
                    for p in item:
                        p_code = str(p).upper()
                        key = (p_code, code)
                        if key not in edge_set:
                            edge_set.add(key)
                            edges.append({"from": p_code, "to": code, "type": "prerequisite"})
                elif isinstance(item, str) and item.strip():
                    p_code = item.strip().upper()
                    key = (p_code, code)
                    if key not in edge_set:
                        edge_set.add(key)
                        edges.append({"from": p_code, "to": code, "type": "prerequisite"})

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": len(nodes),
        "total_edges": len(edges),
    }


def update_course_rules(
    revision_payload: dict[str, Any],
    target_code: str,
    new_prerequisites: list[list[str]],
) -> dict[str, Any]:
    """Update a course's prerequisites in the revision payload."""
    revision_payload = copy.deepcopy(revision_payload)
    courses = revision_payload.get("courses", [])
    target_code = target_code.upper()
    found = False

    for c in courses:
        if c["code"].upper() == target_code:
            c["prerequisites"] = new_prerequisites
            found = True
            break

    if not found:
        raise ValueError(f"Course {target_code} not found in revision payload")

    revision_payload["courses"] = courses
    if revision_payload.get('runtime_catalog'):
        from app.catalog_contracts import digest
        # Update only the matching course, preserving all other catalog structure.
        candidate = revision_payload['runtime_catalog']
        for course in candidate['courses']:
            if course['code'] == target_code:
                course.update(prerequisites=new_prerequisites, prerequisite_variants=[],
                              external_prerequisite_codes=[], prerequisite_status='draft_unverified',
                              source_status='draft_unverified', prerequisites_raw=str(new_prerequisites))
                course['field_evidence']['prerequisites'] = [{
                    'source_ref': 'admin-draft:' + digest(new_prerequisites), 'locator': target_code,
                    'method': 'transcription', 'status': 'draft_unverified',
                }]
        candidate['program']['catalog_revision'] = None
        candidate['program']['catalog_revision'] = digest(candidate)
    return revision_payload



def validate_full_revision_payload(payload: dict[str, Any]) -> dict[str, Any]:
    from app.curriculum.validation import validate_payload
    return validate_payload(payload)
