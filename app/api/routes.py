from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import retired_profile, verified_account
from app.catalog import CatalogError, list_catalogs, load_catalog
from app.profiles import ProfileError, list_profiles, load_profile
from app.progress import calculate_progress
from app.recommendation.llm import configured_adapters
from app.rules import evaluate_eligibility
from app.schemas.advisor import AdvisorRequest, AdvisorResponse
from app.schemas.catalog import (
    Course,
    CourseRequirementType,
    CourseSearchPage,
    CourseSort,
    ProgramCatalogMetadata,
)
from app.schemas.eligibility import EligibilityRequest, EligibilityResult
from app.schemas.profile import ProfileDetail, ProfileSummary, TranscriptSummary
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse, WhatIfRequest
from app.services.advisor_service import chat_advisor
from app.services.course_search_service import search_courses
from app.services.recommendation_service import recommend
from app.transcript import StudentTranscript

router = APIRouter()


def _catalog_metadata(catalog) -> ProgramCatalogMetadata:
    """Tạo metadata catalog thống nhất cho mọi API response."""
    return ProgramCatalogMetadata.model_validate(
        {
            **catalog.program.model_dump(),
            "course_count": len(catalog.courses),
        }
    )


def _raise_domain_error(exc: ValueError, *, catalog_not_found: bool = False) -> None:
    """Map lỗi domain về HTTP status thống nhất ở boundary API."""
    if isinstance(exc, CatalogError) or catalog_not_found:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    raise HTTPException(status_code=422, detail=str(exc)) from exc


def _raise_profile_error(exc: ProfileError) -> None:
    """Profile không tồn tại là 404; profile fixture không hợp lệ là 422."""
    if str(exc).lower().startswith("không tìm thấy profile"):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/programs", response_model=list[ProgramCatalogMetadata])
def programs() -> list[ProgramCatalogMetadata]:
    try:
        return [_catalog_metadata(catalog) for catalog in list_catalogs()]
    except CatalogError as exc:
        _raise_domain_error(exc)
    except ValueError as exc:
        _raise_domain_error(exc)


@router.get("/courses", response_model=list[Course])
def courses(program_id: str = Query(...)) -> list[Course]:
    try:
        return load_catalog(program_id).courses
    except CatalogError as exc:
        _raise_domain_error(exc)
    except ValueError as exc:
        _raise_domain_error(exc)


