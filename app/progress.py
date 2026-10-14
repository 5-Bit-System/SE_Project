"""Advisory curriculum progress from the selected catalog's own rules."""

from pydantic import BaseModel, Field

from app.models import Catalog, Course
from app.rules import _prepare_selection_context, _validate_passed_codes


class ProgressItem(BaseModel):
    id: str
    name: str
    earned_credits: int = Field(ge=0)
    required_credits: int | None = Field(default=None, ge=0)
    remaining_credits: int | None = Field(default=None, ge=0)


class CurriculumProgress(BaseModel):
    program_id: str
    total: ProgressItem
    blocks: list[ProgressItem] = Field(default_factory=list)
    choice_groups: list[ProgressItem] = Field(default_factory=list)
    track: ProgressItem | None = None
    graduation_path: ProgressItem | None = None
    selected_track_id: str | None = None
    selected_graduation_path_id: str | None = None
    warnings: list[str] = Field(default_factory=list)


def counts_toward_total(catalog: Catalog, course: Course) -> bool:
    """Share exclusion semantics between earned credits, GPA and progress."""
    excluded = getattr(catalog.program, "excluded_from_total", [])
    return (
        course.code not in (excluded if isinstance(excluded, list) else [])
        and getattr(course, "counted_in_total", True) is not False
    )


def calculate_progress(
    catalog: Catalog,
    passed_codes: set[str],
    selected_track_id: str | None = None,
    selected_graduation_path_id: str | None = None,
) -> CurriculumProgress:
    """Count unique passed courses; group memberships can overlap.

    Missing targets remain unknown and unselected tracks/paths stay unset.
    These credit totals are advisory, never a graduation eligibility decision.
    """
    course_map = {course.code: course for course in catalog.courses}
    passed = _validate_passed_codes(passed_codes, set(course_map))
    (_, selected_track, selected_track_groups, _, _, selected_path, _, _) = (
        _prepare_selection_context(catalog, selected_track_id, selected_graduation_path_id)
    )
    counted = {code for code in passed if counts_toward_total(catalog, course_map[code])}

    def item(identifier: str, name: str, codes: set[str], required: int | None) -> ProgressItem:
        earned = sum(course_map[code].credits for code in counted & codes)
        return ProgressItem(
            id=identifier,
            name=name,
            earned_credits=earned,
            required_credits=required,
            remaining_credits=None if required is None else max(0, required - earned),
        )

    blocks = []
    for block in getattr(catalog.program, "blocks", []) or []:
        values = block if isinstance(block, dict) else block.model_dump()
        block_id = values["id"]
        codes = values.get("course_codes")
        if codes is None:
            codes = [c.code for c in catalog.courses if c.block == block_id]
        blocks.append(
            item(block_id, values.get("name", block_id), set(codes), values.get("required_credits"))
        )

    group_codes = {
        group.id: {c.code for c in catalog.courses if group.id in c.choice_group_ids}
        for group in catalog.program.choice_groups
    }
    groups = [
        item(group.id, group.name, group_codes[group.id], group.required_credits)
        for group in catalog.program.choice_groups
    ]
    track = None
    if selected_track:
        track_codes = {code for group_id in selected_track_groups for code in group_codes[group_id]}
        required = sum(
            g.required_credits
            for g in catalog.program.choice_groups
            if g.id in selected_track_groups
        )
        track = item(selected_track.id, selected_track.name, track_codes, required)
    path = None
    if selected_path:
        path = item(
            selected_path.id,
            selected_path.name,
            set(selected_path.course_codes),
            catalog.program.graduation_selection.required_credits,
        )
    warnings = ["Credit progress is advisory; it does not confirm graduation eligibility."]
    if catalog.program.catalog_status != "verified":
        warnings.append("Curriculum is draft_unverified; official rules require review.")
    if catalog.program.track_selection.mode == "exactly_one_track" and not selected_track:
        warnings.append("No track selected; track progress is unknown.")
    if catalog.program.graduation_selection.mode == "exactly_one_path" and not selected_path:
        warnings.append("No graduation path selected; path progress is unknown.")
    return CurriculumProgress(
        program_id=catalog.program.program_id,
        total=item("total", catalog.program.name, set(course_map), catalog.program.total_credits),
        blocks=blocks,
        choice_groups=groups,
        track=track,
        graduation_path=path,
        selected_track_id=selected_track_id,
        selected_graduation_path_id=selected_graduation_path_id,
        warnings=warnings,
    )
