"""Single-event-loop, session-scoped sync receipts. Not a durable/exactly-once queue."""

import hashlib
import re

MAX_ACTIVE_JOBS = 40


def key_hash(headers):
    values = headers.getlist("idempotency-key")
    if not values:
        return None  # Legacy callers retain their existing contract.
    if len(values) != 1 or not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", values[0]):
        raise ValueError("invalid_idempotency_key")
    return hashlib.sha256(values[0].encode("ascii")).hexdigest()


def replay(jobs, session, request_key):
    if request_key is not None:
        for job_id, job in jobs.items():
            if (job.get("request_key") == request_key and job.get("session") is session
                    and job.get("owner") == session.owner):
                return response(job_id, job)
    return None


def mark(job, state, phase, percent=None):
    job.update(state=state, phase=phase)
    if percent is not None:
        job["progress_percent"] = percent


def response(job_id, job):
    """Allowlist on-wire fields; the percent is a milestone, not estimated duration."""
    return {"id": job_id, "state": job["state"], "phase": job["phase"],
            "progress_percent": job.get("progress_percent", 0),
            "error": job.get("error"), "result": job.get("result")}
