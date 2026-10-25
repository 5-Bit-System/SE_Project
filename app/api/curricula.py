"""Non-personal curriculum lookup and hypothetical semester planning."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from app.curriculum_reference import (
    ReferenceError,
    list_references,
    plan_reference,
    reference,
    source_pdf,
)

router = APIRouter(prefix="/curricula/reference", tags=["Curriculum reference"])


def boundary(exc: ReferenceError):
    code = str(exc)
    status = 404 if code == "reference_program_not_found" else (
        503 if code == "reference_source_unavailable" else 422)
    raise HTTPException(status, code) from None


@router.get("")
def programs():
    return list_references()


@router.get("/{program_id}")
def curriculum(program_id: str, cohort: int = Query(default=67)):
    try:
        return reference(program_id, cohort)
    except ReferenceError as exc:
        boundary(exc)


@router.get("/{program_id}/source")
def document(program_id: str):
    try:
        path = source_pdf(program_id)
    except ReferenceError as exc:
        boundary(exc)
    return FileResponse(path, media_type="application/pdf", filename=path.name,
                        content_disposition_type="inline")


class ReferencePlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cohort: int = Field(default=67, ge=67)
    max_credits: int = Field(default=20, ge=1, le=30)
    course_codes: list[str] = Field(default_factory=list, max_length=150)
    suggest: bool = False


@router.post("/{program_id}/plan")
def plan(program_id: str, body: ReferencePlan):
    try:
        return plan_reference(program_id, **body.model_dump())
    except ReferenceError as exc:
        boundary(exc)
