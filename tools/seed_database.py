"""Seed script: Import 4 curriculum catalogs from JSON to PostgreSQL.

Usage:
    python tools/seed_database.py
"""

import json
import logging
from pathlib import Path
import sys

# Ensure repository root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import (
    ChoiceGroupModel,
    CourseModel,
    CoursePrerequisiteModel,
    ProgramModel,
)
from app.db.session import SessionLocal, check_db_connection, init_db
from app.models import Catalog, Course, Program
from app.planner import allocate_course_years

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_ROOT = ROOT / "data" / "curricula"


def seed_database() -> None:
    if not check_db_connection():
        logger.error("Không thể kết nối đến PostgreSQL! Hãy kiểm tra Docker container.")
        sys.exit(1)

    logger.info("Khởi tạo cấu trúc bảng trong PostgreSQL (init_db)...")
    init_db()

    session = SessionLocal()
    try:
        curriculum_dirs = sorted([d for d in DATA_ROOT.iterdir() if d.is_dir()])
        total_programs = 0
        total_choice_groups = 0
        total_courses = 0
        total_prereqs = 0

        for cur_dir in curriculum_dirs:
            curriculum_file = cur_dir / "curriculum.json"
            courses_file = cur_dir / "courses.json"

            if not curriculum_file.exists() or not courses_file.exists():
                logger.warning("Bỏ qua thư mục thiếu file: %s", cur_dir.name)
                continue

            cur_data = json.loads(curriculum_file.read_text(encoding="utf-8"))
            courses_data = json.loads(courses_file.read_text(encoding="utf-8"))

            program_id = cur_data["program_id"]
            logger.info("Đang xử lý ngành: %s (%s)...", program_id, cur_data.get("name"))

            # 1. Upsert Program
            program_obj = session.query(ProgramModel).filter_by(id=program_id).first()
            if not program_obj:
                program_obj = ProgramModel(
                    id=program_id,
                    name=cur_data.get("name", program_id),
                    total_credits=cur_data.get("total_credits", 130),
                    catalog_status=cur_data.get("catalog_status", "draft_unverified"),
                    source_file=cur_data.get("source_file"),
                    source_pages=cur_data.get("source_pages"),
                    notes=cur_data.get("notes", []),
                )
                session.add(program_obj)
            else:
                program_obj.name = cur_data.get("name", program_id)
                program_obj.total_credits = cur_data.get("total_credits", 130)
                program_obj.catalog_status = cur_data.get("catalog_status", "draft_unverified")
                program_obj.source_file = cur_data.get("source_file")
                program_obj.source_pages = cur_data.get("source_pages")
                program_obj.notes = cur_data.get("notes", [])

            session.flush()
            total_programs += 1

            # 2. Upsert Choice Groups
            for cg in cur_data.get("choice_groups", []):
                cg_id = cg["id"]
                cg_obj = (
                    session.query(ChoiceGroupModel)
                    .filter_by(id=cg_id, program_id=program_id)
                    .first()
                )
                if not cg_obj:
                    cg_obj = ChoiceGroupModel(
                        id=cg_id,
                        program_id=program_id,
                        name=cg.get("name", cg_id),
                        required_credits=cg.get("required_credits", 0),
                    )
                    session.add(cg_obj)
                else:
                    cg_obj.name = cg.get("name", cg_id)
                    cg_obj.required_credits = cg.get("required_credits", 0)
                total_choice_groups += 1

            session.flush()

            # 3. Tính toán năm học đề xuất bằng Topo Planner
            temp_pydantic_program = Program.model_validate(cur_data)
            temp_pydantic_courses = [Course.model_validate(c) for c in courses_data]
            temp_catalog = Catalog(program=temp_pydantic_program, courses=temp_pydantic_courses)
            allocation = allocate_course_years(temp_catalog)

            # 4. Upsert Courses và Prerequisite Edges
            for c_dict in courses_data:
                code = c_dict["code"]
                course_obj = (
                    session.query(CourseModel)
                    .filter_by(code=code, program_id=program_id)
                    .first()
                )

                alloc_year, alloc_term = allocation.get(code, (1, 1))
                prereqs = c_dict.get("prerequisites", [])

                if not course_obj:
                    course_obj = CourseModel(
                        code=code,
                        program_id=program_id,
                        name=c_dict.get("name", ""),
                        credits=c_dict.get("credits", 3),
                        block=c_dict.get("block", "general"),
                        prerequisites=prereqs,
                        choice_group_ids=c_dict.get("choice_group_ids", []),
                        source_page=c_dict.get("source_page"),
                        year=alloc_year,
                        suggested_term=alloc_term,
                    )
                    session.add(course_obj)
                else:
                    course_obj.name = c_dict.get("name", "")
                    course_obj.credits = c_dict.get("credits", 3)
                    course_obj.block = c_dict.get("block", "general")
                    course_obj.prerequisites = prereqs
                    course_obj.choice_group_ids = c_dict.get("choice_group_ids", [])
                    course_obj.source_page = c_dict.get("source_page")
                    course_obj.year = alloc_year
                    course_obj.suggested_term = alloc_term

                session.flush()
                total_courses += 1

                # Xóa các cạnh cũ của môn này để tạo mới
                session.query(CoursePrerequisiteModel).filter_by(
                    course_id=course_obj.id
                ).delete()

                # Thêm các cạnh tiên quyết
                # prereqs dạng [[A, B], [C]] -> AND clauses
                for clause_idx, or_group in enumerate(prereqs):
                    for prereq_code in or_group:
                        edge = CoursePrerequisiteModel(
                            course_id=course_obj.id,
                            course_code=code,
                            program_id=program_id,
                            prerequisite_code=prereq_code,
                            clause_index=clause_idx,
                            is_verified=True,
                        )
                        session.add(edge)
                        total_prereqs += 1

        session.commit()
        logger.info("==================================================")
        logger.info("SEED DỮ LIỆU POSTGRESQL HOÀN TẤT THÀNH CÔNG!")
        logger.info("  - Tổng số Ngành (Programs): %d", total_programs)
        logger.info("  - Tổng số Nhóm tự chọn (Choice Groups): %d", total_choice_groups)
        logger.info("  - Tổng số Môn học (Courses): %d", total_courses)
        logger.info("  - Tổng số Cạnh tiên quyết (Prerequisites): %d", total_prereqs)
        logger.info("==================================================")

    except Exception as exc:
        session.rollback()
        logger.exception("Lỗi khi seed dữ liệu: %s", exc)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
