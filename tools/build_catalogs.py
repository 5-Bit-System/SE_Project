"""Build course catalogs from the transcribed source rows and curriculum metadata.

python tools/build_catalogs.py --check
python tools/build_catalogs.py --check --report
python tools/build_catalogs.py --write  # regenerate after reviewing source edits
"""

import argparse
from itertools import product
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1] / "data" / "curricula"
TOKEN = re.compile(r"[A-Z]{3}\d{4}E?|[()/&]")


def prerequisite_clauses(raw: str) -> list[list[str]]:
    """Parse slash-OR / line-AND, distributing parentheses into AND-of-OR."""
    if not raw.strip():
        return []
    expression = re.sub(r"\s*/\s*", "/", raw.strip())
    expression = re.sub(r"\s+", "&", expression)
    tokens = TOKEN.findall(expression)
    if "".join(tokens) != expression:
        raise ValueError(f"Unrecognized prerequisite expression: {raw!r}")
    position = 0

    def atom() -> list[list[str]]:
        nonlocal position
        if position >= len(tokens):
            raise ValueError(f"Incomplete prerequisite expression: {raw!r}")
        token = tokens[position]
        position += 1
        if token == "(":
            result = parse_or()
            if position >= len(tokens) or tokens[position] != ")":
                raise ValueError(f"Unclosed parentheses: {raw!r}")
            position += 1
            return result
        if not re.fullmatch(r"[A-Z]{3}\d{4}E?", token):
            raise ValueError(f"Expected course code: {raw!r}")
        return [[token]]

    def parse_and() -> list[list[str]]:
        nonlocal position
        result = atom()
        while position < len(tokens) and tokens[position] == "&":
            position += 1
            result.extend(atom())
        return result

    def parse_or() -> list[list[str]]:
        nonlocal position
        result = parse_and()
        while position < len(tokens) and tokens[position] == "/":
            position += 1
            other = parse_and()
            result = [list(dict.fromkeys(left + right)) for left, right in product(result, other)]
        return result

    result = parse_or()
    if position != len(tokens):
        raise ValueError(f"Unexpected tokens: {raw!r}")
    return result


def clause_signature(clauses: list[list[str]]) -> tuple:
    return tuple(sorted(tuple(sorted(set(clause))) for clause in clauses))


def build_courses(program: dict, rows: list[dict]) -> list[dict]:
    known = {row["code"] for row in rows}
    by_code: dict[str, list[dict]] = {}
    for row in rows:
        by_code.setdefault(row["code"], []).append(row)
    required = {code for block in program["blocks"] for code in block["required_course_codes"]}
    graduation = {
        code for path in program["graduation_selection"]["paths"] for code in path["course_codes"]
    }
    courses = []
    for code, occurrences in by_code.items():
        first = occurrences[0]
        for row in occurrences[1:]:
            if (row["name"], row["credits"], row["hours"]) != (first["name"], first["credits"], first["hours"]):
                raise ValueError(f"Conflicting course metadata: {program['program_id']}/{code}")
        variants = []
        signatures = set()
        for row in occurrences:
            clauses = prerequisite_clauses(row["prerequisites_raw"])
            signature = clause_signature(clauses)
            if signature not in signatures:
                variants.append(clauses)
                signatures.add(signature)
        course_blocks = [block["id"] for block in program["blocks"] if code in block["course_codes"]]
        if len(course_blocks) != 1:
            raise ValueError(f"Expected one block for {code}: {course_blocks}")
        excluded = code in program["excluded_from_total"]
        references = {reference for clauses in variants for clause in clauses for reference in clause}
        courses.append({
            "code": code,
            "name": first["name"],
            "name_en": first["name_en"],
            "credits": first["credits"],
            "block": course_blocks[0],
            "requirement_type": "required_excluded" if excluded else "graduation" if code in graduation else "required" if code in required else "elective",
            "counted_in_total": not excluded,
            "hours": first["hours"],
            "instruction_language": "en" if code.endswith("E") else None,
            "prerequisites": variants[0],
            "prerequisites_raw": first["prerequisites_raw"],
            "prerequisite_status": "source_conflict" if len(variants) > 1 else "transcribed",
            "prerequisite_variants": variants,
            "external_prerequisite_codes": sorted(references - known),
            "choice_group_ids": [group["id"] for group in program["choice_groups"] if code in group["course_codes"]],
            "graduation_path_ids": [path["id"] for path in program["graduation_selection"]["paths"] if code in path["course_codes"]],
            "source_page": first["source_page"],
            "source_rows": list(dict.fromkeys(row["source_row"] for row in occurrences if row["source_row"] is not None)),
        })
    return courses


