"""P0-1: one pinned release, exact source review and explicit generated opt-in."""

import json
import shutil
from collections import Counter
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.hus.answering import HUSAnswerer
from app.hus.demo import app
from app.hus.rag_loader import HUSRAGData, RAGDataError
from app.hus.retrieval import HUSRAGRetriever
from app.schemas.hus import HUSQuestion
from app.services.hus_service import get_hus_answerer
from tools.compare_hus_releases import compare

ROOT = Path("data/hus/rag")
RELEASE = "hus-data-20261031-v3"
DIGEST = "27bdf3714216292af6d6c6da10e7edd164fa6cf8a286fca7338d18bcb05501f4"


@pytest.fixture(scope="module")
def selected():
    return HUSRAGData.load_current()


@pytest.fixture
def copied(tmp_path):
    pointer = json.loads((ROOT / "CURRENT.json").read_bytes())
    target = tmp_path / "rag"
    path = Path(pointer["release_path"])
    shutil.copytree(ROOT / path, target / path)
    (target / "CURRENT.json").write_bytes((ROOT / "CURRENT.json").read_bytes())
    return target, target / path


def test_current_release_preserves_scope_and_never_loads_F2_chunks_twice(selected):
    assert selected.release_identity["release_id"] == RELEASE
    assert selected.release_identity["release_sha256"] == DIGEST
    majors = ["mathematics", "mathematics_informatics", "computer_science", "data_science"]
    assert sum(len(selected.chunks("f1", major=m)) for m in majors) == 65
    assert sum(len(selected.chunks("f3", major=m, allow_generated=True)) for m in majors) == 870
    assert len(selected._courses) == 290
    assert set(selected._chunks) == {"f1", "f3"}
    assert len(selected.program_scopes()) == 4
    hits = HUSRAGRetriever.load().search("Giới thiệu", dataset="f1", major="data_science")
    assert hits and all(h.chunk.metadata["release_id"] == RELEASE for h in hits)


def test_comparison_receipt_reproduces_and_explains_all_four_removed_splits():
    report = compare(ROOT)
    assert report == json.loads(Path("data/hus/qa/20261102/p01/reconciliation.json").read_bytes())
    assert report["f1"]["selected_units"] == 63 and report["f1"]["unit_ids_equal"]
    assert {(r["source_id"], r["old_count"], r["new_count"]) for r in report["f1"]["resplit_units"]} == {
        ("0dd9aaaeefcbd7d7", 3, 2), ("31b55b4ee6f451a6", 3, 2),
        ("1c16ddf8a6f1f409", 2, 1), ("f7f470e712738589", 2, 1)}
    assert all(t["equal"] for t in report["f2"]["tables"].values())
    assert report["f3"]["generated_fields_unchanged"]


def test_exact_project_signoff_is_imported_without_promoting_other_programs_or_AI(selected):
    assert Counter(c.review_status for c in selected._courses.values()) == {"draft_unverified": 223, "verified": 67}
    for course in selected._courses.values():
        review = course.provenance["catalog_review"]
        assert review["institutional_certification"] is False
        if course.major == "computer_science":
            assert course.review_status == "verified" and review["basis"] == "explicit_user_attestation"
        else:
            assert course.review_status == "draft_unverified"
    f3 = selected.chunks("f3", major="computer_science", allow_generated=True)
    assert all(c.metadata["academic_verified"] is False and c.metadata["review_status"] == "needs_review" for c in f3)


def test_generated_requires_opt_in_at_loader_retrieval_and_answering(selected):
    assert not selected.chunks("f3", major="data_science")
    assert not HUSRAGRetriever(selected).search("MAT3533", dataset="f3", major="data_science")
    answerer = HUSAnswerer(selected)
    base = dict(question="Nội dung MAT3533?", major="data_science", version="QD3569-2023")
    assert answerer.answer(HUSQuestion(**base)).status == "needs_clarification"
    allowed = answerer.answer(HUSQuestion(**base, allow_generated_reference=True))
    assert allowed.status == "answered" and allowed.generated_reference_allowed
    assert allowed.release_id == RELEASE and allowed.release_sha256 == DIGEST
    assert all(c.metadata["release_id"] == RELEASE for c in allowed.citations)
    # One opted-in request cannot change the next request's default.
    assert answerer.answer(HUSQuestion(**base)).status == "needs_clarification"
    official = answerer.answer(HUSQuestion(**(base | {"question": "MAT3533 thi cuối kỳ bao nhiêu phần trăm?"}),
                                           allow_generated_reference=True))
    assert official.status == "no_information" and not official.citations


