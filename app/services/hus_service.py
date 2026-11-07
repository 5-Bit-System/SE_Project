"""Lazy snapshot for HUS answers; restart/clear cache after rebuilding the package."""

from functools import lru_cache

from app.hus.answering import HUSAnswerer
from app.hus.rag_loader import HUSRAGData
from app.hus.retrieval_config import HUSRetrievalSettings


@lru_cache(maxsize=1)
def get_hus_answerer() -> HUSAnswerer:
    HUSRetrievalSettings.from_env().require_available()
    return HUSAnswerer(HUSRAGData.load_current())
