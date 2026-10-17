import json
from pathlib import Path

from pydantic import ValidationError

from app.catalog_normalization import normalize_catalog
from app.catalog_validation import validate_curriculum_selections
from app.errors import CatalogError, StorageDataError
from app.models import Catalog
from app.transcript import resolve_program_id

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "curricula"


def list_catalogs(root: Path = DATA_ROOT) -> list[Catalog]:
    try:
        ids = sorted(path.name for path in root.iterdir() if path.is_dir())
    except OSError:
        raise StorageDataError("Không thể đọc thư mục catalog nguồn") from None
    return [load_catalog(program_id, root) for program_id in ids]


def load_catalog(program_id: str, root: Path = DATA_ROOT) -> Catalog:
    resolved_id = resolve_program_id(program_id)
    try:
        allowed = {path.name for path in root.iterdir() if path.is_dir()}
        if resolved_id not in allowed:
            raise CatalogError(f"Không tìm thấy chương trình: {program_id}")
        directory = root / resolved_id
        program_doc = json.loads((directory / "curriculum.json").read_text(encoding="utf-8"))
        course_doc = json.loads((directory / "courses.json").read_text(encoding="utf-8"))
        vocab_path = directory / "vocabulary.json"
        vocab_doc = (
            json.loads(vocab_path.read_text(encoding="utf-8")) if vocab_path.exists() else None
        )
    except CatalogError:
        raise
    except (OSError, json.JSONDecodeError, ValidationError):
        raise StorageDataError("Dữ liệu catalog nguồn không hợp lệ") from None

    catalog = normalize_catalog(program_doc, course_doc, vocab_doc)
    program = catalog.program
    courses = catalog.courses

    validate_curriculum_selections(program, {course.code for course in courses})
    if program.program_id != resolved_id:
        raise StorageDataError("program_id không khớp thư mục catalog")
    codes = [course.code for course in courses]
    if len(codes) != len(set(codes)):
        raise StorageDataError("Mã môn trùng trong catalog nguồn")
    group_ids = {group.id for group in program.choice_groups}
    if any(not set(course.choice_group_ids) <= group_ids for course in courses):
        raise StorageDataError("Nhóm tự chọn không tồn tại trong catalog")
    return catalog
