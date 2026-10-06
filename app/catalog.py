import json
from pathlib import Path

from app.models import Catalog, Course, Program


DATA_ROOT = Path(__file__).resolve().parent.parent / "data" / "curricula"


class CatalogError(ValueError):
    pass


def list_catalogs(root: Path = DATA_ROOT) -> list[Catalog]:
    return [load_catalog(path.name, root) for path in sorted(root.iterdir()) if path.is_dir()]


def load_catalog(program_id: str, root: Path = DATA_ROOT) -> Catalog:
    # The ID is checked against actual directories, never used as a free-form path.
    allowed = {path.name for path in root.iterdir() if path.is_dir()}
    if program_id not in allowed:
        raise CatalogError(f"Không tìm thấy chương trình: {program_id}")
    directory = root / program_id
    program = Program.model_validate(json.loads((directory / "curriculum.json").read_text(encoding="utf-8")))
    courses = [Course.model_validate(item) for item in json.loads((directory / "courses.json").read_text(encoding="utf-8"))]
    if program.program_id != program_id:
        raise CatalogError(f"program_id không khớp trong {directory}")
    codes = [course.code for course in courses]
    if len(codes) != len(set(codes)):
        raise CatalogError(f"Mã môn trùng trong {program_id}")
    group_ids = {group.id for group in program.choice_groups}
    for course in courses:
        if not set(course.choice_group_ids) <= group_ids:
            raise CatalogError(f"Nhóm tự chọn không tồn tại: {course.code}")
    return Catalog(program=program, courses=courses)