@router.get("/courses/search", response_model=CourseSearchPage)
def course_search(
    program_id: str = Query(...), q: str = Query(default="", max_length=120),
    block: str | None = Query(default=None),
    requirement_type: CourseRequirementType | None = Query(default=None),
    sort: CourseSort = Query(default="code"), page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> CourseSearchPage:
    try:
        return search_courses(
            load_catalog(program_id), q=q, block=block, requirement_type=requirement_type,
            sort=sort, page=page, page_size=page_size,
        )
    except CatalogError as exc:
        _raise_domain_error(exc)
    except ValueError as exc:
        _raise_domain_error(exc)


@router.get("/profiles", response_model=list[ProfileSummary], dependencies=[Depends(retired_profile)])
def profiles(program_id: str | None = Query(default=None)) -> list[ProfileSummary]:
    try:
        catalog = load_catalog(program_id) if program_id else None
        return [
            ProfileSummary.model_validate(
                {
                    "profile_id": profile.profile_id,
                    "program_id": profile.program_id,
                    "label": profile.label,
                    "current_term": profile.current_term,
                    "target_track": profile.target_track,
                    "career_goal": profile.career_goal,
                    "preferences": profile.preferences,
                    "record_count": len(profile.records),
                    "catalog": _catalog_metadata(catalog or load_catalog(profile.program_id)),
                }
            )
            for profile in list_profiles(program_id)
        ]
    except ProfileError as exc:
        _raise_profile_error(exc)
    except CatalogError as exc:
        _raise_domain_error(exc)
    except ValueError as exc:
        _raise_domain_error(exc)


@router.get("/profiles/{profile_id}", response_model=ProfileDetail, dependencies=[Depends(retired_profile)])
def profile_detail(profile_id: str) -> ProfileDetail:
    try:
        profile = load_profile(profile_id)
        catalog = load_catalog(profile.program_id)
        return ProfileDetail.model_validate(
            {
                **profile.model_dump(),
                "catalog": _catalog_metadata(catalog),
            }
        )
    except ProfileError as exc:
        _raise_profile_error(exc)
    except CatalogError as exc:
        _raise_domain_error(exc)
    except ValueError as exc:
        _raise_domain_error(exc)


@router.get("/profiles/{profile_id}/transcript/summary", response_model=TranscriptSummary, dependencies=[Depends(retired_profile)])
def profile_transcript_summary(profile_id: str) -> TranscriptSummary:
    try:
        profile = load_profile(profile_id)
        transcript = profile.to_transcript()
        catalog = load_catalog(profile.program_id)
        isolation = transcript.validate_major_isolation(catalog)
        return {
            "profile_id": profile.profile_id,
            "program_id": catalog.program.program_id,
            "program_name": catalog.program.name,
            "current_term": profile.current_term,
            "target_track": profile.target_track,
            "career_goal": profile.career_goal,
            "preferences": profile.preferences,
            "earned_credits": transcript.calculate_earned_credits(catalog),
            "progress": calculate_progress(catalog, transcript.passed_course_codes),
            "gpa": transcript.calculate_gpa(catalog),
            "gpa_10": transcript.calculate_gpa_10(catalog),
            "gpa_scale": 4.0,
            "passed_courses": sorted(transcript.passed_course_codes),
            "failed_courses": sorted(transcript.failed_course_codes),
            "isolation": isolation,
            "catalog": _catalog_metadata(catalog),
        }
    except ProfileError as exc:
        _raise_profile_error(exc)
    except CatalogError as exc:
        _raise_domain_error(exc)
    except ValueError as exc:
        _raise_domain_error(exc)


@router.post("/recommendations", response_model=RecommendationResponse, dependencies=[Depends(verified_account)])
def recommendations(request: RecommendationRequest) -> RecommendationResponse:
    try:
        catalog = load_catalog(request.program_id)
        preference_extractor, llm_ranker = configured_adapters()
        # Validate the enriched response at the API boundary so legacy callers
        # and newer recommendation backends share one response contract.
        return RecommendationResponse.model_validate(
            recommend(
                catalog,
                request,
                preference_extractor=preference_extractor,
                llm_ranker=llm_ranker,
            ).model_dump()
        )
    except CatalogError as exc:
        _raise_domain_error(exc)
    except ValueError as exc:
        _raise_domain_error(exc)


@router.post("/recommendations/what-if", response_model=RecommendationResponse, dependencies=[Depends(verified_account)])
def recommendations_what_if(request: WhatIfRequest) -> RecommendationResponse:
    """Xep hang lai tren eligibility vua tinh, chi thay preference/weights."""
    try:
        catalog = load_catalog(request.program_id)
        eligibility = evaluate_eligibility(
            catalog,
            set(request.passed_course_codes),
            max_credits=request.max_credits,
            selected_track_id=request.selected_track_id,
            selected_graduation_path_id=request.selected_graduation_path_id,
        )
        preference_extractor, llm_ranker = configured_adapters()
        return RecommendationResponse.model_validate(
            recommend(
                catalog,
                request,
                preference_extractor=preference_extractor,
                llm_ranker=llm_ranker,
                eligibility=eligibility,
                what_if=True,
            ).model_dump()
        )
    except CatalogError as exc:
        _raise_domain_error(exc)
    except ValueError as exc:
        _raise_domain_error(exc)


@router.post("/transcript/summary", response_model=TranscriptSummary, dependencies=[Depends(verified_account)])
def transcript_summary(transcript: StudentTranscript) -> TranscriptSummary:
    try:
        catalog = load_catalog(transcript.program_id)
        isolation = transcript.validate_major_isolation(catalog)
        return {
            "program_id": catalog.program.program_id,
            "program_name": catalog.program.name,
            "earned_credits": transcript.calculate_earned_credits(catalog),
            "progress": calculate_progress(
                catalog,
                transcript.passed_course_codes,
                transcript.selected_track_id,
                transcript.selected_graduation_path_id,
            ),
            "gpa": transcript.calculate_gpa(catalog),
            "gpa_10": transcript.calculate_gpa_10(catalog),
            "gpa_scale": 4.0,
            "passed_courses": sorted(transcript.passed_course_codes),
            "failed_courses": sorted(transcript.failed_course_codes),
            "isolation": isolation,
            "catalog": _catalog_metadata(catalog),
        }
    except CatalogError as exc:
        _raise_domain_error(exc)
    except ValueError as exc:
        _raise_domain_error(exc)


@router.post("/eligibility", response_model=EligibilityResult, dependencies=[Depends(verified_account)])
def check_eligibility(request: EligibilityRequest) -> EligibilityResult:
    try:
        catalog = load_catalog(request.program_id)
        return evaluate_eligibility(
            catalog,
            set(request.passed_course_codes),
            max_credits=request.max_credits,
            selected_track_id=request.selected_track_id,
            selected_graduation_path_id=request.selected_graduation_path_id,
        )
    except CatalogError as exc:
        _raise_domain_error(exc)
    except ValueError as exc:
        _raise_domain_error(exc)


@router.post("/advisor/chat", response_model=AdvisorResponse, dependencies=[Depends(verified_account)])
def advisor_chat_endpoint(request: AdvisorRequest) -> AdvisorResponse:
    try:
        catalog = load_catalog(request.program_id)
        return chat_advisor(catalog, request)
    except CatalogError as exc:
        _raise_domain_error(exc)
    except ValueError as exc:
        _raise_domain_error(exc)
