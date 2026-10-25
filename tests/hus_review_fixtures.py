"""Explicit approvals for invented HUS test inputs only; never product review evidence."""

from app.hus.models import HUSDocument, ReviewDecision
from app.hus.review import source_digest


def approved_review(document: HUSDocument, raw: bytes) -> ReviewDecision:
    return ReviewDecision(
        content_hash=document.content_hash, source_url=document.url,
        status="include", reason="Synthetic test source checked",
        reviewer="synthetic-reviewer", reviewed_at="2026-10-26T00:00:00Z",
        evidence_locator="Synthetic fixture body; whole document",
        reviewed_source_sha256=source_digest(raw, "binary"),
    )
