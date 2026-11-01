"""Admin console API endpoints with strict role-based authorization."""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.auth.dependencies import require_account
from app.catalog import CatalogError, list_catalogs, load_catalog
from app.curriculum.diff_service import compute_curriculum_diff
from app.curriculum.import_service import validate_and_parse_csv
from app.curriculum.repository import (
    create_revision,
    get_active_revision,
    get_revision,
    list_revisions,
    publish_revision,
    review_revision,
    rollback_revision,
    update_revision_payload,
    update_validation,
)
from app.curriculum.rule_service import (
    build_prerequisite_graph,
    normalize_prerequisites,
    update_course_rules,
    validate_prerequisite_rules,
)
from app.integrations.daotao.store import engine
from app.services.admin_overview import AdminOverviewResponse, get_admin_overview


class CatalogImportRequest(BaseModel):
    program_id: str
    version_title: str
    cohort: str | None = None
    csv_content: str
    filename: str | None = None


class CatalogImportResponse(BaseModel):
    revision_id: str
    program_id: str
    version_title: str
    status: str
    validation_summary: dict


class CatalogValidationResponse(BaseModel):
    revision_id: str
    program_id: str
    status: str
    validation_summary: dict
    source_digest: str
    source_filename: str | None = None


class CatalogRevisionSummary(BaseModel):
    revision_id: str
    program_id: str
    cohort: str | None = None
    version_title: str
    status: str
    is_active: bool
    created_at: str
    source_filename: str | None = None


class RevisionActionRequest(BaseModel):
    reason: str = Field(min_length=3)
    notes: str | None = None


class RevisionDiffResponse(BaseModel):
    revision_id: str
    program_id: str
    base_revision_id: str | None = None
    summary: dict
    changes: dict


class PrerequisiteUpdateRequest(BaseModel):
    prerequisites: list[list[str]]
    reason: str = Field(min_length=3)


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
        cohort = (
            parts[-1] if len(parts) > 1 and parts[-1].isdigit() and len(parts[-1]) == 4 else None
        )
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


@router.post("/catalog-revisions/import", response_model=CatalogImportResponse)
async def import_catalog_revision(
    request: Request, body: CatalogImportRequest
) -> CatalogImportResponse:
    """Import and validate a curriculum draft without touching active catalog."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")

    # Parse and validate CSV
    val_result = validate_and_parse_csv(
        content=body.csv_content,
        program_id=body.program_id,
        version_title=body.version_title,
        cohort=body.cohort,
    )

    payload = {
        "program_id": body.program_id,
        "version_title": body.version_title,
        "cohort": body.cohort,
        "courses": val_result["courses"],
        "stats": val_result["stats"],
    }

    status = "validated" if val_result["valid"] else "draft"

    with engine().begin() as conn:
        rev = create_revision(
            conn,
            program_id=body.program_id,
            version_title=body.version_title,
            cohort=body.cohort,
            source_filename=body.filename,
            source_digest=val_result["digest"],
            payload=payload,
            created_by=principal.get("account_id"),
        )
        if status == "validated":
            rev = update_validation(conn, rev["revision_id"], status, val_result)

    return CatalogImportResponse(
        revision_id=rev["revision_id"],
        program_id=body.program_id,
        version_title=body.version_title,
        status=rev["status"],
        validation_summary=val_result,
    )


@router.get("/catalog-revisions/{revision_id}/validation", response_model=CatalogValidationResponse)
async def get_revision_validation(request: Request, revision_id: str) -> CatalogValidationResponse:
    """Get row-level validation errors, warnings and aggregate checks for a draft revision."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")

    with engine().connect() as conn:
        rev = get_revision(conn, revision_id)

    if not rev:
        raise HTTPException(404, detail=f"Revision {revision_id} not found")

    return CatalogValidationResponse(
        revision_id=rev["revision_id"],
        program_id=rev["program_id"],
        status=rev["status"],
        validation_summary=rev["validation_summary"],
        source_digest=rev["source_digest"],
        source_filename=rev["source_filename"],
    )


@router.get("/catalog-revisions/{revision_id}")
async def get_catalog_revision(request: Request, revision_id: str) -> dict:
    """Get single revision detail including payload and status."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")

    with engine().connect() as conn:
        rev = get_revision(conn, revision_id)

    if not rev:
        raise HTTPException(404, detail=f"Revision {revision_id} not found")

    return rev


@router.get("/catalog-revisions", response_model=list[CatalogRevisionSummary])
async def list_catalog_revisions(
    request: Request, program_id: str | None = None
) -> list[CatalogRevisionSummary]:
    """List versioned revisions for a program."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")

    with engine().connect() as conn:
        rows = list_revisions(conn, program_id=program_id)

    return [
        CatalogRevisionSummary(
            revision_id=r["revision_id"],
            program_id=r["program_id"],
            cohort=r.get("cohort"),
            version_title=r["version_title"],
            status=r["status"],
            is_active=r["is_active"],
            created_at=r["created_at"],
            source_filename=r.get("source_filename"),
        )
        for r in rows
    ]


