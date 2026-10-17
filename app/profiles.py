"""Hồ sơ demo tổng hợp và loader từ data/synthetic/profiles.json."""


import json
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.catalog import Catalog, CatalogError, load_catalog
from app.config import get_settings
from app.transcript import (
    PROGRAM_ALIASES,
    StudentTranscript,
    TranscriptRecord,
    resolve_program_id,
)


PROFILES_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "synthetic" / "profiles.json"
)


class DemoProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    profile_id: str
    program_id: str
    label: str
    current_term: int = Field(ge=1, le=12)
    target_track: str | None = None
    career_goal: str = ""
    preferences: dict[str, Any] = Field(default_factory=dict)
    records: list[TranscriptRecord] = Field(default_factory=list)

    @field_validator("profile_id", "label")
    @classmethod
    def require_non_empty_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("profile_id và label không được để trống")
        return cleaned

    @field_validator("program_id")
    @classmethod
    def normalize_program(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("program_id không được để trống")
        return resolve_program_id(cleaned)

    @field_validator("target_track")
    @classmethod
    def normalize_target_track(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    def to_transcript(self) -> StudentTranscript:
        return StudentTranscript(
            program_id=self.program_id,
            records=self.records,
        )


class ProfileError(ValueError):
    pass


def _read_profiles(path: Path | None = None) -> list[DemoProfile]:
    if path is None and get_settings().storage_backend == "postgres":
        from app.infrastructure.repositories import postgres_repository

        return [DemoProfile.model_validate(item) for item in postgres_repository().read_profiles()]
    path = path or PROFILES_PATH
    if not path.exists():
        raise ProfileError(f"Không tìm thấy dữ liệu profile: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProfileError(f"profiles.json không hợp lệ: {exc}") from exc
    if not isinstance(payload, list):
        raise ProfileError("profiles.json phải là một danh sách profile.")
    try:
        profiles = [DemoProfile.model_validate(item) for item in payload]
    except ValidationError as exc:
        raise ProfileError(f"Một profile trong profiles.json không hợp lệ: {exc}") from exc

    profile_ids = [profile.profile_id for profile in profiles]
    duplicate_ids = sorted(
        profile_id for profile_id, count in Counter(profile_ids).items() if count > 1
    )
    if duplicate_ids:
        raise ProfileError(
            "profile_id bị trùng trong profiles.json: " + ", ".join(duplicate_ids)
        )
    return profiles


def _track_matches(profile: DemoProfile, catalog: Catalog) -> bool:
    """Kiểm tra target_track theo ID hoặc tên track trong catalog."""
    if profile.target_track is None:
        return True

    tracks = catalog.program.track_selection.tracks
    if not tracks:
        return False

    requested = profile.target_track.casefold()
    return any(
        requested in {track.id.casefold(), track.name.strip().casefold()}
        for track in tracks
    )


def validate_profile(profile: DemoProfile, catalog: Catalog | None = None) -> None:
    """Kiểm tra profile theo catalog, term, prerequisite và track.

    Profile demo là fixture tái lập được nên mỗi môn chỉ xuất hiện một lần,
    phải có term và không được nằm sau ``current_term``. Prerequisite phải
    được hoàn thành ở một term nhỏ hơn term của môn hiện tại; hoàn thành cùng
    term không được dùng để mở khóa.
    """
    try:
        catalog = catalog or load_catalog(profile.program_id)
    except CatalogError as exc:
        raise ProfileError(
            f"Profile {profile.profile_id} tham chiếu catalog không hợp lệ: {exc}"
        ) from exc

    if profile.program_id != catalog.program.program_id:
        raise ProfileError(
            f"Profile {profile.profile_id} có program_id không khớp catalog."
        )

    isolation = profile.to_transcript().validate_major_isolation(catalog)
    if isolation["foreign_courses"]:
        raise ProfileError(
            f"Profile {profile.profile_id} có môn ngoài ngành: "
            + ", ".join(isolation["foreign_courses"])
        )

    course_map = {course.code: course for course in catalog.courses}
    duplicate_courses = sorted(
        course_code
        for course_code, count in Counter(
            record.course_code for record in profile.records
        ).items()
        if count > 1
    )
    if duplicate_courses:
        raise ProfileError(
            f"Profile {profile.profile_id} có mã môn bị lặp: "
            + ", ".join(duplicate_courses)
        )

    unknown = sorted(set(profile.to_transcript().all_course_codes) - set(course_map))
    if unknown:
        raise ProfileError(
            f"Profile {profile.profile_id} có mã môn ngoài catalog: {', '.join(unknown)}"
        )

    for record in profile.records:
        if record.term is None:
            raise ProfileError(
                f"Profile {profile.profile_id}: {record.course_code} phải có term."
            )
        if record.term > profile.current_term:
            raise ProfileError(
                f"Profile {profile.profile_id}: {record.course_code} ở term "
                f"{record.term}, sau current_term {profile.current_term}."
            )

    if not _track_matches(profile, catalog):
        available = ", ".join(
            f"{track.id} ({track.name})"
            for track in catalog.program.track_selection.tracks
        ) or "catalog không có track chính thức"
        raise ProfileError(
            f"Profile {profile.profile_id} có target_track không hợp lệ: "
            f"{profile.target_track}. Track hợp lệ: {available}"
        )

    for record in sorted(profile.records, key=lambda item: item.term or 0):
        if not record.passed:
            continue
        course = course_map[record.course_code]
        completed_before = {
            previous.course_code
            for previous in profile.records
            if previous.passed
            and previous.term is not None
            and previous.term < record.term
        }
        missing = [
            alternatives
            for alternatives in course.prerequisites
            if alternatives and not any(code in completed_before for code in alternatives)
        ]
        if missing:
            formatted = "; ".join(" hoặc ".join(group) for group in missing)
            raise ProfileError(
                f"Profile {profile.profile_id}: {record.course_code} "
                f"thiếu prerequisite trước đó: {formatted}"
            )


def validate_demo_profiles(path: Path = PROFILES_PATH) -> list[DemoProfile]:
    """Validate fixture chuẩn gồm 12 profile, ba profile cho mỗi ngành."""
    profiles = _read_profiles(path)
    for profile in profiles:
        validate_profile(profile)

    expected_program_ids = set(PROGRAM_ALIASES.values())
    actual_program_ids = {profile.program_id for profile in profiles}
    if actual_program_ids != expected_program_ids:
        missing = sorted(expected_program_ids - actual_program_ids)
        extra = sorted(actual_program_ids - expected_program_ids)
        details = []
        if missing:
            details.append("thiếu ngành: " + ", ".join(missing))
        if extra:
            details.append("ngành ngoài danh sách: " + ", ".join(extra))
        raise ProfileError("Bộ profile demo không đủ bốn ngành (" + "; ".join(details) + ")")

    counts = Counter(profile.program_id for profile in profiles)
    invalid_counts = sorted(
        f"{program_id}={count}"
        for program_id, count in counts.items()
        if count != 3
    )
    if invalid_counts or len(profiles) != 12:
        detail = ", ".join(invalid_counts) or f"tổng số={len(profiles)}"
        raise ProfileError(
            "Bộ profile demo phải có đúng 3 profile cho mỗi ngành và tổng 12 profile: "
            + detail
        )
    return profiles


def list_profiles(
    program_id: str | None = None,
    path: Path | None = None,
) -> list[DemoProfile]:
    profiles = _read_profiles(path)
    if program_id is not None:
        normalized = resolve_program_id(program_id)
        profiles = [profile for profile in profiles if profile.program_id == normalized]
    for profile in profiles:
        validate_profile(profile)
    return profiles


def load_profile(profile_id: str, path: Path | None = None) -> DemoProfile:
    matches = [profile for profile in _read_profiles(path) if profile.profile_id == profile_id]
    if not matches:
        raise ProfileError(f"Không tìm thấy profile: {profile_id}")
    profile = matches[0]
    validate_profile(profile)
    return profile
