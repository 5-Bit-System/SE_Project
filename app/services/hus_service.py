"""Lazy snapshot for HUS answers; restart/clear cache after rebuilding the package."""

from functools import lru_cache

from app.hus.answering import HUSAnswerer
from app.hus.rag_loader import HUSRAGData


@lru_cache(maxsize=1)
def get_hus_answerer() -> HUSAnswerer:
    return HUSAnswerer(HUSRAGData.load_current())
