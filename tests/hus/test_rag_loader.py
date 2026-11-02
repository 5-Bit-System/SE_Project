"""Synthetic loader contracts: identities, provenance, isolation and package integrity."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from app.hus.rag_loader import HUSRAGData, RAGDataError


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode()


def write_package(root, files):
    entries = []
    for name, raw in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        entries.append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                        "origin": "synthetic-test-only/no-external-source-required"})
    (root / "manifest.json").write_bytes(json_bytes({"files": entries, "active_release": False}))


@pytest.fixture
def package(tmp_path):
    # Same code in two majors and two versions; none is an academic source.
    identities = [(1, "7460101", "mathematics", "TEST-A", 2022),
                  (2, "7460108", "data_science", "TEST-B", 2022),
                  (3, "7460101", "mathematics", "TEST-OLD", 2021)]
    tables = {k: [] for k in ("courses", "curricula", "curriculum_courses",
                             "course_prerequisites", "official_curriculum_groups",
                             "official_curriculum_entries")}
    tables["courses"] = [{"course_code": code, "course_name": "Môn giả lập — kiểm thử", "credits": 3}
                         for code in ("TST0001", "TST9999")]
    bundle = {"source": "Synthetic fixture, not academic data", "tables": tables,
              "course_metadata": [], "metadata_source_manifest": [],
              "metadata_source_archive": {"scope": "synthetic only"},
              "prerequisite_pdf_review": {"unresolved_codes": ["EXT9999"],
                                          "conflicting_courses": [{"major_code": "7460101", "course_code": "TST0001"}]}}
    f3 = []
    for cid, code, major, version, cohort in identities:
        pid = f"test_{code.lower()}_{cohort}"
        tables["curricula"].append({"curriculum_id": cid, "major_code": code,
                                    "curriculum_version": version, "cohort_year": cohort})
        tables["curriculum_courses"].append({"curriculum_id": cid, "course_code": "TST0001",
                                             "course_group": "I", "course_type": "required"})
        tables["course_prerequisites"].extend(
            {"curriculum_id": cid, "course_code": "TST0001", "group_no": group,
             "prerequisite_course_code": other}
            for group, other in [(1, "EXT9999"), (1, "TST9999"), (2, "TST0002")])
        for group in ("I", "II"):
            tables["official_curriculum_groups"].append(
                {"curriculum_id": cid, "group_key": group, "group_title": "Synthetic"})
            tables["official_curriculum_entries"].append(
                {"curriculum_id": cid, "course_code": "TST0001", "group_key": group,
                 "pdf_document": f"test-{cid}.pdf", "pdf_page": cid,
                 "prerequisite_source_text": "EXT9999/TST9999; TST0002",
                 "prerequisite_parse_status": "unresolved_external"})
        bundle["course_metadata"].append({"program_id": pid, "code": "TST0001",
                                          "values": {"hours": None}, "field_evidence": {"hours": []}})
        bundle["metadata_source_manifest"].append(
            {"decision": version, "cohort_year": cohort, "source_ref": f"test-{cid}.pdf",
             "status": "draft_unverified", "scope": ["hours"]})
        for field in ("content", "objectives", "suggested_assessment"):
            f3.append({"chunk_id": f"f3-{cid}-{field}", "major": major, "program_id": pid,
                       "curriculum_version": version, "cohort_year": cohort,
                       "course_code": "TST0001", "field": field, "text": "Synthetic warning\nNội dung thử",
                       "content_origin": "generated", "academic_verified": False,
                       "review_status": "needs_review", "disclosure_required": True,
                       "usage_scope": "reference_only", "warning": "Synthetic warning",
                       "citation_label": "F3 do AI sinh — TST0001", "locator": {"field": field},
                       "provenance": {"source": "synthetic"}})
    f1 = []
    for i, version, status, variant in [(1, "unknown", "include", "unknown"),
                                       (2, "2015", "include_markdown", "standard")]:
        f1.append({"chunk_id": f"f1-{i}", "text": "Trích dẫn thử — tiếng Việt", "major": "mathematics",
                   "program_version": version, "program_variant": variant, "admission_cohort": "unknown",
                   "review_status": status, "review": {"status": status, "reviewer": "test reviewer"},
                   "usage_scope": "descriptive", "answer_eligible": True,
                   "source_url": "https://example.test/source", "source_quote": "Trích dẫn thử",
                   "locator": {"start_char": 0, "end_char": 13}, "raw_original_verified": False,
                   "academic_verified": False, "field": "objectives"})
    files = {"f1/rag_chunks.jsonl": b"".join(map(json_bytes, f1)),
             "f3/rag_chunks.jsonl": b"".join(map(json_bytes, f3)),
             "f2/hus_source.json": json_bytes(bundle),
             "f2/source_comparison.json": json_bytes({"source": {"url": "https://example.test/f2"}}),
             "f1/pending_F1_sections.jsonl": b""}
    write_package(tmp_path, files)
    return tmp_path, files


def test_f1_preserves_original_metadata_and_filters_unknown_versions(package):
    root, files = package
    data = HUSRAGData.load(root)
    chunks = data.chunks("f1", major="mathematics")
    assert len(chunks) == 2
    for chunk, original in zip(chunks, map(json.loads, files["f1/rag_chunks.jsonl"].splitlines())):
        assert {**chunk.metadata, "text": chunk.text} == original
        assert chunk.package_sha256 == hashlib.sha256(files[chunk.package_path]).hexdigest()
    selected = data.chunks("f1", major="mathematics", version="2015", program_variant="standard")
    assert [c.chunk_id for c in selected] == ["f1-2"]
    assert selected[0].metadata["review_status"] == "include_markdown"
    assert not selected[0].metadata["raw_original_verified"]
    assert not data.chunks("f1", major="data_science")
    assert not data.chunks("f1", major="mathematics", version="TEST-A")
    assert not data.chunks("f1", major="mathematics", course_code="TST0001")


def test_f3_requires_exact_major_version_and_preserves_warning_and_provenance(package):
    root, files = package
    data = HUSRAGData.load(root)
    chunks = data.chunks("f3", major="mathematics", version="TEST-A", course_code=" tst0001 ", allow_generated=True)
    assert len(chunks) == 3
    assert all(c.metadata["warning"] == "Synthetic warning" for c in chunks)
    originals = {r["chunk_id"]: r for r in map(json.loads, files["f3/rag_chunks.jsonl"].splitlines())}
    assert all({**c.metadata, "text": c.text} == originals[c.chunk_id] for c in chunks)
    assert len(data.chunks("f3", major="mathematics", version="TEST-OLD", field="content", allow_generated=True)) == 1
    assert not data.chunks("f3", major="mathematics", version="TEST-B")


def test_f2_preserves_duplicate_rows_AND_OR_groups_unknowns_and_conflicts(package):
    root, _ = package
    data = HUSRAGData.load(root)
    course = data.get_f2_course("tst0001", major="mathematics", version="TEST-A")
    assert course.review_status == "draft_unverified"
    assert len(course.source_rows) == len(course.groups) == 2
    assert [p["group_no"] for p in course.prerequisites] == [1, 1, 2]
    assert course.unresolved_prerequisites == ("EXT9999",)
    assert course.has_prerequisite_conflict
    assert course.course_metadata["values"]["hours"] is None
    assert course.provenance["source_row_pointers"] == ["/tables/official_curriculum_entries/0",
                                                       "/tables/official_curriculum_entries/1"]
    old = data.get_f2_course("TST0001", major="mathematics", version="TEST-OLD")
    assert old.curriculum["cohort_year"] == 2021
    ds = data.get_f2_course("TST0001", major="data_science", version="TEST-B")
    assert not ds.has_prerequisite_conflict
    assert not data.get_f2_course("TST0001", major="mathematics", version="TEST-B")
    assert not data.get_f2_course("TST9999", major="mathematics", version="TEST-A")


def test_returned_metadata_cannot_mutate_loaded_snapshot(package):
    root, _ = package
    data = HUSRAGData.load(root)
    data.chunks("f1", major="mathematics")[0].metadata["review"]["status"] = "exclude"
    course = data.get_f2_course("TST0001", major="mathematics", version="TEST-A")
    course.source_rows[0]["pdf_page"] = 999
    data.manifest["files"].clear()
    assert data.chunks("f1", major="mathematics")[0].metadata["review"]["status"] == "include"
    assert data.get_f2_course("TST0001", major="mathematics", version="TEST-A").source_rows[0]["pdf_page"] == 1
    assert data.manifest["files"]


@pytest.mark.parametrize("failure", ["missing", "hash", "empty", "traversal", "duplicate_path"])
def test_manifest_failures_are_explicit(package, failure):
    root, _ = package
    path = root / "f1/rag_chunks.jsonl"
    if failure == "missing":
        path.unlink()
    elif failure == "hash":
        path.write_bytes(b"{}\n")
    elif failure == "empty":
        (root / "f1/pending_F1_sections.jsonl").unlink()
    else:
        manifest = json.loads((root / "manifest.json").read_bytes())
        if failure == "traversal":
            manifest["files"][0]["path"] = "../outside.jsonl"
        else:
            manifest["files"].append(deepcopy(manifest["files"][0]))
        (root / "manifest.json").write_bytes(json_bytes(manifest))
    with pytest.raises(RAGDataError):
        HUSRAGData.load(root)


@pytest.mark.parametrize("failure", ["withdrawn_f1", "duplicate_chunk", "verified_f3", "foreign_f3",
                                     "duplicate_f2", "missing_f2_source", "dangling_f2", "invalid_json"])
def test_rehashed_package_still_checks_semantic_consistency(package, failure):
    root, files = package
    if failure in {"withdrawn_f1", "duplicate_chunk"}:
        name = "f1/rag_chunks.jsonl"
        rows = list(map(json.loads, files[name].splitlines()))
        if failure == "withdrawn_f1":
            rows[0]["review"]["status"] = "exclude"
        else:
            rows.append(deepcopy(rows[0]))
        files[name] = b"".join(map(json_bytes, rows))
    elif failure in {"verified_f3", "foreign_f3"}:
        name = "f3/rag_chunks.jsonl"
        rows = list(map(json.loads, files[name].splitlines()))
        rows[0]["academic_verified" if failure == "verified_f3" else "major"] = (
            True if failure == "verified_f3" else "data_science")
        files[name] = b"".join(map(json_bytes, rows))
    elif failure == "invalid_json":
        files["f1/rag_chunks.jsonl"] = b"{\n"
    else:
        name = "f2/hus_source.json"
        bundle = json.loads(files[name])
        if failure == "duplicate_f2":
            bundle["tables"]["curriculum_courses"].append(deepcopy(bundle["tables"]["curriculum_courses"][0]))
        elif failure == "missing_f2_source":
            bundle["tables"]["official_curriculum_entries"] = [
                e for e in bundle["tables"]["official_curriculum_entries"] if e["curriculum_id"] != 1]
        else:
            bundle["tables"]["course_prerequisites"][0]["curriculum_id"] = 999
        files[name] = json_bytes(bundle)
    write_package(root, files)
    with pytest.raises(RAGDataError):
        HUSRAGData.load(root)


@pytest.mark.parametrize("major", ["unknown", "general", "out_of_scope", "7460101"])
def test_unknown_major_never_falls_back_to_another_catalog(package, major):
    root, _ = package
    data = HUSRAGData.load(root)
    with pytest.raises(RAGDataError):
        data.get_f2_course("TST0001", major=major, version="TEST-A")
    with pytest.raises(RAGDataError):
        data.chunks("f1", major=major)


def test_current_handoff_loads_without_modifying_dataset_files():
    root = Path("data/hus/rag")
    manifest_before = (root / "manifest.json").read_bytes()
    data = HUSRAGData.load(root)
    majors = ("mathematics", "mathematics_informatics", "computer_science", "data_science")
    assert sum(len(data.chunks("f1", major=m)) for m in majors) == 69
    assert sum(len(data.chunks("f3", major=m, allow_generated=True)) for m in majors) == 870
    rows = json.loads((root / "f2/hus_source.json").read_bytes())["tables"]
    for c, major in zip(sorted(rows["curricula"], key=lambda r: r["curriculum_id"]), majors):
        members = [m for m in rows["curriculum_courses"] if m["curriculum_id"] == c["curriculum_id"]]
        for membership in members:
            course = data.get_f2_course(membership["course_code"], major=major, version=c["curriculum_version"])
            assert course and course.review_status == "draft_unverified"
    assert data.get_f2_course("MAT3325", major="mathematics", version="QD3565-2023").has_prerequisite_conflict
    assert (root / "manifest.json").read_bytes() == manifest_before
