"""HUS RAG router.

Exposes question answering, retrieval context, catalog discovery, and source
document streaming for HUS curriculum data.
"""

from __future__ import annotations

import sys
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response

from app.hus.chat import HUSChatReply, chat
from app.hus.question_catalog import question_catalog
from app.hus.rag_loader import RAGDataError
from app.hus.source_response import source_response
from app.schemas.hus import HUSMajor, HUSQuestion, HUSRetrievalBundle
from app.services import hus_service
from app.services.hus_service import get_hus_answerer

router = APIRouter(prefix="/hus", tags=["hus"])

LABELS: dict[str, str] = {
    "mathematics": "Toán học",
    "mathematics_informatics": "Toán tin",
    "computer_science": "Khoa học máy tính và thông tin",
    "data_science": "Khoa học dữ liệu",
}


def current_answerer():
    try:
        demo_mod = sys.modules.get("app.hus.demo")
        if demo_mod and getattr(demo_mod, "get_hus_answerer", None) not in (None, get_hus_answerer):
            return demo_mod.get_hus_answerer()
        hus_api_mod = sys.modules.get("app.api.hus")
        if hus_api_mod and getattr(hus_api_mod, "get_hus_answerer", None) not in (None, get_hus_answerer):
            return hus_api_mod.get_hus_answerer()
        hus_router_mod = sys.modules.get("app.hus.router")
        if hus_router_mod and getattr(hus_router_mod, "get_hus_answerer", None) not in (None, get_hus_answerer):
            return hus_router_mod.get_hus_answerer()
        return hus_service.get_hus_answerer()
    except (RAGDataError, OSError, ValueError):
        raise HTTPException(503, "Dữ liệu hỏi đáp chưa sẵn sàng.") from None


@router.get("/config")
def config(response: Response) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    answerer = current_answerer()
    scopes = sorted(set(answerer.programs.values()))
    if len({major for major, _ in scopes}) != len(scopes):
        raise HTTPException(503, "Phiên bản chương trình chưa xác định duy nhất.")
    return {
        "majors": [{"id": major, "label": LABELS[major], "version": version} for major, version in scopes],
        **answerer.data.release_identity,
    }


@router.post("/chat", response_model=HUSChatReply)
def reply(request: HUSQuestion, response: Response) -> HUSChatReply:
    response.headers["Cache-Control"] = "no-store"
    try:
        return chat(request, current_answerer())
    except RAGDataError:
        raise HTTPException(503, "Dữ liệu hỏi đáp chưa sẵn sàng.") from None


@router.post("/retrieve", response_model=HUSRetrievalBundle)
def retrieve(
    request: HUSQuestion,
    response: Response,
    top_k: int = Query(default=5, ge=1, le=20),
) -> HUSRetrievalBundle:
    response.headers["Cache-Control"] = "no-store"
    try:
        return current_answerer().retrieve_context(request, top_k=top_k)
    except RAGDataError:
        raise HTTPException(503, "Dữ liệu hỏi đáp chưa sẵn sàng.") from None


@router.get("/questions")
def questions(
    major: HUSMajor,
    response: Response,
    version: str = Query(min_length=1, max_length=80),
) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store"
    answerer = current_answerer()
    if (major, version) not in set(answerer.programs.values()):
        raise HTTPException(404, "Không có ngành và phiên bản chương trình này.")
    try:
        return question_catalog(answerer.data, major=major, version=version)
    except RAGDataError:
        raise HTTPException(503, "Danh mục câu hỏi chưa sẵn sàng.") from None


@router.api_route("/sources/{source_id}", methods=["GET", "HEAD"])
def source(
    request: Request,
    source_id: str,
    page: int | None = Query(default=None, ge=1),
) -> Response:
    return source_response(request, current_answerer().citation_resolver.assets, source_id, page)
