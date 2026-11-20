"""HUS RAG API router.

Exposes question answering, retrieval context, catalog discovery, and source
document streaming for HUS curriculum data in the main application.
"""

from __future__ import annotations

from app.hus.router import (
    LABELS,
    current_answerer,
    get_hus_answerer,
    router,
)

__all__ = ["LABELS", "current_answerer", "get_hus_answerer", "router"]
