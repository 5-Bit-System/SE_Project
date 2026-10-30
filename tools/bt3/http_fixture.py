"""Synthetic file-backed catalog and independent, literal HTTP workload oracles."""

import json
from pathlib import Path

PROGRAM = "bt3_search"


def write_fixture(root: Path) -> None:
    rows = [dict(code=f"S{i:04}", name=f"Systems {i // 3:03}",
                 name_en="Bridge Methods" if i % 10 == 0 else None,
                 credits=1 + i % 5, block="major" if i % 2 == 0 else "general",
                 requirement_type="elective" if i % 4 < 2 else "required")
            for i in range(240)]
    # Four catalogs satisfy the real storage readiness invariant, without source/DB data.
    for name in (PROGRAM, "bt3_other_a", "bt3_other_b", "bt3_other_c"):
        directory = root / name
        directory.mkdir(parents=True)
        program = dict(program_id=name, name="Invented BT3 HTTP catalog", total_credits=720,
                       source_file="synthetic-only", source_pages="none",
                       catalog_revision="synthetic-http-v1")
        courses = list(reversed(rows)) if name == PROGRAM else [
            dict(code="F01", name="Foreign fixture", credits=3, block="general")]
        (directory / "curriculum.json").write_text(json.dumps(program), encoding="utf-8")
        (directory / "courses.json").write_text(json.dumps(courses), encoding="utf-8")
    (root / "BT3_SYNTHETIC_ONLY").write_text("No student or official data", encoding="utf-8")


# Explicit oracle for the nontrivial credits/page case, derived from the fixture congruences:
# major AND elective => indices divisible by 4. Credit groups start 0,16,12,8,4 mod20.
# Page2 size15 = last9 of group2 + first6 of group3, not production search output.
CASES = [
    ({}, list(range(20)), 240),
    ({"page": 4}, list(range(60, 80)), 240),
    ({"q": " SYSTEMS ", "block": "major", "requirement_type": "elective",
      "sort": "credits", "page": 2, "page_size": 15},
     [76, 96, 116, 136, 156, 176, 196, 216, 236, 12, 32, 52, 72, 92, 112], 60),
    ({"q": "bridge", "page": 2, "page_size": 5}, [50, 60, 70, 80, 90], 24),
    ({"sort": "name", "page": 3, "page_size": 13}, list(range(26, 39)), 240),
    ({"q": "not-present"}, [], 0),
    ({"page": 99, "page_size": 100}, [], 240),
    ({"block": "general", "requirement_type": "required", "page_size": 100},
     list(range(3, 240, 4)), 60),
    ({"q": "s0007"}, [7], 1),
    # A legacy full-array request remains in the workload, exercising real JSON serialization.
    (None, list(range(239, -1, -1)), 240),
]


def check_response(response, case: int) -> None:
    params, expected_indices, total = CASES[case]
    assert response.status_code == 200, f"status={response.status_code}"
    data = response.json()
    if params is None:
        assert isinstance(data, list), "legacy response must remain an array"
        rows = data
    else:
        assert set(data) == {"program_id", "items", "total", "page", "page_size"}
        assert data["program_id"] == PROGRAM
        assert type(data["total"]) is int and data["total"] == total
        assert type(data["page"]) is int and data["page"] == params.get("page", 1)
        assert type(data["page_size"]) is int and data["page_size"] == params.get("page_size", 20)
        rows = data["items"]
    assert [row["code"] for row in rows] == [f"S{i:04}" for i in expected_indices]
    for row in rows:
        assert type(row["credits"]) is int and isinstance(row["name"], str)
        assert row["source_status"] == "draft_unverified" and row["offering_status"] == "unknown"
