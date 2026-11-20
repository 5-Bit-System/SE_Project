"""Complete synthetic repository-review evidence for source version tests."""
from app.crawler.document_review_service import document_review_fingerprint

REVIEWER_ID = "57e9a52b-7365-4fe2-b9ce-1320ef48dc02"


def snapshot_decision(document, status="approved", reason="Synthetic reviewed source"):
    return {
        "doc_id": document["id"],
        "url": document["url"],
        "content_hash": document["content_hash"],
        "title": document["title"],
        "review_status": status,
        "review_reason": reason,
        "reviewer_id": REVIEWER_ID,
        "reviewed_at": "2026-11-09T01:00:00+00:00",
        "review_fingerprint": document_review_fingerprint(document),
    }
