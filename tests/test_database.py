# pyrefly: ignore [missing-import]
import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    ChoiceGroupModel,
    CourseModel,
    CoursePrerequisiteModel,
    EnrollmentModel,
    ProgramModel,
    RecommendationItemModel,
    RecommendationRunModel,
    StudentModel,
    StudentPreferenceModel,
)
from app.db.session import SessionLocal, check_db_connection, engine


@pytest.fixture(autouse=True)
def check_db_available():
    """Tự động kiểm tra Docker/PostgreSQL trước khi chạy test."""
    if not check_db_connection() or engine is None:
        pytest.skip("Bỏ qua test DB vì Docker/PostgreSQL chưa được bật trên máy này.")


@pytest.fixture
def db_session():
    """Session chạy trong transaction và tự động rollback ở cuối để không làm bẩn dữ liệu seed."""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


def test_database_connection():
    """Kiểm tra kết nối tới cơ sở dữ liệu PostgreSQL."""
    assert check_db_connection() is True


def test_all_tables_exist():
    """1. Kiểm tra sự tồn tại của đủ 9 bảng qua sqlalchemy.inspect."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    expected_tables = {
        "programs",
        "choice_groups",
        "courses",
        "course_prerequisites",
        "students",
        "enrollments",
        "student_preferences",
        "recommendation_runs",
        "recommendation_items",
    }
    assert expected_tables <= existing_tables, f"Thiếu các bảng: {expected_tables - existing_tables}"


def test_seed_counts(db_session):
    """2. Xác minh số lượng bản ghi seed: programs=4, choice_groups=20, courses=290, course_prerequisites=410."""
    prog_count = db_session.scalar(select(func.count()).select_from(ProgramModel))
    assert prog_count == 4

    cg_count = db_session.scalar(select(func.count()).select_from(ChoiceGroupModel))
    assert cg_count == 20

    course_count = db_session.scalar(select(func.count()).select_from(CourseModel))
    assert course_count == 290

    prereq_count = db_session.scalar(select(func.count()).select_from(CoursePrerequisiteModel))
    assert prereq_count == 410


def test_database_seeded_programs(db_session):
    """Kiểm tra dữ liệu chi tiết của 4 CTĐT đã nạp vào DB."""
    stmt = select(ProgramModel)
    programs = list(db_session.scalars(stmt).all())
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


def test_database_seeded_courses(db_session):
    """Kiểm tra môn học cụ thể và khối kiến thức."""
    course_stmt = select(CourseModel).where(
        CourseModel.code == "PHI1006",
        CourseModel.program_id == "khdl_7460108_2022",
    )
    phi_course = db_session.scalars(course_stmt).first()
    assert phi_course is not None
    assert phi_course.credits == 3
    assert phi_course.block == "general"


def test_unique_enrollment(db_session):
    """3. Thêm trùng (student_id, course_code, term) phải raise IntegrityError; khác term thì thành công."""
    student = StudentModel(id="test_std_unique", program_id="khdl_7460108_2022")
    db_session.add(student)
    db_session.flush()

    e1 = EnrollmentModel(student_id="test_std_unique", course_code="MAT1090", term=1)
    db_session.add(e1)
    db_session.flush()

    # Thêm bản ghi trùng lặp kỳ 1 -> Phải ném IntegrityError
    e_dup = EnrollmentModel(student_id="test_std_unique", course_code="MAT1090", term=1)
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(e_dup)
            db_session.flush()

    # Cùng sinh viên và môn nhưng kỳ 2 (học lại / cải thiện) -> Phải thành công
    e2 = EnrollmentModel(student_id="test_std_unique", course_code="MAT1090", term=2)
    db_session.add(e2)
    db_session.flush()
    assert e2.id is not None


def test_fk_recommendation_run_invalid_student(db_session):
    """4. student_id không tồn tại trong students phải raise IntegrityError."""
    invalid_run = RecommendationRunModel(
        id="test_run_invalid_student",
        student_id="student_not_exist_999",
        program_id="khdl_7460108_2022",
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(invalid_run)
            db_session.flush()


def test_fk_recommendation_run_invalid_program(db_session):
    """5. program_id không tồn tại trong programs phải raise IntegrityError."""
    invalid_run = RecommendationRunModel(
        id="test_run_invalid_program",
        student_id=None,
        program_id="program_not_exist_999",
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(invalid_run)
            db_session.flush()


def test_recommendation_run_null_student_ok(db_session):
    """6. student_id=None hợp lệ khi gợi ý cho người dùng vãng lai/demo."""
    guest_run = RecommendationRunModel(
        id="test_run_guest",
        student_id=None,
        program_id="khdl_7460108_2022",
        passed_course_codes=["MAT1090"],
    )
    db_session.add(guest_run)
    db_session.flush()

    queried = db_session.get(RecommendationRunModel, "test_run_guest")
    assert queried is not None
    assert queried.student_id is None
    assert queried.program_id == "khdl_7460108_2022"


def test_student_delete_sets_null(db_session):
    """7. Xóa Student thì recommendation_runs.student_id thành NULL, bản ghi run vẫn tồn tại."""
    student = StudentModel(id="test_std_setnull", program_id="khdl_7460108_2022")
    db_session.add(student)
    db_session.flush()

    run = RecommendationRunModel(
        id="test_run_setnull",
        student_id="test_std_setnull",
        program_id="khdl_7460108_2022",
    )
    db_session.add(run)
    db_session.flush()

    # Xóa sinh viên
    db_session.delete(student)
    db_session.flush()
    db_session.expire_all()

    # Bản ghi run vẫn tồn tại nhưng student_id được set về NULL
    queried_run = db_session.get(RecommendationRunModel, "test_run_setnull")
    assert queried_run is not None
    assert queried_run.student_id is None


def test_program_delete_cascades(db_session):
    """8. Xóa Program tạo riêng cho test thì recommendation_runs liên quan bị xóa theo (CASCADE)."""
    test_prog = ProgramModel(
        id="test_prog_cascade_custom",
        name="Chương trình test xóa cascade",
        total_credits=130,
    )
    db_session.add(test_prog)
    db_session.flush()

    run = RecommendationRunModel(
        id="test_run_prog_cascade",
        student_id=None,
        program_id="test_prog_cascade_custom",
    )
    db_session.add(run)
    db_session.flush()

    # Xóa chương trình test
    db_session.delete(test_prog)
    db_session.flush()
    db_session.expire_all()

    # Bản ghi run phải bị xóa theo
    queried_run = db_session.get(RecommendationRunModel, "test_run_prog_cascade")
    assert queried_run is None


def test_prerequisite_code_has_no_fk(db_session):
    """9. Chèn course_prerequisites với prerequisite_code ngoài danh mục phải THÀNH CÔNG (AGENTS.md)."""
    phi_course = db_session.scalars(
        select(CourseModel).where(CourseModel.code == "PHI1006", CourseModel.program_id == "khdl_7460108_2022")
    ).first()
    assert phi_course is not None

    external_prereq = CoursePrerequisiteModel(
        course_id=phi_course.id,
        course_code="PHI1006",
        program_id="khdl_7460108_2022",
        prerequisite_code="EXTERNAL_UNKNOWN_COURSE_999",
        clause_index=0,
        is_verified=False,
    )
    db_session.add(external_prereq)
    db_session.flush()
    assert external_prereq.id is not None


def test_crud_student_enrollment_recommendation(db_session):
    """10. CRUD mẫu cho StudentModel, EnrollmentModel, RecommendationRunModel."""
    # CREATE
    student = StudentModel(
        id="test_std_crud",
        program_id="khdl_7460108_2022",
        current_term=3,
        gpa_10=8.0,
        target_track="AI Engineer",
    )
    pref = StudentPreferenceModel(student_id="test_std_crud", weight_goal=2.0)
    enrollment = EnrollmentModel(
        student_id="test_std_crud",
        course_code="MAT1090",
        grade=8.5,
        status="passed",
        term=1,
    )
    run = RecommendationRunModel(
        id="test_run_crud",
        student_id="test_std_crud",
        program_id="khdl_7460108_2022",
        passed_course_codes=["MAT1090"],
        whatif_weights={"goal": 2.0},
    )
    item = RecommendationItemModel(
        run_id="test_run_crud",
        course_code="INT2015",
        rank=1,
        score=0.95,
        reason="Đủ điều kiện tiên quyết",
    )

    db_session.add_all([student, pref, enrollment, run, item])
    db_session.flush()

    # READ
    db_session.expire_all()
    s = db_session.get(StudentModel, "test_std_crud")
    assert s is not None
    assert s.target_track == "AI Engineer"
    assert s.preference is not None
    assert s.preference.weight_goal == 2.0
    assert len(s.enrollments) == 1
    assert s.enrollments[0].course_code == "MAT1090"

    r = db_session.get(RecommendationRunModel, "test_run_crud")
    assert r is not None
    assert len(r.items) == 1
    assert r.items[0].course_code == "INT2015"

    # UPDATE
    s.gpa_10 = 8.8
    s.enrollments[0].grade = 9.0
    r.items[0].score = 0.98
    db_session.flush()

    db_session.expire_all()
    updated_s = db_session.get(StudentModel, "test_std_crud")
    assert updated_s is not None
    assert updated_s.gpa_10 == 8.8
    assert updated_s.enrollments[0].grade == 9.0
    updated_r = db_session.get(RecommendationRunModel, "test_run_crud")
    assert updated_r is not None
    assert updated_r.items[0].score == 0.98

    # DELETE
    db_session.delete(updated_r)
    db_session.delete(updated_s)
    db_session.flush()

    db_session.expire_all()
    assert db_session.get(RecommendationRunModel, "test_run_crud") is None
    assert db_session.get(StudentModel, "test_std_crud") is None
