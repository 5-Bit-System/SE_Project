"""One fail-closed review gate for corpus, chunking, and index export."""

from datetime import date, datetime
import hashlib

from app.hus.models import HUSDocument, ReviewDecision
from app.hus.cleaning import infer_major
from app.hus.metadata import metadata_for
from app.hus.models import MajorCategory


class ReviewGateError(ValueError):
    """The document is not approved for the requested export."""


def source_digest(raw: bytes, encoding: str) -> str:
    if encoding == "utf8-lf":
        raw = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode()
    elif encoding != "binary":
        raise ReviewGateError("Unknown source checksum encoding")
    return hashlib.sha256(raw).hexdigest()


def require_review(
    document: HUSDocument, decision: ReviewDecision | None, source_sha256: str | None,
    *, source_encoding: str = "binary", as_of: date | None = None,
) -> ReviewDecision:
    """Validate current decisions, not a cached review embedded in an old index record."""
    if decision is None:
        raise ReviewGateError("Missing review decision")
    applicability = metadata_for(document)
    if (infer_major(document.title, document.url, document.content) == MajorCategory.OUT_OF_SCOPE
        or applicability.major.proposed == "out_of_scope" or applicability.major.verified == "out_of_scope"):
        raise ReviewGateError("Source is outside the four supported HUS majors")
    # Revalidate even if a caller mutated an existing model after creation.
    decision = ReviewDecision.model_validate(decision.model_dump())
    for name in ("validity_status", "effective_from", "effective_to"):
        verified = getattr(applicability, name).verified
        if verified != "unknown" and verified != getattr(decision, name):
            raise ReviewGateError(f"Review and verified applicability disagree: {name}")
    if document.status.value != "active" or decision.status != "include":
        raise ReviewGateError("Only active documents with include review may be exported")
    if decision.source_url != document.url:
        raise ReviewGateError("Review belongs to a different source URL")
    actual_hash = hashlib.sha256(document.content.encode()).hexdigest()
    if document.content_hash != actual_hash or decision.content_hash != actual_hash:
        raise ReviewGateError("Stale review content hash")
    if (
        not source_sha256 or decision.reviewed_source_sha256 != source_sha256
        or decision.source_checksum_encoding != source_encoding
        or not (decision.reviewer or "").strip() or not decision.reviewed_at
        or not (decision.evidence_locator or "").strip()
    ):
        raise ReviewGateError("Include lacks timestamped, hash-bound source review evidence")
    if as_of is not None and datetime.fromisoformat(
        decision.reviewed_at.replace("Z", "+00:00")
    ).date() > as_of:
        raise ReviewGateError("Review is later than the requested as_of date")
    if as_of is not None:
        from app.hus.metadata import METADATA_FIELDS

        for name in METADATA_FIELDS:
            field = getattr(applicability, name)
            if field.verified != "unknown" and datetime.fromisoformat(
                field.reviewed_at.replace("Z", "+00:00")
            ).date() > as_of:
                raise ReviewGateError(f"Metadata review is later than as_of: {name}")
    if decision.usage_scope == "current":
        if as_of is None:
            raise ReviewGateError("Current usage requires an explicit as_of date")
        if not decision.effective_from:
            raise ReviewGateError("Current usage requires effective_from evidence")
        if as_of < date.fromisoformat(decision.effective_from) or (
            decision.effective_to and as_of > date.fromisoformat(decision.effective_to)
        ):
            raise ReviewGateError("Document is not effective on as_of")
    return decision