@pytest.mark.parametrize("failure", ["missing", "hash", "path", "id", "policy", "corrupt_file"])
def test_pointer_and_payload_errors_do_not_fall_back_to_legacy(copied, monkeypatch, failure):
    root, release = copied
    current = json.loads((root / "CURRENT.json").read_bytes())
    if failure == "missing":
        (root / "CURRENT.json").unlink()
    elif failure == "corrupt_file":
        (release / "f1_chunks.jsonl").write_bytes(b"{}\n")
    else:
        key, value = {"hash": ("release_sha256", "0" * 64), "path": ("release_path", "../outside"),
                      "id": ("release_id", "wrong"), "policy": ("generated_reference_requires_opt_in", False)}[failure]
        current[key] = value
        (root / "CURRENT.json").write_text(json.dumps(current), encoding="utf-8")
    monkeypatch.setattr(HUSRAGData, "load", lambda *a, **k: pytest.fail("Unexpected legacy fallback"))
    with pytest.raises(RAGDataError):
        HUSRAGData.load_current(root)


def test_snapshot_does_not_reread_a_changed_pointer_or_source_during_request(copied):
    root, release = copied
    snapshot = HUSRAGData.load_current(root)
    (root / "CURRENT.json").write_text("{}", encoding="utf-8")
    (release / "f1_chunks.jsonl").write_bytes(b"CORRUPTED AFTER SNAPSHOT")
    answerer = HUSAnswerer(snapshot)
    a = answerer.answer(HUSQuestion(question="Giới thiệu ngành", major="data_science"))
    b = answerer.answer(HUSQuestion(question="Số tín chỉ MAT3533?", major="data_science", version="QD3569-2023"))
    assert a.status == b.status == "answered"
    assert a.release_id == b.release_id == RELEASE
    assert a.release_sha256 == b.release_sha256 == DIGEST
    with pytest.raises(RAGDataError):
        HUSRAGData.load_current(root)


def test_no_filesystem_mixing_between_validation_and_adaptation(copied, monkeypatch):
    import app.hus.portable_adapter as module
    root, release = copied
    original = module.validate_release
    def mutate_original_after_validation(snapshot):
        result = original(snapshot)
        (release / "f1_chunks.jsonl").write_bytes(b"CHANGED AFTER VALIDATION")
        return result
    monkeypatch.setattr(module, "validate_release", mutate_original_after_validation)
    data = HUSRAGData.load_current(root)
    assert len(data.chunks("f1", major="data_science")) == 10


def test_legacy_and_qa_files_are_never_read_by_current_adapter(copied):
    root, _ = copied
    for relative in ["manifest.json", "f1/rag_chunks.jsonl", "f2/hus_source.json", "qa/chunks.jsonl"]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"MUST NOT BE PARSED")
    data = HUSRAGData.load_current(root)
    assert data.release_identity["release_sha256"] == DIGEST


def test_http_uses_one_release_and_failed_reload_is_503(copied, monkeypatch):
    root, _ = copied
    original = HUSRAGData.load_current
    monkeypatch.setattr(HUSRAGData, "load_current", lambda: original(root))
    get_hus_answerer.cache_clear()
    try:
        client = TestClient(app)
        body = {"question": "Số tín chỉ MAT3533?", "major": "data_science", "version": "QD3569-2023"}
        a = client.post("/hus/chat", json=body)
        assert a.status_code == 200 and a.json()["hus_answer"]["release_id"] == RELEASE
        (root / "CURRENT.json").write_text("{}", encoding="utf-8")
        cached = client.post("/hus/chat", json=body)
        assert cached.status_code == 200 and cached.json()["hus_answer"]["release_sha256"] == DIGEST
        get_hus_answerer.cache_clear()
        assert client.post("/hus/chat", json=body).status_code == 503
    finally:
        get_hus_answerer.cache_clear()


@pytest.mark.parametrize("value", [1, "true", "false"])
def test_generated_consent_requires_a_json_boolean(value):
    body = {"question": "Nội dung MAT3533?", "major": "data_science",
            "version": "QD3569-2023", "allow_generated_reference": value}
    client = TestClient(app)
    assert client.post("/hus/chat", json=body).status_code == 422
    assert client.post("/hus/chat", json={**body, "question": "Xin chào"}).status_code == 422
