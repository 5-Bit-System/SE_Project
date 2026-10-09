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


def unique_index(items: list[dict], key: str, context: str) -> dict[str, dict]:
    indexed = {}
    for item in items:
        value = item[key]
        if value in indexed:
            raise ValueError(f"Duplicate {key} in {context}: {value}")
        indexed[value] = item
    return indexed


def source_occurrences(program: dict, rows: list[dict]) -> dict[str, list[dict]]:
    by_code: dict[str, list[dict]] = {}
    seen = set()
    for row in rows:
        number = row["source_row"]
        if number is not None and (type(number) is not int or number <= 0):
            raise ValueError(f"Invalid source row: {program['program_id']}/{row['code']}, source_row={number!r}")
        identity = (row["source_row"], row["code"])
        if identity in seen:
            raise ValueError(
                f"Duplicate source entry: {program['program_id']}/{row['code']}, "
                f"source_row={row['source_row']}, page={row['source_page']}"
            )
        seen.add(identity)
        by_code.setdefault(row["code"], []).append(row)
    return by_code


def source_prerequisite_variants(program_id: str, code: str, occurrences: list[dict]) -> list[list[list[str]]]:
    variants = []
    signatures = set()
    for row in occurrences:
        try:
            clauses = prerequisite_clauses(row["prerequisites_raw"])
        except ValueError as exc:
            raise ValueError(
                f"{program_id}/{code}, source_row={row['source_row']}, "
                f"page={row['source_page']}: {exc}"
            ) from exc
        signature = clause_signature(clauses)
        if signature not in signatures:
            variants.append(clauses)
            signatures.add(signature)
    return variants


