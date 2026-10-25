import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.academic import router as academic_router
from app.api.auth import router as auth_router
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


def check_auth_ready():
    from sqlalchemy import text

    from app.auth import repository
    from app.auth.settings import settings as auth_settings

    config = auth_settings()
    if config.environment == 'production':
        if get_settings().storage_backend != 'postgres':
            raise StorageDataError('Production authentication requires PostgreSQL')
        with repository.engine().connect() as conn:
            if conn.execute(text('SELECT count(*) FROM accounts WHERE seeded_for_dev AND is_active')).scalar_one():
                raise StorageDataError('Production cannot run with active development seed accounts')


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    check_storage_ready()
    check_auth_ready()
    from app.integrations.daotao.runtime import startup

    startup()
    try:
        yield
    finally:
        from app.integrations.daotao.runtime import shutdown

        await shutdown()


app = FastAPI(title="Explainable Course Recommender", version="0.2.0", lifespan=lifespan)
STATIC_ROOT = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")
app.include_router(api_router)
app.include_router(auth_router)
app.include_router(portal_router)
app.include_router(academic_router)


@app.middleware("http")
async def portal_boundary(request: Request, call_next):
    legacy = request.url.path.startswith('/profiles') or request.url.path in {
        '/recommendations', '/recommendations/what-if', '/eligibility', '/transcript/summary', '/advisor/chat'}
    protected = legacy or request.url.path.startswith(("/auth/", "/me/", "/admin/"))
    if protected:
        from app.auth.settings import settings as auth_settings
        allowed = set(auth_settings().allowed_origins)
        origin = request.headers.get("origin")
        if (str(request.base_url).rstrip("/") not in allowed
                or (request.method not in {"GET", "HEAD"} and origin not in allowed)):
            return JSONResponse({"detail": "origin_rejected"}, status_code=403,
                                headers={"Cache-Control": "no-store"})
    response = await call_next(request)
    if protected:
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
    return response


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
    check_auth_ready()
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
