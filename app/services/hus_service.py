"""Lazy snapshot for HUS answers; restart/clear cache after rebuilding the package."""

from functools import lru_cache

from app.hus.answering import HUSAnswerer
from app.hus.rag_loader import HUSRAGData
from app.hus.retrieval_config import HUSRetrievalSettings


@lru_cache(maxsize=1)
def get_hus_answerer() -> HUSAnswerer:
    settings = HUSRetrievalSettings.from_env()
    settings.require_available()
    data = HUSRAGData.load_current()  # Canonical errors must never become vector fallback.
    if settings.mode == 'lexical':
        return HUSAnswerer(data)
    from app.hus.vector_query import HUSVectorRetriever

    def runtime_factory():
        from app.hus.vector_runtime import LocalVectorRuntime
        return LocalVectorRuntime(settings, data)

    vector = HUSVectorRetriever(data, runtime_factory=runtime_factory)
    if settings.mode == 'hybrid':
        from app.hus.hybrid_retrieval import HUSHybridRetriever
        return HUSAnswerer(data, retriever=HUSHybridRetriever(data, vector=vector))
    return HUSAnswerer(data, retriever=vector)
