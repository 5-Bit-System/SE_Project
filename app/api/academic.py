"""Authenticated source-owned academic endpoints, staged before legacy cutover.

Real applicability evidence/policy registration is deliberately absent until the
user's deferred program/login work is verified. Preview/readiness works now;
personal results fail closed rather than falling back to client-supplied grades.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.academic_context import AcademicContextError, AcademicPolicy, build_context, require_ready
from app.api.portal import safe_call, session
from app.auth.dependencies import COOKIE
from app.catalog import load_catalog
from app.integrations.daotao import runtime, store
from app.models import RankingWeights, RecommendationRequest, StructuredPreference
from app.progress import calculate_progress
from app.recommendation.llm import configured_adapters
from app.rules import _prepare_selection_context, evaluate_eligibility
from app.schemas.advisor import AdvisorMessage, AdvisorRequest
from app.services.advisor_service import chat_advisor
from app.services.recommendation_service import recommend

router = APIRouter()
# Server-reviewed policies only; no route accepts a policy or review flag from a student.
POLICIES: dict[str, AcademicPolicy] = {}


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


async def resolve_context(request: Request, query: AcademicQuery) -> tuple[Any, dict]:
    owner_id = (await session(request)).owner
    saved = await safe_call(store.profile, owner_id)
    try:
        catalog, revision = await asyncio.to_thread(_catalog_context, query.program_id)
        _prepare_selection_context(catalog, query.selected_track_id,
                                   query.selected_graduation_path_id)
    except ValueError:
        raise HTTPException(422, "academic_program_invalid") from None
    metadata = saved.get("profile") or {}
    binding = metadata.get("academic_binding")
    if not isinstance(binding, dict):
        binding = None
    policy = POLICIES.get(binding.get("policy_version")) if binding else None
    context = build_context(saved.get("snapshot"), owner_id=owner_id, catalog=catalog,
                            catalog_revision=revision, binding=binding, policy=policy)
    # Track/path are part of the revision even if they do not change passed facts.
    context["revision"] = hashlib.sha256(json.dumps({
        "context": context["revision"], "track": query.selected_track_id,
        "path": query.selected_graduation_path_id,
        "session": runtime.digest(request.cookies[COOKIE])}, sort_keys=True).encode()).hexdigest()
    context["fetched_at"] = saved.get("fetched_at")
    await session(request)  # DB/catalog I/O must not outlive a logout or expired session.
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
