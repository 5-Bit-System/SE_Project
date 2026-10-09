import json
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from app.models import Catalog, Course, Program


DATA_ROOT = Path(__file__).resolve().parent.parent / "data" / "curricula"
COURSES_ADAPTER = TypeAdapter(list[Course])


class CatalogError(ValueError):
    pass


class CatalogNotFoundError(CatalogError):
    pass


def _catalog_directories(root: Path) -> dict[str, Path]:
    try:
        resolved_root = root.resolve()
        return {
            path.name: path
            for path in sorted(root.iterdir())
            if path.is_dir() and path.resolve().parent == resolved_root
        }
    except OSError as exc:
        raise CatalogError(f"Không thể đọc thư mục catalog {root}: {exc}") from exc


def _read_json(path: Path) -> object:
    try:
        contents = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise CatalogError(f"Thiếu file catalog: {path}") from exc
    except UnicodeDecodeError as exc:
        raise CatalogError(f"File catalog không phải UTF-8 hợp lệ: {path}") from exc
    except OSError as exc:
        raise CatalogError(f"Không thể đọc file catalog {path}: {exc}") from exc
    try:
        return json.loads(contents)
    except json.JSONDecodeError as exc:
        raise CatalogError(
            f"JSON không hợp lệ trong {path}, dòng {exc.lineno}, cột {exc.colno}: {exc.msg}"
        ) from exc


def list_catalogs(root: Path = DATA_ROOT) -> list[Catalog]:
    return [load_catalog(program_id, root) for program_id in _catalog_directories(root)]


def load_catalog(program_id: str, root: Path = DATA_ROOT) -> Catalog:
    # The ID is checked against actual directories, never used as a free-form path.
    allowed = _catalog_directories(root)
    if program_id not in allowed:
        raise CatalogNotFoundError(f"Không tìm thấy chương trình: {program_id}")
    directory = allowed[program_id]
    program_path = directory / "curriculum.json"
    courses_path = directory / "courses.json"
    program_data = _read_json(program_path)
    try:
        program = Program.model_validate(program_data)
    except ValidationError as exc:
        raise CatalogError(f"Dữ liệu không hợp lệ trong {program_path}: {exc}") from exc
    courses_data = _read_json(courses_path)
    try:
        courses = COURSES_ADAPTER.validate_python(courses_data)
    except ValidationError as exc:
        raise CatalogError(f"Dữ liệu không hợp lệ trong {courses_path}: {exc}") from exc
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
