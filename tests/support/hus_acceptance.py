"""Optional HUS backend for the existing full catalog acceptance cases.

Expected values come from the PDF inventory/manifest; the source bundle is
always the actual input to the production builder, never the expected output.
"""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from database.hus_db.catalog_builder import build_catalogs

PROJECT = Path(__file__).resolve().parents[2]


def is_hus(root):
    return (root / "hus_pdf_expectations.json").is_file()


def expectations(root):
    document = json.loads((root / "hus_pdf_expectations.json").read_text(encoding="utf8"))
    assert document["format"] == "hus-pdf-acceptance-v1"
    return document


def source_bundle():
    return json.loads((PROJECT / "database/data/hus_source.json").read_text(encoding="utf8"))


def catalog(program_id):
    return next(c for c in build_catalogs(source_bundle()) if c.program.program_id == program_id)


def assert_inventory(root, program_id, bundle=None):
    expected = expectations(root)
    spec = expected["programs"][program_id]
    pdfs = list((root.parents[1]).glob(spec["pdf_number"] + "*.pdf"))
    assert len(pdfs) == 1, "Provide exactly one matching original PDF"
    assert hashlib.sha256(pdfs[0].read_bytes()).hexdigest() == spec["sha256"]
    with (root / expected["inventory"]).open(encoding="utf8", newline="") as file:
        reference = Counter(
            (int(row["pdf_page"]), row["course_code"])
            for row in csv.DictReader(file) if row["decision"] == spec["decision"]
        )
    bundle = source_bundle() if bundle is None else bundle
    curriculum = next(c for c in bundle["tables"]["curricula"]
                      if c["curriculum_version"] == spec["decision"])
    assert curriculum["cohort_year"] == expected["cohort_year"]
    rows = [e for e in bundle["tables"]["official_curriculum_entries"]
            if e["curriculum_id"] == curriculum["curriculum_id"]]
    actual = Counter((e["pdf_page"], e["course_code"]) for e in rows)
    assert actual == reference, {"missing": reference - actual, "extra": actual - reference}
    return rows
