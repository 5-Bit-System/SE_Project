from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.catalog import CatalogError, list_catalogs, load_catalog
from app.models import RecommendationRequest, RecommendationResponse
from app.service import recommend


app = FastAPI(title="Explainable Course Recommender", version="0.1.0")
STATIC_ROOT = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_ROOT / "index.html")


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
