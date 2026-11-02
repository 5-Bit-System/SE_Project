from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import ValidationError

from app.errors import StorageDataError
from app.models import Program
from app.schemas.metadata import CourseMetadata

if TYPE_CHECKING:
    from app.models import Catalog


def validate_curriculum_selections(program: Program, course_codes: set[str]) -> None:
    """Validate catalog structure independently of its storage backend."""
    groups = {group.id for group in program.choice_groups}
    if len(groups) != len(program.choice_groups):
        raise StorageDataError("Nhóm lựa chọn bị trùng")
    tracks = program.track_selection.tracks
    track_ids = {track.id for track in tracks}
    if len(track_ids) != len(tracks):
        raise StorageDataError("Track bị trùng")
    for track in tracks:
        if not set(track.choice_group_ids) <= groups:
            raise StorageDataError("Track chứa nhóm lựa chọn không tồn tại")
    paths = program.graduation_selection.paths
    if len({path.id for path in paths}) != len(paths):
        raise StorageDataError("Nhánh tốt nghiệp bị trùng")
    for path in paths:
        if not set(path.course_codes) <= course_codes:
            raise StorageDataError("Nhánh tốt nghiệp chứa môn không tồn tại")
        if not set(path.allowed_track_ids) <= track_ids:
            raise StorageDataError("Nhánh tốt nghiệp chứa track không tồn tại")


def validate_catalog(catalog: "Catalog", vocabulary: dict | None = None) -> None:
    from app.models import Catalog

    if not isinstance(catalog, Catalog):
        raise StorageDataError("Invalid catalog object")

    strict_metadata = catalog.metadata_schema_version is not None
    if strict_metadata:
        vocabulary = vocabulary if vocabulary is not None else catalog.vocabulary
        if catalog.metadata_schema_version != "1.0" or catalog.vocabulary_version != "1.0":
            raise StorageDataError("Unsupported metadata/vocabulary version")
        if not vocabulary or vocabulary.get("vocabulary_version") != catalog.vocabulary_version:
            raise StorageDataError("Matching vocabulary is required")

    course_codes = [c.code for c in catalog.courses]
    if len(course_codes) != len(set(course_codes)):
        raise StorageDataError("Mã môn trùng trong catalog")

    validate_curriculum_selections(catalog.program, set(course_codes))

    group_ids = {group.id for group in catalog.program.choice_groups}
    path_ids = {path.id for path in catalog.program.graduation_selection.paths}
    course_map = {c.code: c for c in catalog.courses}

    for group in catalog.program.choice_groups:
        declared = getattr(group, "course_codes", None)
        if declared is not None:
            actual = {c.code for c in catalog.courses if group.id in c.choice_group_ids}
            if (
                len(declared) != len(set(declared))
                or not set(declared) <= set(course_map)
                or set(declared) != actual
            ):
                raise StorageDataError(f"Inconsistent choice-group membership: {group.id}")
    if strict_metadata:
        for path in catalog.program.graduation_selection.paths:
            actual = {c.code for c in catalog.courses if path.id in c.graduation_path_ids}
            if set(path.course_codes) != actual:
                raise StorageDataError(f"Inconsistent graduation-path membership: {path.id}")
        for block in getattr(catalog.program, "blocks", []) or []:
            if "course_codes" in block:
                actual = {c.code for c in catalog.courses if c.block == block["id"]}
                if set(block["course_codes"]) != actual:
                    raise StorageDataError(f"Inconsistent block membership: {block['id']}")

    for course in catalog.courses:
        if not set(course.choice_group_ids) <= group_ids:
            raise StorageDataError(f"Môn {course.code} chứa nhóm tự chọn không tồn tại")
        if not set(course.graduation_path_ids) <= path_ids:
            raise StorageDataError(f"Môn {course.code} chứa nhánh tốt nghiệp không tồn tại")

        # Prerequisite validation
        referenced_codes: set[str] = set()
        expressions = [course.prerequisites, *course.prerequisite_variants]
        for clause in (clause for expression in expressions for clause in expression):
            if len(clause) == 0:
                raise StorageDataError(f"Môn {course.code} có nhóm OR rỗng")
            if len(clause) != len(set(clause)):
                raise StorageDataError(f"Môn {course.code} có mã trùng trong nhóm OR: {clause}")
            if course.code in clause:
                raise StorageDataError(f"Môn {course.code} tự tham chiếu chính nó")
            for ref in clause:
                referenced_codes.add(ref)

        actual_external = {code for code in referenced_codes if code not in course_map}
        marked_external = set(course.external_prerequisite_codes)
        if (strict_metadata and actual_external != marked_external) or (
            marked_external and actual_external != marked_external
        ):
            raise StorageDataError(
                f"Môn {course.code} đánh dấu external prerequisite sai: {actual_external} != {marked_external}"
            )

        if strict_metadata:
            try:
                CourseMetadata.model_validate(course.model_dump())
            except ValidationError as exc:
                raise StorageDataError(f"Invalid metadata for {course.code}: {exc}") from None
            for field in ("topics", "career_paths"):
                values = getattr(course, field)
                allowed = vocabulary.get(field)
                if not isinstance(allowed, list) or any(not isinstance(v, str) for v in allowed):
                    raise StorageDataError(f"Vocabulary {field} must be a list of labels")
                if values is not None and (
                    len(values) != len(set(values)) or not set(values) <= set(allowed)
                ):
                    raise StorageDataError(f"Invalid or duplicate {field} in {course.code}")
            enums = vocabulary.get("enums", {})
            if not isinstance(enums, dict):
                raise StorageDataError("Vocabulary enums must be an object")
            for field, allowed in enums.items():
                value = getattr(course, field, None)
                if value is not None and (not isinstance(allowed, list) or value not in allowed):
                    raise StorageDataError(f"Invalid {field} in {course.code}")
    # Prerequisite DAG cycle check
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(code: str) -> None:
        if code in visiting:
            raise StorageDataError(f"Chu trình tiên quyết liên quan đến môn {code}")
        if code in visited:
            return
        visiting.add(code)
        expressions = [course_map[code].prerequisites, *course_map[code].prerequisite_variants]
        for clause in (clause for expression in expressions for clause in expression):
            for ref in clause:
                if ref in course_map:
                    dfs(ref)
        visiting.remove(code)
        visited.add(code)

    for code in course_map:
        dfs(code)
