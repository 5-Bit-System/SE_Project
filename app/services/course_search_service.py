"""Deterministic search over one already validated catalog snapshot."""

from app.models import Catalog
from app.schemas.catalog import CourseRequirementType, CourseSearchPage, CourseSort


def search_courses(
    catalog: Catalog, *, q: str = "", block: str | None = None,
    requirement_type: CourseRequirementType | None = None, sort: CourseSort = "code",
    page: int = 1, page_size: int = 20,
) -> CourseSearchPage:
    """Filter, totally order, then page; callers supply API-validated bounds.

    Stability applies to unchanged data, not to requests spanning catalog publications.
    No exceptions are converted into empty results and no source metadata is inferred.
    """
    query = q.strip().casefold()
    selected = [
        course for course in catalog.courses
        if (block is None or course.block == block)
        and (requirement_type is None or course.requirement_type == requirement_type)
        and (not query or query in course.code.casefold() or query in course.name.casefold()
             or query in (course.name_en or "").casefold())
    ]
    if sort == "name":
        ordered = sorted(selected, key=lambda course: (course.name.casefold(), course.code))
    elif sort == "credits":
        ordered = sorted(selected, key=lambda course: (course.credits, course.code))
    else:
        ordered = sorted(selected, key=lambda course: course.code)
    start = (page - 1) * page_size
    return CourseSearchPage(
        program_id=catalog.program.program_id, items=ordered[start:start + page_size],
        total=len(ordered), page=page, page_size=page_size,
    )
