"""Loopback RAG demo: only chat, pinned package metadata, static UI and source bytes.

Production account/context integration is separate; this app never imports its stack.
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.hus.router import LABELS, current_answerer
from app.hus.router import router as hus_router
from app.services.hus_service import get_hus_answerer

__all__ = ["LABELS", "app", "current_answerer", "get_hus_answerer"]

app = FastAPI(title="HUS RAG — demo local", docs_url=None, redoc_url=None)
STATIC = Path(__file__).resolve().parents[1] / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")
app.include_router(hus_router)


@app.middleware("http")
async def no_store(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def index():
    return FileResponse(STATIC / "hus-rag-demo.html")
