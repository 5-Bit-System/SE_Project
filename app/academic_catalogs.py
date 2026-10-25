"""Academic catalog access without publishing reference-only curricula to HUS."""

from app.catalog import list_catalogs, load_catalog
from app.catalog_validation import validate_catalog
from app.curriculum_reference import reference
from app.models import Catalog, Course, Program

TALENT_PROGRAM_ID = "toan_hoc_tai_nang_7460101_2022"


def talented_catalog() -> Catalog:
    ref = reference(TALENT_PROGRAM_ID)
    choice_groups = []
    for group in ref["planning_groups"]:
        codes = [course["code"] for course in ref["courses"] if group["id"] in course["group_ids"]]
        choice_groups.append({"id": group["id"], "name": group["name"],
                              "required_credits": group["required_credits"], "course_codes": codes})
    group_ids = {group["id"] for group in choice_groups}
    courses = [Course(**{key: value for key, value in course.items() if key != "group_ids"},
                      block=course["group_ids"][0],
                      choice_group_ids=[key for key in course["group_ids"] if key in group_ids],
                      graduation_path_ids=["thesis"] if course["code"] == "MAT4074" else [])
               for course in ref["courses"]]
    program = Program(program_id=TALENT_PROGRAM_ID, name=ref["name"], total_credits=168,
        source_file=ref["source_file"], source_pages="8–14", choice_groups=choice_groups,
        graduation_selection={"mode": "exactly_one_path", "required_credits": 10,
                              "paths": [{"id": "thesis", "name": "Khóa luận tốt nghiệp",
                                         "course_codes": ["MAT4074"]}]},
        planning_blockers=["source_track_rules_unresolved"], source_issues=ref["issues"])
    value = Catalog(program=program, courses=courses)
    validate_catalog(value)
    return value


def load_academic_catalog(program_id: str) -> Catalog:
    return talented_catalog() if program_id == TALENT_PROGRAM_ID else load_catalog(program_id)


def list_academic_catalogs() -> list[Catalog]:
    return [*list_catalogs(), talented_catalog()]