def check_curriculum(program: dict, rows: list[dict], courses: list[dict]) -> dict:
    numbered = {row["source_row"] for row in rows if row["source_row"] is not None}
    expected = set(range(1, program["digitization"]["numbered_source_rows"] + 1))
    if numbered != expected:
        raise ValueError(f"Missing/unexpected source rows: {numbered ^ expected}")
    if len(rows) != program["digitization"]["source_course_entries"]:
        raise ValueError("Source entry count mismatch")
    if sum(row["source_row"] is None for row in rows) != program["digitization"]["unnumbered_course_rows"]:
        raise ValueError("Unnumbered source entry count mismatch")
    if len(courses) != program["digitization"]["unique_course_codes"]:
        raise ValueError("Unique course count mismatch")
    if sum(block["required_credits"] for block in program["blocks"]) != program["total_credits"]:
        raise ValueError("Block credits do not match program total")
    known = {course["code"]: course for course in courses}
    page_first, page_last = map(int, program["source_pages"].split("-"))
    for row in rows:
        if not page_first <= row["source_page"] <= page_last:
            raise ValueError("Source page outside curriculum table")
        if row["credits"] <= 0 or (row["hours"] and any(value < 0 for value in row["hours"].values())):
            raise ValueError("Invalid credit/hour values")
    for group in program["choice_groups"]:
        if len(group["course_codes"]) != len(set(group["course_codes"])):
            raise ValueError(f"Duplicate group member: {group['id']}")
        if sum(known[code]["credits"] for code in group["course_codes"]) != group["listed_credits"]:
            raise ValueError(f"Listed group credits mismatch: {group['id']}")
        source_members = {row["code"] for row in rows if row["source_row"] in group["source_rows"]}
        if source_members != set(group["course_codes"]):
            raise ValueError(f"Group members differ from source rows: {group['id']}")
    groups = {group["id"]: group for group in program["choice_groups"]}
    tracks = program["track_selection"]["tracks"]
    if tracks:
        for track in tracks:
            if sum(groups[group_id]["required_credits"] for group_id in track["choice_group_ids"]) != program["major_credit_structure"]["elective"]:
                raise ValueError(f"Track elective credits mismatch: {track['id']}")
    else:
        if sum(group["required_credits"] for group in groups.values() if group["id"] not in {"foreign_language_b1", "field_electives", "programming"}) != program["major_credit_structure"]["elective"]:
            raise ValueError("Major elective group quotas mismatch")
    for path in program["graduation_selection"]["paths"]:
        if sum(known[code]["credits"] for code in path["course_codes"]) != program["graduation_selection"]["required_credits"]:
            raise ValueError(f"Graduation path credits mismatch: {path['id']}")
        if not set(path["allowed_track_ids"]) <= {track["id"] for track in tracks}:
            raise ValueError(f"Unknown graduation track: {path['id']}")
    for block in program["blocks"]:
        compulsory = sum(known[code]["credits"] for code in block["required_course_codes"])
        if block["id"] == "general" and compulsory + 5 != block["required_credits"]:
            raise ValueError("General required credits + one B1 course mismatch")
        if block["id"] == "discipline" and compulsory != block["required_credits"]:
            raise ValueError("Discipline required credits mismatch")
        if block["id"] == "group":
            programming = next((group["required_credits"] for group in program["choice_groups"] if group["id"] == "programming"), 0)
            if compulsory + programming != block["required_credits"]:
                raise ValueError("Group required credits mismatch")
        if block["id"] == "major":
            structure = program["major_credit_structure"]
            if compulsory != structure["required"] or sum(structure[key] for key in ("required", "elective", "graduation")) != block["required_credits"]:
                raise ValueError("Major credit structure mismatch")
    visiting, visited = set(), set()

    def visit(code: str) -> None:
        if code in visiting:
            raise ValueError(f"Prerequisite cycle involving {code}")
        if code in visited:
            return
        visiting.add(code)
        for clause in known[code]["prerequisites"]:
            for reference in clause:
                if reference in known:
                    visit(reference)
        visiting.remove(code)
        visited.add(code)

    for code in known:
        visit(code)
    return {
        "program_id": program["program_id"],
        "numbered_source_rows": len(numbered),
        "unnumbered_course_rows": sum(row["source_row"] is None for row in rows),
        "source_course_entries": len(rows),
        "unique_course_codes": len(courses),
        "total_credits": program["total_credits"],
        "status": "passed",
        "digitization_status": program["digitization"]["status"],
        "review_status": program["digitization"]["review_status"],
        "external_prerequisite_codes": sorted({code for course in courses for code in course["external_prerequisite_codes"]}),
        "conflicting_prerequisite_courses": [course["code"] for course in courses if course["prerequisite_status"] == "source_conflict"],
        "source_issue_count": len(program["source_issues"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="Check without changing files (default)")
    action.add_argument("--write", action="store_true", help="Regenerate courses.json after reviewing source edits")
    parser.add_argument("--report", action="store_true", help="Print the validation report as JSON")
    args = parser.parse_args()
    reports = []
    for directory in sorted(ROOT.iterdir()):
        if not directory.is_dir():
            continue
        program = json.loads((directory / "curriculum.json").read_text(encoding="utf-8"))
        rows = json.loads((directory / "source_rows.json").read_text(encoding="utf-8"))
        courses = build_courses(program, rows)
        reports.append(check_curriculum(program, rows, courses))
        target = directory / "courses.json"
        if args.write:
            target.write_text(json.dumps(courses, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        elif json.loads(target.read_text(encoding="utf-8")) != courses:
            raise ValueError(f"Catalog differs from source transcription: {target}")
    if args.report:
        print(json.dumps({"programs": reports}, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            print(f"{report['program_id']}: {report['unique_course_codes']} courses, {report['numbered_source_rows']} numbered rows — passed")


if __name__ == "__main__":
    main()
