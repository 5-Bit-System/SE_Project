import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.config import get_settings
from app.errors import StorageDataError, StorageUnavailable

logger = logging.getLogger(__name__)


def check_storage_ready() -> None:
    if get_settings().storage_backend == "postgres":
        from app.infrastructure.repositories import postgres_repository

        postgres_repository().ready()
    else:
        from app.catalog import list_catalogs

        if len(list_catalogs()) != 4:
            raise StorageDataError("Chưa có đủ bốn catalog")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    check_storage_ready()
    yield


app = FastAPI(title="Explainable Course Recommender", version="0.2.0", lifespan=lifespan)
STATIC_ROOT = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")
app.include_router(api_router)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_ROOT / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    check_storage_ready()
    return {"status": "ok", "storage": get_settings().storage_backend}


@app.exception_handler(StorageUnavailable)
async def storage_unavailable_handler(request: Request, exc: StorageUnavailable) -> JSONResponse:
    logger.error("Storage unavailable for %s", request.url.path)
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(StorageDataError)
async def storage_data_error_handler(request: Request, exc: StorageDataError) -> JSONResponse:
    logger.error("Stored data invalid for %s", request.url.path)
    return JSONResponse(
        status_code=500, content={"detail": "Dữ liệu máy chủ chưa hợp lệ; kiểm tra migration/seed"}
    )
