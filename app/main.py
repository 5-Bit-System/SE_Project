from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.catalog import CatalogError, CatalogNotFoundError, list_catalogs, load_catalog
from app.models import (
    CatalogErrorResponse,
    CourseResponse,
    ProgramResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from app.service import recommend


app = FastAPI(title="Explainable Course Recommender", version="0.1.0")
STATIC_ROOT = Path(__file__).resolve().parent / "static"
CATALOG_UNAVAILABLE = "Không thể tải dữ liệu catalog. Vui lòng thử lại sau."
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_ROOT / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/programs",
    tags=["Catalog"],
    response_model=list[ProgramResponse],
    responses={503: {"model": CatalogErrorResponse, "description": "Dữ liệu catalog không tải được"}},
)
def programs() -> list[dict]:
    try:
        return [
            {**catalog.program.model_dump(), "course_count": len(catalog.courses)}
            for catalog in list_catalogs()
        ]
    except CatalogError as exc:
        raise HTTPException(status_code=503, detail=CATALOG_UNAVAILABLE) from exc


@app.get(
    "/courses",
    tags=["Catalog"],
    response_model=list[CourseResponse],
    responses={
        404: {"model": CatalogErrorResponse, "description": "Ngành không tồn tại"},
        503: {"model": CatalogErrorResponse, "description": "Dữ liệu catalog không tải được"},
    },
)
def courses(program_id: str = Query(..., min_length=1, description="ID ngành từ GET /programs")) -> list[dict]:
    try:
        return [course.model_dump() for course in load_catalog(program_id).courses]
    except CatalogNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CatalogError as exc:
        raise HTTPException(status_code=503, detail=CATALOG_UNAVAILABLE) from exc


@app.post("/recommendations", response_model=RecommendationResponse)
def recommendations(request: RecommendationRequest) -> RecommendationResponse:
    try:
        catalog = load_catalog(request.program_id)
        return recommend(catalog, request)
    except CatalogError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
