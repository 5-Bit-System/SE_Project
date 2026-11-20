"""Lazy snapshot for HUS answers; restart/clear cache after rebuilding the package."""

from functools import lru_cache
import os
from pathlib import Path

from app.hus.answering import HUSAnswerer
from app.hus.rag_loader import HUSRAGData
from app.hus.retrieval_config import HUSRetrievalSettings


@lru_cache(maxsize=1)
def get_hus_answerer() -> HUSAnswerer:
    settings = HUSRetrievalSettings.from_env()
    policy = os.environ.get('HUS_ANSWER_POLICY', 'legacy')
    if policy not in {'legacy', 'focused'}:
        raise ValueError('Invalid answer policy')
    settings.require_available()
    # An explicit preview root never changes shared CURRENT. Restart/clear this
    # cache after changing the process setting, just as after a snapshot change.
    root = os.environ.get('HUS_RAG_ROOT')
    data = HUSRAGData.load_current(Path(root)) if root else HUSRAGData.load_current()
    if settings.mode == 'lexical':
        return HUSAnswerer(data, answer_policy=policy)
    from app.hus.vector_query import HUSVectorRetriever

    def runtime_factory():
        from app.hus.vector_runtime import LocalVectorRuntime
        return LocalVectorRuntime(settings, data)

    vector = HUSVectorRetriever(data, runtime_factory=runtime_factory)
    if settings.mode == 'hybrid':
        from app.hus.hybrid_retrieval import HUSHybridRetriever
        return HUSAnswerer(data, retriever=HUSHybridRetriever(data, vector=vector), answer_policy=policy)
    return HUSAnswerer(data, retriever=vector, answer_policy=policy)



@lru_cache(maxsize=1)
def _workspace_answerer(answerer: HUSAnswerer) -> HUSAnswerer:
    from app.hus.workspace_answering import WorkspaceAnswerer

    workspace = WorkspaceAnswerer(answerer.data, retriever=answerer.retriever)
    workspace.citation_resolver = answerer.citation_resolver
    return workspace


def workspace_answerer(answerer: HUSAnswerer) -> HUSAnswerer:
    if isinstance(answerer, HUSAnswerer) and answerer.answer_policy == 'legacy':
        return _workspace_answerer(answerer)
    return answerer
