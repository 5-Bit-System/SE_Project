"""Purpose-built invented catalog and literal test oracle; no university/student data."""

from app.models import Catalog, Course, Program

INPUT_CODES = ["C04", "C02", "C08", "C05", "C01", "C07", "C03", "C06"]
CODE_ORDER = ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08"]
CREDIT_ORDER = ["C06", "C05", "C01", "C02", "C04", "C08", "C03", "C07"]
NAME_ORDER = ["C01", "C03", "C02", "C04", "C05", "C08", "C07", "C06"]


def search_catalog() -> Catalog:
    rows = [
        ("C01", "Calculus", None, 3, "general", "required"),
        ("C02", "Data Systems", "Data Systems", 3, "major", "elective"),
        ("C03", "Data Basics", "Data Foundations", 4, "major", "required"),
        ("C04", "data systems", "DATA SYSTEMS", 3, "major", "elective"),
        ("C05", "Logic", None, 2, "general", "required"),
        ("C06", "Éthique", "Ethics", 1, "general", "required_excluded"),
        ("C07", "Thesis", None, 6, "major", "graduation"),
        ("C08", "Special % Lab", "Special Percent Lab", 3, "major", "elective"),
    ]
    by_code = {
        code: Course(code=code, name=name, name_en=en, credits=credits, block=block,
                     requirement_type=kind, counted_in_total=kind != "required_excluded",
                     hours={"lecture": 0, "practice": None},
                     test_provenance={"kind": "invented"})
        for code, name, en, credits, block, kind in rows
    }
    return Catalog(program=Program(
        program_id="bt3_synthetic", name="Invented BT3", total_credits=25,
        source_file="synthetic", source_pages="none", catalog_revision="test-v1"),
        courses=[by_code[code] for code in INPUT_CODES])
