import hashlib
import logging
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.academic import router as academic_router
from app.api.curricula import router as curricula_router
from app.api.portal import router as portal_router
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
    try:
        yield
    finally:
        from app.integrations.daotao.runtime import shutdown

        await shutdown()


app = FastAPI(title="Explainable Course Recommender", version="0.2.0", lifespan=lifespan)
STATIC_ROOT = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")
app.include_router(api_router)
app.include_router(portal_router)
app.include_router(academic_router)
app.include_router(curricula_router)


@app.middleware("http")
async def portal_boundary(request: Request, call_next):
    protected = request.url.path.startswith(("/auth/", "/me/"))
    if protected:
        allowed = {"http://127.0.0.1:8000", "http://localhost:8000"}
        origin = request.headers.get("origin")
        if (str(request.base_url).rstrip("/") not in allowed
                or (request.method not in {"GET", "HEAD"} and origin not in allowed)):
            return JSONResponse({"detail": "origin_rejected"}, status_code=403,
                                headers={"Cache-Control": "no-store"})
    response = await call_next(request)
    if protected:
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
    elif request.url.path == "/":
        response.headers["Cache-Control"] = "no-store"
    elif request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/")
def index() -> HTMLResponse:
    template = (STATIC_ROOT / "index.html").read_text(encoding="utf-8")

    def version_asset(match: re.Match) -> str:
        name = match[2]
        path = STATIC_ROOT / name
        if not path.is_file():
            return match[0]
        revision = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        return f'{match[1]}/static/{name}?v={revision}"'

    markup = re.sub(r'(\b(?:src|href)=")/static/([^"?#]+)"', version_asset, template)
    return HTMLResponse(markup)


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
