import pytest
from app.catalog import load_catalog, list_catalogs
from app.transcript import (
    TranscriptRecord,
    StudentTranscript,
    resolve_program_id,
    detect_program_from_courses,
)


def test_transcript_record_normalization_and_pass_logic():
    # Tự động viết hoa và loại bỏ khoảng trắng thừa
    rec1 = TranscriptRecord(course_code=" mat1093 ", grade=8.5)
    assert rec1.course_code == "MAT1093"
    assert rec1.passed is True
    assert rec1.grade == 8.5

    # Điểm dưới 5.0 tự động tính là trượt (passed = False)
    rec2 = TranscriptRecord(course_code="mat2501", grade=4.0)
    assert rec2.passed is False

    # Không nhập điểm thì mặc định hoàn thành môn học
    rec3 = TranscriptRecord(course_code="phi1006")
    assert rec3.passed is True
    assert rec3.grade is None

    # Điểm ngoài thang 0-10 bị từ chối
    with pytest.raises(ValueError):
        TranscriptRecord(course_code="MAT1093", grade=10.5)

    with pytest.raises(ValueError):
        TranscriptRecord(course_code="MAT1093", grade=-1.0)


def test_student_transcript_program_resolution_and_properties():
    # Hỗ trợ alias ngắn
    transcript = StudentTranscript(
        program_id="khdl",
        records=[
            TranscriptRecord(course_code="PHI1006", grade=8.0),
            TranscriptRecord(course_code="PEC1008", grade=4.5),  # Trượt
            TranscriptRecord(course_code="MAT2505", grade=9.0),
            TranscriptRecord(course_code="MAT2400"),  # Đạt, không có điểm số cụ thể
        ],
    )
    assert transcript.program_id == "khdl_7460108_2022"
    assert transcript.passed_course_codes == {"PHI1006", "MAT2505", "MAT2400"}
    assert transcript.failed_course_codes == {"PEC1008"}
    assert transcript.grade_map == {"PHI1006": 8.0, "PEC1008": 4.5, "MAT2505": 9.0}


def test_student_transcript_credit_and_gpa_calculation():
    catalog = load_catalog("khdl_7460108_2022")
    # PHI1006: 3 tín chỉ
    # MAT2505: 3 tín chỉ
    # PEC1008: 2 tín chỉ (trượt -> không tính vào earned credits)
    # CME1000: Giáo dục quốc phòng (nằm trong excluded_from_total -> không tính vào tổng tín chỉ tích lũy)
    transcript = StudentTranscript(
        program_id="khdl",
        records=[
            TranscriptRecord(course_code="PHI1006", grade=8.0),
            TranscriptRecord(course_code="MAT2505", grade=10.0),
            TranscriptRecord(course_code="PEC1008", grade=3.0),
            TranscriptRecord(course_code="CME1000", grade=9.0),
        ],
    )

    earned = transcript.calculate_earned_credits(catalog)
    # PHI1006 (3) + MAT2505 (3) = 6 (PEC1008 trượt, CME1000 bị loại trừ khỏi tổng tích lũy)
    assert earned == 6

    # GPA = (8.0 * 3 + 10.0 * 3 + 3.0 * 2) / (3 + 3 + 2) = (24 + 30 + 6) / 8 = 60 / 8 = 7.5
    # (Lưu ý: CME1000 không có trong catalog.courses của KHDL hoặc bị loại trừ)
    gpa = transcript.calculate_gpa(catalog)
    assert gpa is not None
    assert gpa == 7.5


def test_major_isolation_validation():
    catalog = load_catalog("toan_hoc_7460101_2022")
    # Giả sử sinh viên ngành Toán nhưng có mã môn đặc thù của KHDL/KHMT
    transcript = StudentTranscript(
        program_id="toan_hoc",
        records=[
            TranscriptRecord(course_code="PHI1006"),  # Môn chung (có trong Toán)
            TranscriptRecord(course_code="MAT3399"),  # Môn chuyên sâu KHDL (không có trong Toán)
        ],
    )
    isolation_res = transcript.validate_major_isolation(catalog)
    assert "PHI1006" in isolation_res["valid_courses"]
    assert "MAT3399" in isolation_res["foreign_courses"]


def test_load_catalog_supports_all_short_aliases():
    for alias, expected in [
        ("khdl", "khdl_7460108_2022"),
        ("khmtt", "khmtt_7480113qtd_2022"),
        ("toan_hoc", "toan_hoc_7460101_2022"),
        ("toan_tin", "toan_tin_7460117_2022"),
    ]:
        assert resolve_program_id(alias) == expected
        cat = load_catalog(alias)
        assert cat.program.program_id == expected


def test_detect_program_from_courses():
    catalogs = list_catalogs()
    # Danh sách môn đặc thù của KHDL
    khdl_courses = ["MAT3390", "MAT3391", "MAT3392", "MAT3386"]
    rankings = detect_program_from_courses(khdl_courses, catalogs)
    assert len(rankings) == 4
    # Ngành KHDL phải đứng đầu bảng xếp hạng
    assert rankings[0]["program_id"] == "khdl_7460108_2022"
    assert rankings[0]["matched_count"] == 4
    assert rankings[0]["confidence"] == 1.0


def test_transcript_endpoints():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Test POST /transcript/summary
    summary_resp = client.post(
        "/transcript/summary",
        json={
            "program_id": "khdl",
            "records": [
                {"course_code": "PHI1006", "grade": 8.0},
                {"course_code": "MAT2505", "grade": 10.0},
                {"course_code": "PEC1008", "grade": 3.0},
            ],
        },
    )
    assert summary_resp.status_code == 200
    data = summary_resp.json()
    assert data["program_id"] == "khdl_7460108_2022"
    assert data["earned_credits"] == 6
    assert data["gpa"] == 7.5
    assert "PHI1006" in data["passed_courses"]
    assert "PEC1008" in data["failed_courses"]

    # Test POST /transcript/detect-program
    detect_resp = client.post(
        "/transcript/detect-program",
        json={"course_codes": ["MAT3390", "MAT3391", "MAT3392"]},
    )
    assert detect_resp.status_code == 200
    rankings = detect_resp.json()
    assert len(rankings) == 4
    assert rankings[0]["program_id"] == "khdl_7460108_2022"
