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


def validate_and_parse_csv(content: str, program_id: str, version_title: str,
                           cohort: str | None = None) -> dict[str, Any]:
    from app.curriculum.validation import validate_payload
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    courses, parse_errors = [], []
    reader = csv.DictReader(io.StringIO(content))
    headers = [f.strip().lower() for f in reader.fieldnames or []]
    if len(content.encode("utf-8")) > 1_000_000:
        parse_errors.append({"column": "file", "message": "Tệp vượt giới hạn 1 MB"})
    if not {"code", "name", "credits"} <= set(headers) or len(headers) != len(set(headers)):
        parse_errors.append({"column": "header", "message": "Thiếu cột bắt buộc hoặc trùng tiêu đề cột"})
    if not parse_errors:
        try:
            for index, row in enumerate(reader):
                if index >= 1000:
                    parse_errors.append({"column": "file", "message": "Tệp vượt giới hạn 1000 dòng"})
                    break
                row = {k.strip().lower(): v for k, v in row.items() if k}
                def cell(key, default=""):
                    return sanitize_cell(row.get(key) or default)
                raw_credits = cell("credits")
                try:
                    credits = float(raw_credits)
                    if not __import__('math').isfinite(credits):
                        credits = raw_credits
                except ValueError:
                    credits = raw_credits
                # Comma/semicolon-separated prerequisites are AND; explicit | is OR.
                prereqs = [[p.strip().upper() for p in group.split('|') if p.strip()]
                           for group in re.split(r"[,;\s]+", cell("prerequisites")) if group.strip()]
                courses.append({"code": cell("code").upper(), "name": cell("name"),
                    "credits": credits, "prerequisites": prereqs, "block": cell("block", "general"),
                    "suggested_term": int(cell("suggested_term")) if cell("suggested_term").isdigit() else None})
        except csv.Error:
            parse_errors.append({"column": "file", "message": "Cấu trúc CSV không hợp lệ"})
    result = validate_payload({"courses": courses, "import_errors": parse_errors})
    result.update(digest=digest, parse_errors=parse_errors)
    return result
