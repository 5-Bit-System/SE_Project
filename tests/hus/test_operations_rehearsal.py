"""Real selector corruption/races and telemetry privacy; no production targets."""

import json

import pytest

from tools.hus_ops_state import (
    check_receipt,
    digest,
    encoded,
    loopback_url,
    rollback,
    transition,
    verify_files,
)
from tools.rehearse_hus_operations import Observations, run


def worker(name):
    return {"instance": name, "base_url": "http://127.0.0.1:8123", "build_sha256": "a" * 64,
            "release_id": "synthetic", "release_sha256": "b" * 64, "registry_sha256": "c" * 64}


def ready(target):
    return {**target, "ready": True}


def receipt(target):
    return {"scope": "local_operational_rehearsal", "production_eligible": False, "status": "pass", "worker": target}


def selector(tmp_path):
    traffic = tmp_path / "traffic"
    traffic.mkdir()
    (traffic / "LOCAL_REHEARSAL_ONLY").write_bytes(b"loopback-only\n")
    pointer = traffic / "ACTIVE_WORKER.json"
    original = encoded({"scope": "local_operational_rehearsal", "worker": worker("blue")})
    pointer.write_bytes(original)
    return pointer, original


@pytest.mark.parametrize("url", ["https://127.0.0.1:8123", "http://example.com", "http://127.0.0.1.evil:8123",
                                  "http://user:password@127.0.0.1:8123", "http://127.0.0.1:8123/path",
                                  "http://127.0.0.1:8123#fragment", "http://127.0.0.1:8123?x=1"])
def test_operational_rehearsal_never_connects_to_external_or_credentialled_url(url):
    with pytest.raises(ValueError):
        loopback_url(url)


def test_activation_and_rollback_restore_exact_selector(tmp_path):
    pointer, original = selector(tmp_path)
    candidate = worker("green")
    result = transition(pointer, candidate, receipt(candidate), digest(original), lambda _: ready(candidate))
    assert json.loads(pointer.read_bytes())["worker"]["instance"] == "green"
    rollback(pointer, digest(original), result["selector_sha256"], lambda _: ready(worker("blue")))
    assert pointer.read_bytes() == original


def test_stale_CAS_and_held_lock_do_not_probe_or_write(tmp_path):
    pointer, original = selector(tmp_path)
    def forbidden_probe(_):
        raise AssertionError("must reject before probing")
    with pytest.raises(ValueError, match="stale"):
        transition(pointer, worker("green"), receipt(worker("green")), "0" * 64, forbidden_probe)
    pointer.with_suffix(".lock").write_bytes(b"held")
    with pytest.raises(ValueError, match="lock"):
        transition(pointer, worker("green"), receipt(worker("green")), digest(original), forbidden_probe)
    assert pointer.read_bytes() == original


def test_unready_or_wrong_build_cannot_activate(tmp_path):
    pointer, original = selector(tmp_path)
    candidate = worker("green")
    for state in [{**ready(candidate), "ready": False}, {**ready(candidate), "build_sha256": "d" * 64}]:
        with pytest.raises(ValueError):
            transition(pointer, candidate, receipt(candidate), digest(original), lambda _, state=state: state)
        assert pointer.read_bytes() == original


def test_production_receipts_and_canonical_CURRENT_are_refused(tmp_path):
    target = worker("green")
    with pytest.raises(ValueError, match="local-only"):
        check_receipt(target, {**receipt(target), "production_eligible": True}, ready(target))
    canonical = tmp_path / "CURRENT.json"
    canonical.write_bytes(b"original")
    with pytest.raises(ValueError, match="dedicated"):
        transition(canonical, target, receipt(target), digest(b"original"), lambda _: ready(target))
    assert canonical.read_bytes() == b"original"


def test_tampered_history_and_unready_rollback_target_preserve_active_worker(tmp_path):
    pointer, original = selector(tmp_path)
    candidate = worker("green")
    result = transition(pointer, candidate, receipt(candidate), digest(original), lambda _: ready(candidate))
    active = pointer.read_bytes()
    with pytest.raises(ValueError, match="not ready"):
        rollback(pointer, digest(original), result["selector_sha256"], lambda _: {**ready(worker("blue")), "ready": False})
    (pointer.parent / "history" / f"{digest(original)}.json").write_bytes(b"changed")
    with pytest.raises(ValueError, match="history"):
        rollback(pointer, digest(original), result["selector_sha256"], lambda _: ready(worker("blue")))
    assert pointer.read_bytes() == active


def test_changed_artifact_bytes_cannot_be_declared_ready(tmp_path):
    (tmp_path / "source.pdf").write_bytes(b"new bytes")
    with pytest.raises(ValueError, match="changed"):
        verify_files(tmp_path, {"source.pdf": digest(b"old bytes")})


def test_metrics_and_events_never_store_raw_path_or_prompt(tmp_path):
    log = tmp_path / "events.jsonl"
    observation = Observations("blue", worker("blue"), log)
    observation.record("GET", "/hus/sources/private-question-student-id?secret=example", 503, .025, "random-id")
    event = log.read_text()
    assert not any(secret in event for secret in ["private-question", "student-id", "example"])
    assert json.loads(event)["route"] == "source"
    metrics = observation.metrics()
    assert metrics["service_5xx_ratio"] == 1 and metrics["http_counts"]["source:503"] == 1


def test_run_rejects_writing_into_source_before_mkdir(tmp_path, monkeypatch):
    def forbidden_mkdir(*args, **kwargs):
        raise AssertionError("must reject before write")
    monkeypatch.setattr(type(tmp_path), "mkdir", forbidden_mkdir)
    with pytest.raises(ValueError, match="backups"):
        run(tmp_path)
