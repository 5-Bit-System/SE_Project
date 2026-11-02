"""Compare an independently transcribed PDF code/page inventory to HUS rows."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "docs" / "HUS_PDF_CODE_PAGE_AUDIT.csv"
SOURCE = ROOT / "database" / "data" / "hus_source.json"
DECISIONS = {
    1: "QD3565-2023",
    2: "QD3567-2023",
    3: "QD3568-2023",
    4: "QD3569-2023",
}


def test_pdf_code_page_inventory_matches_hus_export():
    with AUDIT.open(encoding="utf-8", newline="") as file:
        reviewed_rows = list(csv.DictReader(file))
    bundle = json.loads(SOURCE.read_text(encoding="utf-8"))

    expected = Counter(
        (row["decision"], int(row["pdf_page"]), row["course_code"])
        for row in reviewed_rows
    )
    actual = Counter(
        (DECISIONS[row["curriculum_id"]], row["pdf_page"], row["course_code"])
        for row in bundle["tables"]["official_curriculum_entries"]
    )
    assert actual == expected, {
        "missing_from_export": expected - actual,
        "extra_in_export": actual - expected,
    }

    positions = defaultdict(list)
    for row in reviewed_rows:
        assert row["method"] in {"ocr_exact", "visual"}
        positions[row["decision"], int(row["pdf_page"])].append(
            int(row["position_on_page"])
        )
    assert set(decision for decision, _ in positions) == set(DECISIONS.values())
    for page_positions in positions.values():
        assert sorted(page_positions) == list(range(1, len(page_positions) + 1))
