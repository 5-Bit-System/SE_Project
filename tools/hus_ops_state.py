"""Loopback-only operational rehearsal state; never selects a production release."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def loopback_url(url):
    parts = urlsplit(url)
    require(parts.scheme == "http" and parts.hostname == "127.0.0.1" and parts.port is not None
            and parts.username is None and parts.password is None and not parts.path
            and not parts.query and not parts.fragment and not any(c.isspace() for c in url),
            "rehearsal target must be a plain IPv4 loopback HTTP origin")
    return url


def atomic_write(path, raw):
    path = Path(path)
    descriptor, name = tempfile.mkstemp(prefix=".hus-ops-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def verify_files(root, pins):
    root = Path(root).resolve()
    for relative, sha in pins.items():
        path = (root / relative).resolve()
        require(path.is_relative_to(root), "build path escapes artifact")
        require(digest(path.read_bytes()) == sha, "build file changed: " + relative)


def check_receipt(candidate, receipt, ready):
    require(receipt.get("scope") == "local_operational_rehearsal"
            and receipt.get("production_eligible") is False and receipt.get("status") == "pass",
            "a local-only passed operational receipt is required")
    loopback_url(candidate["base_url"])
    require(all(isinstance(candidate.get(key), str) and re.fullmatch(r"[a-f0-9]{64}", candidate[key])
                for key in ["build_sha256", "release_sha256", "registry_sha256"])
            and isinstance(candidate.get("instance"), str) and bool(candidate["instance"])
            and isinstance(candidate.get("release_id"), str) and bool(candidate["release_id"]),
            "candidate identity is incomplete")
    require(receipt.get("worker") == candidate, "receipt does not bind this worker")
    require(ready.get("ready") is True, "candidate is not ready")
    for name in ("instance", "build_sha256", "release_id", "release_sha256", "registry_sha256"):
        require(ready.get(name) == candidate.get(name), "candidate identity differs from readiness")


@contextmanager
def locked(pointer):
    lock = pointer.with_suffix(".lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError("another local transition holds the lock") from None
    try:
        os.close(descriptor)
        yield
    finally:
        lock.unlink(missing_ok=True)


def rehearsal_pointer(pointer):
    pointer = Path(pointer).resolve()
    # Both location and a capability marker must be explicit. No canonical CURRENT.
    require(pointer.name == "ACTIVE_WORKER.json" and pointer.parent.name == "traffic"
            and (pointer.parent / "LOCAL_REHEARSAL_ONLY").read_bytes() == b"loopback-only\n",
            "requires a dedicated local traffic selector")
    return pointer


def transition(pointer, candidate, receipt, expected, probe):
    pointer = rehearsal_pointer(pointer)
    with locked(pointer):
        old = pointer.read_bytes()
        require(digest(old) == expected, "stale expected selector; no transition")
        check_receipt(candidate, receipt, probe(loopback_url(candidate["base_url"])))
        require(digest(pointer.read_bytes()) == expected, "selector changed during preflight")
        history = pointer.parent / "history"
        history.mkdir(exist_ok=True)
        saved = history / f"{expected}.json"
        if saved.exists():
            require(saved.read_bytes() == old, "rollback history changed")
        else:
            atomic_write(saved, old)
        new = encoded({"scope": "local_operational_rehearsal", "worker": candidate,
                       "previous_sha256": expected, "receipt_sha256": digest(encoded(receipt))})
        atomic_write(pointer, new)
    return {"action": "activate_local_worker", "previous_sha256": expected, "selector_sha256": digest(new)}


def rollback(pointer, previous, expected, probe):
    pointer = rehearsal_pointer(pointer)
    with locked(pointer):
        old = pointer.read_bytes()
        require(digest(old) == expected, "stale expected selector; no rollback")
        require(len(previous) == 64 and all(c in "0123456789abcdef" for c in previous), "invalid history hash")
        require(json.loads(old).get("previous_sha256") == previous, "must restore the immediate previous worker")
        raw = (pointer.parent / "history" / f"{previous}.json").read_bytes()
        require(digest(raw) == previous, "rollback history changed")
        selection = json.loads(raw)
        require(selection.get("scope") == "local_operational_rehearsal", "history is not a rehearsal")
        target = selection["worker"]
        ready = probe(loopback_url(target["base_url"]))
        check_receipt(target, {"scope": selection["scope"], "production_eligible": False,
                              "status": "pass", "worker": target}, ready)
        require(digest(pointer.read_bytes()) == expected, "selector changed during rollback preflight")
        atomic_write(pointer, raw)
    return {"action": "rollback_local_worker", "selector_sha256": previous}
