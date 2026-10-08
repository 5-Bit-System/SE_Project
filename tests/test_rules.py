import pytest
from fastapi.testclient import TestClient

from app.catalog import load_catalog
from app.main import app
from app.models import Catalog, ChoiceGroup, Course, Program
from app.rules import evaluate_eligibility, eligible_courses


def sample_catalog() -> Catalog:
    return Catalog(
        program=Program(
            program_id="demo",
            name="CTĐT thử nghiệm cho Rule Engine",
            total_credits=20,
            catalog_status="draft_unverified",
            source_file="synthetic",
            source_pages="none",
            choice_groups=[ChoiceGroup(id="elective_group", name="Nhóm Tự chọn 1", required_credits=3)],
        ),
        courses=[
            Course(code="A", name="Nhập môn A", credits=3, block="general"),
            Course(code="B", name="Cơ sở B", credits=3, block="group", prerequisites=[["A"]]),
            Course(code="C", name="Môn C (A hoặc B)", credits=3, block="group", prerequisites=[["A", "B"]]),
            Course(code="D", name="Môn D (A và B)", credits=4, block="major", prerequisites=[["A"], ["B"]]),
            Course(code="E1", name="Tự chọn E1", credits=3, block="major", choice_group_ids=["elective_group"]),
            Course(code="E2", name="Tự chọn E2", credits=3, block="major", choice_group_ids=["elective_group"]),
            Course(code="CONFLICT", name="Môn xung đột nguồn", credits=3, block="major", prerequisite_status="source_conflict"),
        ],
    )


def test_rule_engine_basic_prerequisites_and_blocked_reasons():
    cat = sample_catalog()

    # Chưa học môn nào
    res0 = evaluate_eligibility(cat, passed_codes=set(), max_credits=30)
    # A, E1, E2 không có tiên quyết -> eligible
    eligible_codes_0 = {c.code for c in res0.eligible_courses}
    assert eligible_codes_0 == {"A", "E1", "E2"}

    # Bị chặn: B (thiếu A), C (thiếu A hoặc B), D (thiếu A, B), CONFLICT (xung đột)
    blocked_dict = {b.code: b for b in res0.blocked_courses}
    assert "B" in blocked_dict
    assert any(r.kind == "missing_prerequisites" for r in blocked_dict["B"].reasons)
    assert blocked_dict["B"].reasons[0].missing_prerequisites == [["A"]]

    assert "C" in blocked_dict
    assert any(r.kind == "missing_prerequisites" for r in blocked_dict["C"].reasons)
    assert blocked_dict["C"].reasons[0].missing_prerequisites == [["A", "B"]]

    assert "CONFLICT" in blocked_dict
    assert any(r.kind == "source_conflict" for r in blocked_dict["CONFLICT"].reasons)


def test_rule_engine_or_and_clauses_and_choice_quota():
    cat = sample_catalog()

    # Đã hoàn thành A
    res_a = evaluate_eligibility(cat, passed_codes={"A"}, max_credits=30)
    assert "A" in res_a.completed_course_codes
    eligible_a = {c.code for c in res_a.eligible_courses}
    # B (cần A -> đủ), C (cần A hoặc B -> đủ), E1, E2 -> eligible
    # D (cần cả A và B -> vẫn thiếu B)
    assert eligible_a == {"B", "C", "E1", "E2"}

    blocked_d = next(b for b in res_a.blocked_courses if b.code == "D")
    assert blocked_d.reasons[0].missing_prerequisites == [["B"]]

    # Đã hoàn thành A và E1 (nhóm elective_group yêu cầu 3 TC, E1 có 3 TC -> đủ quota)
    res_quota = evaluate_eligibility(cat, passed_codes={"A", "E1"}, max_credits=30)
    # E2 cùng nhóm elective_group -> bị chặn do choice_group_full
    assert not any(c.code == "E2" for c in res_quota.eligible_courses)
    blocked_e2 = next(b for b in res_quota.blocked_courses if b.code == "E2")
    assert any(r.kind == "choice_group_full" for r in blocked_e2.reasons)


def test_rule_engine_max_credits_constraint():
    cat = sample_catalog()
    # Khi đã qua cả A và B, D (4 tín chỉ) đủ điều kiện nếu max_credits >= 4
    res_ok = evaluate_eligibility(cat, passed_codes={"A", "B"}, max_credits=4)
    assert any(c.code == "D" for c in res_ok.eligible_courses)

    # Nếu max_credits = 3 thì D (4 tín chỉ) bị chặn
    res_limit = evaluate_eligibility(cat, passed_codes={"A", "B"}, max_credits=3)
    assert not any(c.code == "D" for c in res_limit.eligible_courses)
    blocked_d = next(b for b in res_limit.blocked_courses if b.code == "D")
    assert any(r.kind == "credits_exceeded" for r in blocked_d.reasons)


def test_zero_eligibility_violation_rate_on_real_catalog():
    # Kiểm tra tính toàn vẹn luật trên CTĐT thực tế Khoa học Dữ liệu (KHDL)
    cat = load_catalog("khdl")
    passed = {"PHI1006", "PEC1008", "MAT2505", "MAT2400"}
    res = evaluate_eligibility(cat, passed_codes=passed, max_credits=30)

    # 1. Không môn nào trong eligible đã nằm trong passed
    eligible_codes = {c.code for c in res.eligible_courses}
    assert not (eligible_codes & passed)

    # 2. Toàn bộ môn trong eligible phải thỏa mãn 100% điều kiện tiên quyết
    for course in res.eligible_courses:
        for alternatives in course.prerequisites:
            assert any(alt in passed for alt in alternatives), (
                f"Môn {course.code} bị lọt vào eligible dù thiếu tiên quyết {alternatives}"
            )

    # 3. Môn bị chặn do thiếu tiên quyết phải có danh sách missing cụ thể
    for blocked in res.blocked_courses:
        for r in blocked.reasons:
            if r.kind == "missing_prerequisites":
                assert len(r.missing_prerequisites) > 0


def test_eligibility_http_endpoint():
    client = TestClient(app)
    resp = client.post(
        "/eligibility",
        json={
            "program_id": "khdl",
            "passed_course_codes": ["PHI1006", "MAT2505"],
            "max_credits": 25,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["program_id"] == "khdl_7460108_2022"
    assert data["total_eligible"] > 0
    assert data["total_blocked"] > 0
    assert "PHI1006" in data["completed_course_codes"]
    assert "MAT2505" in data["completed_course_codes"]
    # Kiểm tra định dạng cấu trúc blocked_courses
    sample_blocked = data["blocked_courses"][0]
    assert "code" in sample_blocked
    assert "reasons" in sample_blocked
    assert len(sample_blocked["reasons"]) > 0
