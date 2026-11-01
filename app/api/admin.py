"""Admin console API endpoints with strict role-based authorization."""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.auth.dependencies import require_account
from app.catalog import CatalogError, list_catalogs, load_catalog
from app.services.admin_overview import AdminOverviewResponse, get_admin_overview


class AdminProgramSummary(BaseModel):
    program_id: str
    name: str
    total_credits: int
    course_count: int
    catalog_status: str
    catalog_revision: str | None = None
    cohort: str | None = None
    source_file: str
    source_pages: str
    notes: list[str] = Field(default_factory=list)


class AdminCourseItem(BaseModel):
    code: str
    name: str
    name_en: str | None = None
    credits: int
    block: str
    requirement_type: str
    prerequisites: list[list[str]] = Field(default_factory=list)
    prerequisites_raw: str | None = None
    prerequisite_status: str
    suggested_term: int | None = None
    year: int | None = None
    source_status: str
    source_page: int | None = None


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverviewResponse)
async def overview(request: Request) -> AdminOverviewResponse:
    """Return truthful overview metrics for administrators only."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")
    return await get_admin_overview()


@router.get("/programs", response_model=list[AdminProgramSummary])
async def list_admin_programs(request: Request) -> list[AdminProgramSummary]:
    """Return curriculum programs with verification state and provenance."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")

    catalogs = list_catalogs()
    result = []
    for cat in catalogs:
        prog = cat.program
        parts = prog.program_id.split("_")
        cohort = parts[-1] if len(parts) > 1 and parts[-1].isdigit() and len(parts[-1]) == 4 else None
        result.append(
            AdminProgramSummary(
                program_id=prog.program_id,
                name=prog.name,
                total_credits=prog.total_credits,
                course_count=len(cat.courses),
                catalog_status=prog.catalog_status,
                catalog_revision=prog.catalog_revision,
                cohort=cohort,
                source_file=prog.source_file,
                source_pages=prog.source_pages,
                notes=prog.notes,
            )
        )
    return result


@router.get("/courses", response_model=list[AdminCourseItem])
async def list_admin_courses(
    request: Request, program_id: str = Query(...)
) -> list[AdminCourseItem]:
    """Return courses in a curriculum program with prerequisite status."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")

    try:
        catalog = load_catalog(program_id)
    except CatalogError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc

    return [
        AdminCourseItem(
            code=c.code,
            name=c.name,
            name_en=c.name_en,
            credits=c.credits,
            block=c.block,
            requirement_type=c.requirement_type,
            prerequisites=c.prerequisites,
            prerequisites_raw=c.prerequisites_raw,
            prerequisite_status=c.prerequisite_status,
            suggested_term=c.suggested_term,
            year=c.year,
            source_status=c.source_status,
            source_page=c.source_page,
        )
        for c in catalog.courses
    ]
