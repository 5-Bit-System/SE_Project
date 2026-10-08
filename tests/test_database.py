# pyrefly: ignore [missing-import]
import pytest
from sqlalchemy import select

from app.db.models import CourseModel, ProgramModel
from app.db.session import SessionLocal, check_db_connection


@pytest.fixture(autouse=True)
def check_db_available():
    """Tự động kiểm tra Docker/PostgreSQL trước khi chạy test."""
    if not check_db_connection():
        pytest.skip("Bỏ qua test DB vì Docker/PostgreSQL chưa được bật trên máy này.")


def test_database_connection():
    """Kiểm tra kết nối tới cơ sở dữ liệu PostgreSQL."""
    assert check_db_connection() is True


def test_database_seeded_programs():
    """Kiểm tra dữ liệu 4 chương trình đào tạo đã được nạp vào DB."""
    with SessionLocal() as session:
        stmt = select(ProgramModel)
        programs = list(session.scalars(stmt).all())
        program_ids = {p.id for p in programs}
        expected = {
            "toan_hoc_7460101_2022",
            "toan_tin_7460117_2022",
            "khmtt_7480113qtd_2022",
            "khdl_7460108_2022",
        }
        assert expected <= program_ids
        for p in programs:
            assert p.total_credits >= 120


def test_database_seeded_courses():
    """Kiểm tra môn học và điều kiện tiên quyết trong DB."""
    with SessionLocal() as session:
        # Ngành KHDL phải có ít nhất 60 môn
        stmt = select(CourseModel).where(CourseModel.program_id == "khdl_7460108_2022")
        ds_courses = list(session.scalars(stmt).all())
        assert len(ds_courses) >= 60

        # Kiểm tra môn cụ thể
        course_stmt = select(CourseModel).where(
            CourseModel.code == "PHI1006",
            CourseModel.program_id == "khdl_7460108_2022",
        )
        phi_course = session.scalars(course_stmt).first()
        assert phi_course is not None
        assert phi_course.credits == 3
        assert phi_course.block == "general"
