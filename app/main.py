from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.advisor import AdvisorRequest, AdvisorResponse, chat_advisor
from app.catalog import CatalogError, list_catalogs, load_catalog
from app.models import (
    EligibilityRequest,
    EligibilityResult,
    RecommendationRequest,
    RecommendationResponse,
)
from app.rules import evaluate_eligibility
from app.service import recommend
from app.transcript import StudentTranscript


app = FastAPI(title="Explainable Course Recommender", version="0.1.0")
STATIC_ROOT = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_ROOT / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/programs")
def programs() -> list[dict]:
    return [
        {**catalog.program.model_dump(), "course_count": len(catalog.courses)}
        for catalog in list_catalogs()
    ]


@app.get("/courses")
def courses(program_id: str = Query(...)) -> list[dict]:
    try:
        return [course.model_dump() for course in load_catalog(program_id).courses]
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/recommendations", response_model=RecommendationResponse)
def recommendations(request: RecommendationRequest) -> RecommendationResponse:
    try:
        catalog = load_catalog(request.program_id)
        return recommend(catalog, request)
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/transcript/summary")
def transcript_summary(transcript: StudentTranscript) -> dict:
    try:
        catalog = load_catalog(transcript.program_id)
        isolation = transcript.validate_major_isolation(catalog)
        return {
            "program_id": catalog.program.program_id,
            "program_name": catalog.program.name,
            "earned_credits": transcript.calculate_earned_credits(catalog),
            "gpa": transcript.calculate_gpa(catalog),
            "passed_courses": sorted(transcript.passed_course_codes),
            "failed_courses": sorted(transcript.failed_course_codes),
            "isolation": isolation,
        }
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/eligibility", response_model=EligibilityResult)
def check_eligibility(request: EligibilityRequest) -> EligibilityResult:
    try:
        catalog = load_catalog(request.program_id)
        return evaluate_eligibility(
            catalog,
            set(request.passed_course_codes),
            max_credits=request.max_credits,
        )
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/advisor/chat", response_model=AdvisorResponse)
def advisor_chat_endpoint(request: AdvisorRequest) -> AdvisorResponse:
    try:
        catalog = load_catalog(request.program_id)
        return chat_advisor(catalog, request)
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
