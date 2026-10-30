"""Source-owned academic endpoints using current account sessions and owner binding.

Complete source evidence and applicable program/policy remain mandatory. The
course board can show individually resolved facts while strict APIs stay gated.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.academic_context import AcademicContextError, build_context, require_ready
from app.academic_policies import POLICIES
from app.api.portal import safe_call, session
from app.auth import portal as account_portal
from app.auth.dependencies import COOKIE, require_account
from app.auth.dependencies import call as auth_call
from app.catalog import load_catalog
from app.catalog_contracts import digest
from app.integrations.daotao import runtime, store
from app.models import RankingWeights, RecommendationRequest, StructuredPreference
from app.program_bindings import ProgramBindingError, binding_current
from app.program_bindings import confirm as confirm_program
from app.program_bindings import options as program_options
from app.progress import calculate_progress
from app.recommendation.llm import configured_adapters
from app.rules import _prepare_selection_context, evaluate_eligibility
from app.schemas.advisor import AdvisorMessage, AdvisorRequest
from app.services import semester_plan_service as plans
from app.services.advisor_service import chat_advisor
from app.services.course_status_service import course_board, reviewed_course_board
from app.services.recommendation_service import recommend

router = APIRouter()
# Server-reviewed policies only; no route accepts a policy or review flag from a student.


@router.get("/academic-policy/vnu-3626-2022")
def policy_source():
    path = Path(__file__).resolve().parents[2] / "docs/policies/vnu_3626_2022.pdf"
    return FileResponse(path, media_type="application/pdf", filename="vnu_3626_2022.pdf",
                        content_disposition_type="inline")


class AcademicQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    program_id: str = Field(min_length=1, max_length=100)
    selected_track_id: str | None = Field(default=None, max_length=100)
    selected_graduation_path_id: str | None = Field(default=None, max_length=100)


class AcademicOperation(AcademicQuery):
    expected_revision: str | None = Field(default=None, max_length=64)
    goal: str = Field(default="", max_length=500)
    max_credits: int = Field(default=18, ge=1, le=30)
    limit: int = Field(default=5, ge=1, le=20)
    preference: StructuredPreference | None = None
    ranking_weights: RankingWeights | None = None
    message: str = Field(default="", max_length=1000)
    history: list[AdvisorMessage] = Field(default_factory=list, max_length=20)


def parse_query(request: Request) -> AcademicQuery:
    try:
        return AcademicQuery.model_validate(dict(request.query_params))
    except ValidationError:
        raise HTTPException(422, "invalid_academic_request") from None


async def parse_body(request: Request) -> AcademicOperation:
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 16384:
            raise HTTPException(413, "invalid_academic_request")
    try:
        result = AcademicOperation.model_validate_json(raw)
        if any(message.role == "system" for message in result.history):
            raise ValueError
        return result
    except (ValueError, ValidationError):
        # Never echo a submitted student payload in validation errors.
        raise HTTPException(422, "invalid_academic_request") from None


def _catalog_context(program_id: str):
    catalog = load_catalog(program_id)
    # Content-addressed revision for this staged read-only context, not a DB FK.
    revision = hashlib.sha256(json.dumps(catalog.model_dump(mode="json"),
                                        sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return catalog, revision


async def resolve_context(request: Request, query: AcademicQuery, saved: dict | None = None,
                          source_session: runtime.Session | None = None,
                          preview_unverified_metadata: bool = False) -> tuple[Any, dict]:
    value = source_session or await session(request)
    owner_id = value.owner
    if saved is None:
        saved = await safe_call(store.profile, owner_id)
    await auth_call(account_portal.check, value)
    try:
        catalog, revision = await asyncio.to_thread(_catalog_context, query.program_id)
        _prepare_selection_context(catalog, query.selected_track_id,
                                   query.selected_graduation_path_id)
    except ValueError:
        raise HTTPException(422, "academic_program_invalid") from None
    metadata = saved.get("profile") or {}
    binding = metadata.get("academic_binding")
    if not isinstance(binding, dict) or not binding_current(metadata):
        binding = None
    policy = POLICIES.get(binding.get("policy_version")) if binding else None
    context = build_context(saved.get("snapshot"), owner_id=owner_id, catalog=catalog,
                            catalog_revision=revision, binding=binding, policy=policy,
                            preview_unverified_metadata=preview_unverified_metadata)
    # Track/path are part of the revision even if they do not change passed facts.
    context["revision"] = hashlib.sha256(json.dumps({
        "context": context["revision"], "track": query.selected_track_id,
        "path": query.selected_graduation_path_id,
        "session": runtime.digest(request.cookies[COOKIE])}, sort_keys=True).encode()).hexdigest()
    context["fetched_at"] = saved.get("fetched_at")
    await auth_call(account_portal.check, value)  # Recheck the original owner after I/O.
    return catalog, context


def ready(context: dict, expected_revision: str | None = None) -> set[str]:
    try:
        return require_ready(context, expected_revision)
    except AcademicContextError as exc:
        raise HTTPException(409, {"code": str(exc), "context_revision": context["revision"],
                                  "status": context["status"],
                                  "blocking_reasons": context["blocking_reasons"]}) from None


async def ensure_current(request: Request, query: AcademicQuery, context: dict) -> None:
    """Discard slow ranking/chat output if its owner/session/source has changed."""
    _, current = await resolve_context(request, query)
    ready(current, context["revision"])


@router.get("/me/academic-context")
async def context_view(request: Request):
    await session(request)
    _, context = await resolve_context(request, parse_query(request))
    return context


class CourseBoardQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_credits: int = Field(default=20, ge=1, le=30)
    selected_track_id: str | None = Field(default=None, max_length=100)
    selected_graduation_path_id: str | None = Field(default=None, max_length=100)


class ProgramConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    program_id: str = Field(min_length=1, max_length=100)
    cohort: int = Field(ge=67, le=200)
    expected_catalog_revision: str = Field(min_length=64, max_length=64)
    expected_snapshot_digest: str = Field(min_length=1, max_length=100)
    expected_source_scope: str = Field(min_length=64, max_length=64)
    confirm: bool = Field(strict=True)


@router.get("/me/academic-program")
async def academic_program(request: Request):
    value = (await session(request))
    saved = await safe_call(store.profile, value.owner)
    result = await asyncio.to_thread(program_options, saved)
    await auth_call(account_portal.check, value)
    return result


@router.post("/me/academic-program")
async def academic_program_confirm(request: Request):
    value = (await session(request))
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 4096:
            raise HTTPException(413, "invalid_academic_request")
    try:
        body = ProgramConfirmation.model_validate_json(raw)
        if body.confirm is not True:
            raise ValueError
    except ValueError:
        raise HTTPException(422, "academic_program_confirmation_required") from None
    saved = await safe_call(store.profile, value.owner)
    try:
        binding = await asyncio.to_thread(confirm_program, saved,
            **body.model_dump(exclude={"confirm"}))
    except ProgramBindingError as exc:
        raise HTTPException(409, str(exc)) from None
    await session(request)
    await auth_call(account_portal.save_academic_binding, value, binding,
                    body.expected_snapshot_digest, body.expected_source_scope)
    await session(request)
    return {"confirmed": True, "program_id": binding["program_id"], "cohort": binding["cohort"]}


@router.get("/me/course-status")
async def course_status(request: Request):
    """Choose the catalog from server-owned evidence, never a display name/default."""
    value = await session(request)
    owner_id = value.owner
    try:
        options = CourseBoardQuery.model_validate(dict(request.query_params))
    except ValidationError:
        raise HTTPException(422, "invalid_academic_request") from None
    saved = await safe_call(store.profile, owner_id)
    await auth_call(account_portal.check, value)
    binding = (saved.get("profile") or {}).get("academic_binding")
    unavailable = {
        "status": "needs_program_binding", "blocking_reasons": [],
        "courses": None, "progress": None, "plan": None,
        "latest_collection": (await session(request)).latest_collection,
    }
    snapshot = saved.get("snapshot") or {}
    unavailable["collection_status"] = {
        "connector_version": snapshot.get("connector_version"),
        "completeness": snapshot.get("completeness"),
        "evidence": snapshot.get("collection_evidence"),
        "unparsed_rows": len(snapshot.get("unknown_rows") or []),
    }
    if not snapshot:
        unavailable["blocking_reasons"].append("source_missing")
    elif snapshot.get("completeness") != "complete":
        unavailable["blocking_reasons"].append("source_incomplete")
    if (not isinstance(binding, dict) or not binding_current(saved.get("profile") or {})
            or binding.get("verified") is not True
            or not isinstance(binding.get("program_id"), str)
            or not binding["program_id"].strip()):
        unavailable["blocking_reasons"].append("program_binding_unverified")
        unavailable["program_selection"] = await asyncio.to_thread(program_options, saved)
        await auth_call(account_portal.check, value)
        return unavailable
    query = AcademicQuery(program_id=binding["program_id"], **options.model_dump(exclude={"max_credits"}))
    catalog, context = await resolve_context(
        request, query, saved, source_session=value,
        preview_unverified_metadata=True,
    )
    selections = {
        "tracks": [track.model_dump() for track in catalog.program.track_selection.tracks],
        "paths": [path.model_dump() for path in catalog.program.graduation_selection.paths],
        "track_required": catalog.program.track_selection.mode == "exactly_one_track",
        "path_required": catalog.program.graduation_selection.mode == "exactly_one_path",
    }
    board_context = dict(context)
    preview_reasons = []
    if catalog.program.catalog_status != "verified":
        preview_reasons.append("catalog_unverified")
    if any(course.source_status != "verified" for course in catalog.courses):
        preview_reasons.append("course_source_unverified")
    if any(course.prerequisite_status not in {
        "verified", "unknown", "conflict", "source_conflict",
    } for course in catalog.courses):
        preview_reasons.append("prerequisite_unverified")
    board_context["blocking_reasons"] = list(dict.fromkeys([
        *context["blocking_reasons"], *preview_reasons,
    ]))
    if preview_reasons and context["status"] == "ready":
        board_context["status"] = "needs_policy_review"
    allowed_review_reasons = {
        "catalog_unverified", "course_source_unverified", "prerequisite_unverified",
        "course_outcomes_unresolved", "program_rules_review_required",
    }
    reviewable = (board_context["status"] == "needs_policy_review"
                  and board_context["blocking_reasons"]
                  and set(board_context["blocking_reasons"]) <= allowed_review_reasons)
    if board_context["status"] != "ready" and not reviewable:
        result = {**unavailable, "status": board_context["status"],
                  "blocking_reasons": board_context["blocking_reasons"], "selections": selections}
        if "program_binding_unverified" in board_context["blocking_reasons"]:
            result["program_selection"] = await asyncio.to_thread(program_options, saved)
        return result
    missing = []
    if selections["track_required"] and not query.selected_track_id:
        missing.append("track_selection_required")
    if selections["path_required"] and not query.selected_graduation_path_id:
        missing.append("graduation_selection_required")
    if missing:
        result = reviewed_course_board(catalog, board_context, options.max_credits,
            query.selected_track_id, query.selected_graduation_path_id, missing)
    elif reviewable:
        result = reviewed_course_board(catalog, board_context, options.max_credits,
            query.selected_track_id, query.selected_graduation_path_id)
    else:
        result = course_board(catalog, board_context, options.max_credits,
                              query.selected_track_id, query.selected_graduation_path_id)
    if result["status"] == "partial":
        _, current = await resolve_context(request, query)
        if current["revision"] != context["revision"]:
            raise HTTPException(409, "context_changed")
    else:
        await ensure_current(request, query, context)
    return {**result, "selections": selections,
            "plan_basis": digest(plans.basis_for(saved, catalog,
                query.selected_track_id, query.selected_graduation_path_id))}


@router.get("/me/eligibility")
async def eligibility(request: Request):
    await session(request)
    query = parse_query(request)
    catalog, context = await resolve_context(request, query)
    passed = ready(context)
    result = evaluate_eligibility(catalog, passed, max_credits=30,
        selected_track_id=query.selected_track_id,
        selected_graduation_path_id=query.selected_graduation_path_id).model_dump(mode="json")
    return {**result, "context_revision": context["revision"]}


@router.get("/me/academic-progress")
async def progress(request: Request):
    await session(request)
    query = parse_query(request)
    catalog, context = await resolve_context(request, query)
    passed = ready(context)
    result = calculate_progress(catalog, passed, query.selected_track_id,
                                query.selected_graduation_path_id)
    return {"context_revision": context["revision"], "progress": result,
            "gpa": None, "gpa_source": "portal_only"}


async def operation(request: Request):
    await session(request)
    query = await parse_body(request)
    catalog, context = await resolve_context(request, query)
    passed = ready(context, query.expected_revision)
    if query.expected_revision is None:
        raise HTTPException(409, "context_revision_required")
    return query, catalog, context, passed


@router.post("/me/recommendations")
async def recommendations(request: Request):
    query, catalog, context, passed = await operation(request)
    internal = RecommendationRequest(**query.model_dump(include={
        "goal", "max_credits", "limit", "selected_track_id", "selected_graduation_path_id",
        "preference", "ranking_weights"}), program_id=catalog.program.program_id,
        passed_course_codes=sorted(passed))
    extractor, ranker = configured_adapters()
    result = await asyncio.to_thread(recommend, catalog, internal,
                                     preference_extractor=extractor, llm_ranker=ranker)
    await ensure_current(request, query, context)
    return {**result.model_dump(mode="json"), "context_revision": context["revision"]}


@router.post("/me/recommendations/what-if")
async def what_if(request: Request):
    # A ready context alone is not a baseline. No fabricated what-if comparison.
    await operation(request)
    raise HTTPException(409, "academic_baseline_not_available")


@router.post("/me/advisor/chat")
async def advisor(request: Request):
    query, catalog, context, passed = await operation(request)
    if not query.message.strip():
        raise HTTPException(422, "academic_message_required")
    internal = AdvisorRequest(program_id=catalog.program.program_id, message=query.message,
        history=query.history, passed_course_codes=sorted(passed),
        selected_track_id=query.selected_track_id,
        selected_graduation_path_id=query.selected_graduation_path_id)
    result = await asyncio.to_thread(chat_advisor, catalog, internal)
    await ensure_current(request, query, context)
    return {**result.model_dump(mode="json"), "context_revision": context["revision"]}


class SemesterPlanInput(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=100)
    academic_year_start: int = Field(ge=2000, le=2100, strict=True)
    semester: int = Field(ge=1, le=3, strict=True)
    max_credits: int = Field(default=20, ge=1, le=30, strict=True)
    selected_track_id: str | None = Field(default=None, max_length=100)
    selected_graduation_path_id: str | None = Field(default=None, max_length=100)
    course_codes: list[str] = Field(max_length=100)
    expected_basis: str = Field(pattern=r'^[a-f0-9]{64}$')
    expected_version: int | None = Field(default=None, ge=1, strict=True)


async def plan_body(request):
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 16384:
            raise HTTPException(413, 'invalid_semester_plan')
    try:
        return SemesterPlanInput.model_validate_json(raw)
    except ValueError:
        raise HTTPException(422, 'invalid_semester_plan') from None


@router.get('/me/semester-plans')
async def semester_plans(request: Request):
    principal = await require_account(request)
    return {'plans': await auth_call(plans.list_plans, principal)}


@router.post('/me/semester-plans', status_code=201)
async def semester_plan_create(request: Request):
    value = await session(request)
    body = await plan_body(request)
    if body.expected_version is not None:
        raise HTTPException(422, 'invalid_semester_plan')
    return await auth_call(plans.save_plan, value, body)


@router.put('/me/semester-plans/{plan_id}')
async def semester_plan_update(plan_id: UUID, request: Request):
    value = await session(request)
    body = await plan_body(request)
    if body.expected_version is None:
        raise HTTPException(422, 'semester_plan_version_required')
    return await auth_call(plans.save_plan, value, body, plan_id)


@router.delete('/me/semester-plans/{plan_id}')
async def semester_plan_delete(plan_id: UUID, request: Request):
    principal = await require_account(request)
    raw = request.query_params.get('expected_version', '')
    if not raw.isdigit() or int(raw) < 1 or len(raw) > 10:
        raise HTTPException(422, 'semester_plan_version_required')
    await auth_call(plans.delete_plan, principal, plan_id, int(raw))
    return {'deleted': True}