def build_courses(program: dict, rows: list[dict]) -> list[dict]:
    by_code = source_occurrences(program, rows)
    known = set(by_code)
    required = {code for block in program["blocks"] for code in block["required_course_codes"]}
    graduation = {
        code for path in program["graduation_selection"]["paths"] for code in path["course_codes"]
    }
    courses = []
    for code, occurrences in by_code.items():
        first = occurrences[0]
        for row in occurrences[1:]:
            if any(row[field] != first[field] for field in ("name", "credits", "hours")):
                raise ValueError(
                    f"Conflicting course metadata: {program['program_id']}/{code}, "
                    f"source_rows={[item['source_row'] for item in occurrences]}"
                )
        variants = source_prerequisite_variants(program["program_id"], code, occurrences)
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
    context = program["program_id"]
    known = unique_index(courses, "code", f"catalog {context}")
    groups = unique_index(program["choice_groups"], "id", f"choice groups {context}")
    by_code = source_occurrences(program, rows)
    numbered = {row["source_row"] for row in rows if row["source_row"] is not None}
    expected = set(range(1, program["digitization"]["numbered_source_rows"] + 1))
    if numbered != expected:
        raise ValueError(f"Missing/unexpected source rows: {numbered ^ expected}")
    if len(rows) != program["digitization"]["source_course_entries"]:
        raise ValueError("Source entry count mismatch")
    if sum(row["source_row"] is None for row in rows) != program["digitization"]["unnumbered_course_rows"]:
        raise ValueError("Unnumbered source entry count mismatch")
    if set(known) != set(by_code):
        raise ValueError(
            f"Catalog/source course coverage mismatch in {context}: "
            f"missing={sorted(set(by_code) - set(known))}, "
            f"unexpected={sorted(set(known) - set(by_code))}"
        )
    if len(courses) != program["digitization"]["unique_course_codes"]:
        raise ValueError("Unique course count mismatch")
    if sum(block["required_credits"] for block in program["blocks"]) != program["total_credits"]:
        raise ValueError("Block credits do not match program total")
    page_first, page_last = map(int, program["source_pages"].split("-"))
    for row in rows:
        page = row.get("source_page")
        if type(page) is not int or not page_first <= page <= page_last:
            raise ValueError(f"Missing/invalid source page outside curriculum table: {context}/{row['code']}, source_row={row['source_row']}, page={page!r}")
        if row["credits"] <= 0 or (row["hours"] and any(value < 0 for value in row["hours"].values())):
            raise ValueError(f"Invalid credit/hour values: {context}/{row['code']}, source_row={row['source_row']}")

    def check_members(codes: list[str], label: str) -> None:
        if len(codes) != len(set(codes)):
            raise ValueError(f"Duplicate group member: {label}")
        unknown = set(codes) - set(known)
        if unknown:
            raise ValueError(f"Unknown course in {label}: {sorted(unknown)}")

    for group in program["choice_groups"]:
        check_members(group["course_codes"], f"choice group {group['id']}")
        unknown_rows = set(group["source_rows"]) - numbered
        if unknown_rows:
            raise ValueError(f"Unknown source rows in group {group['id']}: {sorted(unknown_rows)}")
        if sum(known[code]["credits"] for code in group["course_codes"]) != group["listed_credits"]:
            raise ValueError(f"Listed group credits mismatch: {group['id']}")
        source_members = {row["code"] for row in rows if row["source_row"] in group["source_rows"]}
        if source_members != set(group["course_codes"]):
            raise ValueError(f"Group members differ from source rows: {group['id']}")
    # Rebuild from every source occurrence so neither a missing variant nor a
    # guessed correction can pass merely by retaining the right record counts.
    expected_courses = build_courses(program, rows)
    for expected_course in expected_courses:
        course = known[expected_course["code"]]
        group_ids = course["choice_group_ids"]
        if len(group_ids) != len(set(group_ids)):
            raise ValueError(f"Duplicate choice group reference: {context}/{course['code']}")
        if not set(group_ids) <= set(groups):
            raise ValueError(f"Unknown choice group: {context}/{course['code']}, {sorted(set(group_ids) - set(groups))}")
        for field in (
            "name", "name_en", "credits", "hours", "block", "choice_group_ids",
            "source_rows", "source_page", "prerequisites_raw", "prerequisites",
            "prerequisite_variants", "prerequisite_status", "external_prerequisite_codes",
        ):
            if course.get(field) != expected_course[field]:
                raise ValueError(
                    f"Catalog {field} differs from source: {context}/{course['code']}, "
                    f"source_rows={expected_course['source_rows']}"
                )
    tracks = program["track_selection"]["tracks"]
    track_ids = set(unique_index(tracks, "id", f"tracks {context}"))
    if tracks:
        for track in tracks:
            unknown_groups = set(track["choice_group_ids"]) - set(groups)
            if unknown_groups:
                raise ValueError(f"Unknown choice group in track {track['id']}: {sorted(unknown_groups)}")
            if len(track["choice_group_ids"]) != len(set(track["choice_group_ids"])):
                raise ValueError(f"Duplicate choice group in track: {track['id']}")
            if sum(groups[group_id]["required_credits"] for group_id in track["choice_group_ids"]) != program["major_credit_structure"]["elective"]:
                raise ValueError(f"Track elective credits mismatch: {track['id']}")
    else:
        if sum(group["required_credits"] for group in groups.values() if group["id"] not in {"foreign_language_b1", "field_electives", "programming"}) != program["major_credit_structure"]["elective"]:
            raise ValueError("Major elective group quotas mismatch")
    for path in program["graduation_selection"]["paths"]:
        check_members(path["course_codes"], f"graduation path {path['id']}")
        if sum(known[code]["credits"] for code in path["course_codes"]) != program["graduation_selection"]["required_credits"]:
            raise ValueError(f"Graduation path credits mismatch: {path['id']}")
        if not set(path["allowed_track_ids"]) <= track_ids:
            raise ValueError(f"Unknown graduation track: {path['id']}")
    for block in program["blocks"]:
        check_members(block["course_codes"], f"block {block['id']}")
        check_members(block["required_course_codes"], f"required block {block['id']}")
        if not set(block["required_course_codes"]) <= set(block["course_codes"]):
            raise ValueError(f"Required courses outside block: {block['id']}")
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
        for variant in known[code]["prerequisite_variants"]:
            for clause in variant:
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
        "prerequisite_conflicts": [
            {
                "code": course["code"],
                "source_rows": course["source_rows"],
                "source_entries": [
                    {key: row[key] for key in ("source_row", "source_page", "prerequisites_raw")}
                    for row in by_code[course["code"]]
                ],
                "prerequisite_variants": course["prerequisite_variants"],
            }
            for course in courses if course["prerequisite_status"] == "source_conflict"
        ],
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
        target = directory / "courses.json"
        try:
            program = json.loads((directory / "curriculum.json").read_text(encoding="utf-8"))
            rows = json.loads((directory / "source_rows.json").read_text(encoding="utf-8"))
            courses = build_courses(program, rows) if args.write else json.loads(target.read_text(encoding="utf-8"))
            reports.append(check_curriculum(program, rows, courses))
            if not args.write and courses != build_courses(program, rows):
                raise ValueError(f"Catalog differs from source transcription: {target}")
        except ValueError as exc:
            parser.exit(1, f"{directory}: {exc}\n")
        if args.write:
            target.write_text(json.dumps(courses, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.report:
        print(json.dumps({"programs": reports}, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            print(f"{report['program_id']}: {report['unique_course_codes']} courses, {report['numbered_source_rows']} numbered rows — passed")


if __name__ == "__main__":
    main()
