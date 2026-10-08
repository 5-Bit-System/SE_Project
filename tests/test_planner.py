import pytest
from fastapi.testclient import TestClient

from app.catalog import list_catalogs, load_catalog
from app.main import app
from app.planner import (
    allocate_course_years,
    compute_prerequisite_depths,
    generate_roadmap,
)


def test_prerequisite_depths_calculation():
    cat = load_catalog("khdl")
    depths = compute_prerequisite_depths(cat)
    # Môn không có tiên quyết
    assert depths["PHI1006"] == 0
    assert depths["MAT2400"] == 0

    # PEC1008 cần PHI1006 (depth 0) -> depth = 1
    assert depths["PEC1008"] == 1

    # Môn có chuỗi tiên quyết sâu hơn
    for code, d in depths.items():
        assert d >= 0


def test_topological_year_invariant_across_all_four_catalogs():
    """Ràng buộc Topo bất biến: Năm học của môn con không bao giờ nhỏ hơn năm học của môn tiên quyết."""
    catalogs = list_catalogs()
    assert len(catalogs) == 4

    for cat in catalogs:
        allocation = allocate_course_years(cat)
        course_map = {c.code: c for c in cat.courses}

        for c in cat.courses:
            year_c, term_c = allocation[c.code]
            assert 1 <= year_c <= 4
            assert 1 <= term_c <= 8

            # Kiểm tra môn tốt nghiệp luôn ở Năm 4
            if getattr(c, "graduation_path_ids", []):
                assert year_c == 4, f"Môn tốt nghiệp {c.code} phải ở Năm 4"

            # Kiểm tra với các môn tiên quyết nội bộ
            for clause in c.prerequisites:
                valid_clause = [p for p in clause if p in allocation]
                if valid_clause:
                    min_req_year = min(allocation[p][0] for p in valid_clause)
                    assert year_c >= min_req_year, (
                        f"Vi phạm Topo trong {cat.program.program_id}: Môn {c.code} (Năm {year_c}) "
                        f"có tiên quyết {valid_clause} (Năm nhỏ nhất {min_req_year})"
                    )


def test_catalog_courses_have_year_and_term_populated():
    cat = load_catalog("toan_tin")
    for c in cat.courses:
        assert c.year is not None
        assert 1 <= c.year <= 4
        assert c.suggested_term is not None
        assert 1 <= c.suggested_term <= 8


def test_generate_roadmap_with_student_status():
    cat = load_catalog("khdl")
    # Giả sử sinh viên đã hoàn thành 2 môn năm 1
    passed = ["PHI1006", "MAT2505"]
    roadmap = generate_roadmap(cat, passed_course_codes=passed)

    assert roadmap.program_id == "khdl_7460108_2022"
    assert len(roadmap.years) == 4
    assert [y.year_name for y in roadmap.years] == ["Năm 1", "Năm 2", "Năm 3", "Năm 4"]

    # Kiểm tra trạng thái môn đã học: PHI1006 thuộc Năm 1, MAT2505 thuộc Năm 2
    year1_courses = {c.code: c for c in roadmap.years[0].courses}
    year2_courses = {c.code: c for c in roadmap.years[1].courses}
    assert year1_courses["PHI1006"].status == "completed"
    assert year2_courses["MAT2505"].status == "completed"

    # Kiểm tra tiến độ tổng hợp
    progress = roadmap.progress
    assert progress["completed_courses_count"] == 2
    assert progress["completed_credits"] == 6
    assert progress["eligible_courses_count"] > 0
    assert progress["blocked_courses_count"] > 0


def test_roadmap_http_endpoints():
    client = TestClient(app)

    # 1. GET /roadmap
    get_resp = client.get("/roadmap", params={"program_id": "khmtt"})
    assert get_resp.status_code == 200
    data_get = get_resp.json()
    assert data_get["program_id"] == "khmtt_7480113qtd_2022"
    assert len(data_get["years"]) == 4

    # 2. POST /roadmap
    post_resp = client.post(
        "/roadmap",
        json={
            "program_id": "khdl",
            "passed_course_codes": ["PHI1006", "MAT2505"],
        },
    )
    assert post_resp.status_code == 200
    data_post = post_resp.json()
    assert data_post["progress"]["completed_courses_count"] == 2
    assert data_post["progress"]["completed_credits"] == 6
    assert data_post["years"][0]["completed_credits"] == 3
    assert data_post["years"][1]["completed_credits"] == 3
