"""Loopback RAG demo: only chat, pinned package metadata, static UI and source bytes.

Production account/context integration is separate; this app never imports its stack.
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.hus.chat import HUSChatReply, chat
from app.hus.question_catalog import question_catalog
from app.hus.rag_loader import RAGDataError
from app.hus.source_response import source_response
from app.schemas.hus import HUSMajor, HUSQuestion, HUSRetrievalBundle
from app.services.hus_service import get_hus_answerer

app = FastAPI(title="HUS RAG — demo local", docs_url=None, redoc_url=None)
STATIC = Path(__file__).resolve().parents[1] / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")
LABELS = {"mathematics": "Toán học", "mathematics_informatics": "Toán tin",
          "computer_science": "Khoa học máy tính và thông tin", "data_science": "Khoa học dữ liệu"}


def current_answerer():
    try:
        return get_hus_answerer()
    except (RAGDataError, OSError, ValueError):
        raise HTTPException(503, "Dữ liệu hỏi đáp chưa sẵn sàng.") from None


@app.middleware("http")
async def no_store(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def index():
    return FileResponse(STATIC / "hus-rag-demo.html")


@app.get("/hus/config")
def config():
    answerer = current_answerer()
    scopes = sorted(set(answerer.programs.values()))
    if len({major for major, _ in scopes}) != len(scopes):
        raise HTTPException(503, "Phiên bản chương trình chưa xác định duy nhất.")
    return {"majors": [{"id": major, "label": LABELS[major], "version": version} for major, version in scopes],
            **answerer.data.release_identity}


@app.post("/hus/chat", response_model=HUSChatReply)
def reply(request: HUSQuestion):
    try:
        return chat(request, current_answerer())
    except RAGDataError:
        raise HTTPException(503, "Dữ liệu hỏi đáp chưa sẵn sàng.") from None


@app.post("/hus/retrieve", response_model=HUSRetrievalBundle)
def retrieve(request: HUSQuestion, top_k: int = Query(default=5, ge=1, le=20)):
    try:
        return current_answerer().retrieve_context(request, top_k=top_k)
    except RAGDataError:
        raise HTTPException(503, "Dữ liệu hỏi đáp chưa sẵn sàng.") from None


@app.get("/hus/questions")
def questions(major: HUSMajor, version: str = Query(min_length=1, max_length=80)):
    answerer = current_answerer()
    if (major, version) not in set(answerer.programs.values()):
        raise HTTPException(404, "Không có ngành và phiên bản chương trình này.")
    try:
        return question_catalog(answerer.data, major=major, version=version)
    except RAGDataError:
        raise HTTPException(503, "Danh mục câu hỏi chưa sẵn sàng.") from None


@app.api_route("/hus/sources/{source_id}", methods=["GET", "HEAD"])
def source(request: Request, source_id: str, page: int | None = Query(default=None, ge=1)) -> Response:
    return source_response(request, current_answerer().citation_resolver.assets, source_id, page)