@router.get("/catalog-revisions/{revision_id}/diff", response_model=RevisionDiffResponse)
async def get_revision_diff(
    request: Request, revision_id: str, base_revision_id: str | None = None
) -> RevisionDiffResponse:
    """Compare a revision against base (or active) revision."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")

    with engine().connect() as conn:
        target_rev = get_revision(conn, revision_id)
        if not target_rev:
            raise HTTPException(404, detail=f"Revision {revision_id} not found")

        base_rev = None
        if base_revision_id:
            base_rev = get_revision(conn, base_revision_id)
        else:
            base_rev = get_active_revision(conn, target_rev["program_id"])

    target_courses = (target_rev.get("payload") or {}).get("courses", [])
    base_courses = (base_rev.get("payload") or {}).get("courses", []) if base_rev else []

    diff_result = compute_curriculum_diff(base_courses, target_courses)

    return RevisionDiffResponse(
        revision_id=revision_id,
        program_id=target_rev["program_id"],
        base_revision_id=base_rev.get("revision_id") if base_rev else None,
        summary=diff_result["summary"],
        changes=diff_result["changes"],
    )


@router.post("/catalog-revisions/{revision_id}/approve")
async def approve_catalog_revision(
    request: Request, revision_id: str, body: RevisionActionRequest
) -> dict:
    """Approve a validated curriculum revision with required reason."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")

    try:
        with engine().begin() as conn:
            rev = review_revision(
                conn,
                revision_id=revision_id,
                reviewer_id=principal.get("account_id"),
                decision="approved",
                reason=body.reason,
                notes=body.notes,
            )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc

    return {"status": "approved", "revision_id": rev["revision_id"]}


@router.post("/catalog-revisions/{revision_id}/publish")
async def publish_catalog_revision(
    request: Request, revision_id: str, body: RevisionActionRequest
) -> dict:
    """Publish an approved revision, atomically deactivating previous active revision."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")

    try:
        with engine().begin() as conn:
            rev = publish_revision(
                conn,
                revision_id=revision_id,
                publisher_id=principal.get("account_id"),
                reason=body.reason,
            )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc

    return {
        "status": "published",
        "revision_id": rev["revision_id"],
        "is_active": rev["is_active"],
        "published_at": rev.get("published_at"),
    }


@router.post("/catalog-revisions/{revision_id}/rollback")
async def rollback_catalog_revision(
    request: Request, revision_id: str, body: RevisionActionRequest
) -> dict:
    """Roll back active pointer to this target revision."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")

    with engine().connect() as conn:
        target = get_revision(conn, revision_id)

    if not target:
        raise HTTPException(404, detail=f"Revision {revision_id} not found")

    try:
        with engine().begin() as conn:
            rev = rollback_revision(
                conn,
                program_id=target["program_id"],
                target_revision_id=revision_id,
                user_id=principal.get("account_id"),
                reason=body.reason,
            )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc

    return {
        "status": "published",
        "revision_id": rev["revision_id"],
        "is_active": rev["is_active"],
    }


@router.get("/catalog-revisions/{revision_id}/prerequisite-graph")
async def get_prerequisite_graph(request: Request, revision_id: str) -> dict:
    """Return dependency graph nodes and edges for visual rendering."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")

    with engine().connect() as conn:
        rev = get_revision(conn, revision_id)

    if not rev:
        raise HTTPException(404, detail=f"Revision {revision_id} not found")

    courses = (rev.get("payload") or {}).get("courses", [])
    return build_prerequisite_graph(courses)


@router.put("/catalog-revisions/{revision_id}/courses/{course_code}/prerequisites")
async def update_course_prerequisites(
    request: Request,
    revision_id: str,
    course_code: str,
    body: PrerequisiteUpdateRequest,
) -> dict:
    """Edit prerequisite conditions for a course in a draft revision (or branch if active)."""
    principal = await require_account(request)
    if principal.get("role") != "admin":
        raise HTTPException(403, "forbidden")

    with engine().connect() as conn:
        rev = get_revision(conn, revision_id)

    if not rev:
        raise HTTPException(404, detail=f"Revision {revision_id} not found")

    # If the revision is already published/active, we cannot mutate it directly!
    # We must branch a new draft revision.
    target_rev_id = revision_id
    payload = rev.get("payload") or {}
    courses = payload.get("courses", [])

    norm_prereqs = normalize_prerequisites(body.prerequisites)

    # Validate rules
    is_valid, errors = validate_prerequisite_rules(
        target_code=course_code,
        new_prerequisites=norm_prereqs,
        all_courses=courses,
    )
    if not is_valid:
        raise HTTPException(400, detail="; ".join(errors))

    # Update payload
    try:
        updated_payload = update_course_rules(payload, course_code, norm_prereqs)
    except ValueError as exc:
        raise HTTPException(404, detail=str(exc)) from exc

    with engine().begin() as conn:
        if rev["is_active"] or rev["status"] == "published":
            # Branch a new draft revision
            branch_title = f"[Bản thảo] {rev['version_title']} (Cập nhật môn {course_code})"
            new_rev = create_revision(
                conn,
                program_id=rev["program_id"],
                version_title=branch_title,
                cohort=rev.get("cohort"),
                source_filename=rev.get("source_filename"),
                source_digest=rev["source_digest"],
                payload=updated_payload,
                created_by=principal.get("account_id"),
            )
            target_rev_id = new_rev["revision_id"]
        else:
            update_revision_payload(
                conn,
                revision_id=target_rev_id,
                payload=updated_payload,
                updated_by=principal.get("account_id"),
                reason=body.reason,
            )

    return {
        "revision_id": target_rev_id,
        "course_code": course_code.upper(),
        "prerequisites": norm_prereqs,
        "branched": target_rev_id != revision_id,
    }
