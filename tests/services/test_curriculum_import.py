"""Unit tests for curriculum import parsing and validation logic."""

import pytest
from app.curriculum.import_service import validate_and_parse_csv, detect_prerequisite_cycles


def test_valid_csv_parsing():
    csv_content = """code,name,credits,prerequisites,block,suggested_term
MAT1001,Giải tích 1,3,,Khối chung,1
MAT1002,Giải tích 2,3,MAT1001,Khối chung,2
PHY1001,Vật lý đại cương,3,,Khối chung,1
"""
    result = validate_and_parse_csv(csv_content, program_id="khdl_test", version_title="K68 2026")
    assert result["valid"] is True
    assert len(result["errors"]) == 0
    assert len(result["courses"]) == 3
    assert result["stats"]["course_count"] == 3
    assert result["stats"]["total_credits"] == 9


def test_duplicate_course_codes():
    csv_content = """code,name,credits,prerequisites
MAT1001,Giải tích 1,3,
MAT1001,Giải tích 1 trùng lặp,3,
"""
    result = validate_and_parse_csv(csv_content, program_id="khdl_test", version_title="K68 Duplicate")
    assert result["valid"] is False
    assert any("Trùng mã học phần: MAT1001" in err["message"] for err in result["errors"])


def test_prerequisite_cycle_detection():
    # A requires B, B requires C, C requires A
    graph = {
        "A": ["B"],
        "B": ["C"],
        "C": ["A"],
        "D": []
    }
    has_cycle, cycle_path = detect_prerequisite_cycles(graph)
    assert has_cycle is True
    assert len(cycle_path) >= 3

    # Direct mutual cycle
    csv_content = """code,name,credits,prerequisites
CS101,Lập trình 1,3,CS102
CS102,Lập trình 2,3,CS101
"""
    result = validate_and_parse_csv(csv_content, program_id="khdl_test", version_title="Cycle Test")
    assert result["valid"] is False
    assert any("Chu trình tiên quyết" in err["message"] for err in result["errors"])


def test_invalid_credits():
    csv_content = """code,name,credits,prerequisites
MAT1001,Toán âm,-2,
MAT1002,Toán quá tải,50,
"""
    result = validate_and_parse_csv(csv_content, program_id="khdl_test", version_title="Credit Test")
    assert result["valid"] is False
    assert len(result["errors"]) >= 2
    assert any("Tín chỉ không hợp lệ" in err["message"] for err in result["errors"])


def test_formula_injection_defense():
    csv_content = """code,name,credits,prerequisites
=cmd|' /C calc'!A0,Lệnh nguy hiểm,3,
+12345,Dấu cộng,3,
"""
    result = validate_and_parse_csv(csv_content, program_id="khdl_test", version_title="Formula injection")
    # All formula characters at cell start must be rejected or escaped
    for course in result["courses"]:
        assert not course["code"].startswith(("=", "+", "@", "-cmd"))
