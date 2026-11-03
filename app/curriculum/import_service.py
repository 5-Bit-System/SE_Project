"""Service for parsing, validating, and importing curriculum revisions."""

import csv
import hashlib
import io
import re
from typing import Any


def sanitize_cell(value: str) -> str:
    """Strip dangerous leading formula triggers (=, +, -, @, tab, newline) to prevent CSV injection."""
    val = value.strip()
    if not val:
        return ""
    # If starting with formula operators or DDE commands, sanitize with leading apostrophe or strip
    if val[0] in ("=", "+", "@") or val.startswith("-cmd"):
        val = "'" + val
    return val


def detect_prerequisite_cycles(graph: dict[str, list[str]]) -> tuple[bool, list[str]]:
    """Detect cycles in prerequisite directed graph using DFS 3-color approach.
    Returns (has_cycle, cycle_nodes).
    """
    visited = {}  # 0: unvisited, 1: visiting, 2: visited
    parent = {}

    for node in graph:
        visited[node] = 0

    cycle_path = []

    def dfs(u):
        visited[u] = 1
        for v in graph.get(u, []):
            if v not in visited:
                continue
            if visited[v] == 1:
                # Cycle found
                cycle_path.append(v)
                curr = u
                while curr != v and curr in parent:
                    cycle_path.append(curr)
                    curr = parent[curr]
                cycle_path.append(v)
                cycle_path.reverse()
                return True
            if visited[v] == 0:
                parent[v] = u
                if dfs(v):
                    return True
        visited[u] = 2
        return False

    for node in graph:
        if visited[node] == 0:
            if dfs(node):
                return True, cycle_path
    return False, []


def validate_and_parse_csv(
    content: str,
    program_id: str,
    version_title: str,
    cohort: str | None = None,
) -> dict[str, Any]:
    """Parse CSV text, enforce rules, and return structured validation summary and courses."""
    errors = []
    warnings = []
    courses = []
    seen_codes = set()
    prereq_graph = {}

    # Calculate SHA-256
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        return {
            "valid": False,
            "errors": [{"row": 0, "column": "header", "message": "Tệp CSV rỗng hoặc thiếu tiêu đề cột"}],
            "warnings": [],
            "stats": {"course_count": 0, "total_credits": 0},
            "courses": [],
            "digest": digest,
        }

    # Normalize header fieldnames
    clean_fieldnames = [f.strip().lower() for f in reader.fieldnames if f]
    required = {"code", "name", "credits"}
    if not required.issubset(set(clean_fieldnames)):
        return {
            "valid": False,
            "errors": [{"row": 0, "column": "header", "message": f"Thiếu các cột bắt buộc: {required - set(clean_fieldnames)}"}],
            "warnings": [],
            "stats": {"course_count": 0, "total_credits": 0},
            "courses": [],
            "digest": digest,
        }

    total_credits = 0

    for idx, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): v for k, v in raw_row.items() if k}
        code = sanitize_cell(row.get("code", "")).upper()
        name = sanitize_cell(row.get("name", ""))
        credits_str = sanitize_cell(row.get("credits", "0"))
        prereqs_raw = sanitize_cell(row.get("prerequisites", ""))
        block = sanitize_cell(row.get("block", "Chưa phân loại"))
        suggested_term = sanitize_cell(row.get("suggested_term", ""))

        if not code:
            errors.append({"row": idx, "column": "code", "message": "Mã học phần không được để trống"})
            continue

        if code in seen_codes:
            errors.append({"row": idx, "column": "code", "message": f"Trùng mã học phần: {code}"})
        else:
            seen_codes.add(code)

        if not name:
            errors.append({"row": idx, "column": "name", "message": f"Tên học phần không được để trống (Mã: {code})"})

        # Validate credits
        try:
            credits_val = float(credits_str)
            if credits_val < 0 or credits_val > 20:
                errors.append({"row": idx, "column": "credits", "message": f"Tín chỉ không hợp lệ ({credits_val}) cho môn {code}. Phải từ 0 đến 20."})
            else:
                total_credits += int(credits_val) if credits_val.is_integer() else credits_val
        except ValueError:
            errors.append({"row": idx, "column": "credits", "message": f"Giá trị tín chỉ '{credits_str}' không phải là số hợp lệ cho môn {code}."})
            credits_val = 0

        # Parse prerequisites (comma, semicolon, or space-separated)
        prereq_list = [p.strip().upper() for p in re.split(r"[,;|\s]+", prereqs_raw) if p.strip()]
        prereq_graph[code] = prereq_list

        courses.append({
            "code": code,
            "name": name,
            "credits": credits_val,
            "prerequisites": prereq_list,
            "block": block,
            "suggested_term": int(suggested_term) if suggested_term.isdigit() else None,
        })

    # Check for dangling prerequisites (prereq code not defined in curriculum)
    for code, prereqs in prereq_graph.items():
        for p in prereqs:
            if p not in seen_codes:
                warnings.append({
                    "column": "prerequisites",
                    "message": f"Môn '{code}' yêu cầu môn tiên quyết '{p}' chưa có trong danh mục của chương trình này.",
                })

    # Check for prerequisite cycles
    has_cycle, cycle_path = detect_prerequisite_cycles(prereq_graph)
    if has_cycle:
        errors.append({
            "column": "prerequisites",
            "message": f"Phát hiện Chu trình tiên quyết (vòng lặp vô tận): {' -> '.join(cycle_path)}",
        })

    is_valid = len(errors) == 0

    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "course_count": len(courses),
            "total_credits": total_credits,
        },
        "courses": courses,
        "digest": digest,
    }
