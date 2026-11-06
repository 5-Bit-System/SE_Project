"""Retrieval contracts use invented data; real-package checks do not verify academics."""

import hashlib
import json
import unicodedata
from copy import deepcopy
from pathlib import Path

import pytest

from app.hus.rag_loader import MAJOR_CODES, HUSRAGData, RAGDataError
from app.hus.retrieval import FIELD_LABELS, HUSRAGRetriever


def _json(value):
    return (json.dumps(value, ensure_ascii=False) + "\n").encode()


def _write(root, files):
    entries = []
    for name, raw in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        entries.append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                        "origin": "../qa/not-a-second-input.jsonl"})
    (root / "manifest.json").write_bytes(_json({"files": entries}))


@pytest.fixture
def corpus(tmp_path):
    root = tmp_path / "rag"
    tables = {name: [] for name in ("courses", "curricula", "curriculum_courses", "course_prerequisites",
                                    "official_curriculum_groups", "official_curriculum_entries")}
    bundle = {"source": "synthetic test only", "tables": tables, "course_metadata": [],
              "metadata_source_manifest": [], "metadata_source_archive": {},
              "prerequisite_pdf_review": {"unresolved_codes": [], "conflicting_courses": []}}
    for code, title in [("TST0001", "Học máy"), ("TST0002", "Mạng máy tính")]:
        tables["courses"].append({"course_code": code, "course_name": title, "credits": 3})
    f3 = []
    for cid, major_code, major, version, cohort in [
        (1, "7460101", "mathematics", "TEST-A", 2022),
        (2, "7460108", "data_science", "TEST-B", 2022),
        (3, "7460101", "mathematics", "TEST-OLD", 2021),
    ]:
        pid = f"test_{major_code}_{cohort}"
        tables["curricula"].append({"curriculum_id": cid, "major_code": major_code,
                                    "curriculum_version": version, "cohort_year": cohort})
        tables["official_curriculum_groups"].append({"curriculum_id": cid, "group_key": "I"})
        bundle["metadata_source_manifest"].append({"decision": version, "cohort_year": cohort,
                                                   "source_ref": "synthetic.pdf", "status": "draft_unverified"})
        for course in tables["courses"][:2 if cid == 1 else 1]:
            code = course["course_code"]
            tables["curriculum_courses"].append({"curriculum_id": cid, "course_code": code, "course_group": "I"})
            tables["official_curriculum_entries"].append(
                {"curriculum_id": cid, "course_code": code, "group_key": "I", "pdf_document": "synthetic.pdf"})
            bundle["course_metadata"].append({"program_id": pid, "code": code, "values": {}})
            texts = {"content": ("Học máy dùng mô hình phân loại dữ liệu và hồi quy." if code == "TST0001"
                                  else "Mạng máy tính dùng giao thức định tuyến và truyền thông."),
                     "objectives": "Vận dụng kiến thức phân tích bài toán.",
                     "suggested_assessment": "Thiết kế dự án và trình bày báo cáo."}
            for field, body in texts.items():
                f3.append({"chunk_id": f"f3-{cid}-{code}-{field}", "major": major, "curriculum_version": version,
                           "program_id": pid, "cohort_year": cohort, "course_code": code,
                           "course_name": course["course_name"], "field": field,
                           "text": f"CANHBAOCHUNG\nRepeated context {code}\n{body}",
                           "content_origin": "generated", "academic_verified": False,
                           "review_status": "needs_review", "disclosure_required": True,
                           "usage_scope": "reference_only", "warning": "CANHBAOCHUNG",
                           "citation_label": f"F3 do AI sinh — {code}", "provenance": {"source": "synthetic"},
                           "locator": {"offset_scope": "rendered_field_text_excluding_repeated_context",
                                       "start_char": 0, "end_char": len(body)}})
    f1 = []
    for cid, major, version, variant in [("target", "mathematics", "2015", "standard"),
                                        ("foreign", "data_science", "2015", "standard"),
                                        ("old", "mathematics", "2008", "standard"),
                                        ("unknown", "mathematics", "unknown", "standard"),
                                        ("clc", "mathematics", "2015", "high_quality")]:
        f1.append({"chunk_id": f"f1-{cid}", "major": major, "program_version": version,
                   "program_variant": variant, "field": "careers", "text": "Context\nLập trình phần mềm.",
                   "source_quote": "Lập trình phần mềm.", "title": "Ngành giả lập",
                   "source_url": "https://example.test/f1", "locator": {"line": 1},
                   "review_status": "include_markdown", "review": {"status": "include_markdown"},
                   "answer_eligible": True, "usage_scope": "descriptive", "raw_original_verified": False})
    files = {"f1/rag_chunks.jsonl": b"".join(map(_json, f1)),
             "f3/rag_chunks.jsonl": b"".join(map(_json, f3)),
             "f2/hus_source.json": _json(bundle), "f2/source_comparison.json": _json({"synthetic": True})}
    _write(root, files)
    return root, files


def test_filtering_happens_before_top_k_and_term_statistics(corpus):
    root, files = corpus
    args = dict(dataset="f1", major="mathematics", version="2015", program_variant="standard", top_k=1)
    before = HUSRAGRetriever.load(root, source="legacy").search("lập trình phần mềm", **args)
    rows = list(map(json.loads, files["f1/rag_chunks.jsonl"].splitlines()))
    for i in range(20):
        foreign = deepcopy(rows[1])
        foreign.update(chunk_id=f"foreign-{i}", source_quote="phần mềm " * (i + 1))
        rows.append(foreign)
    files["f1/rag_chunks.jsonl"] = b"".join(map(_json, rows))
    _write(root, files)
    after = HUSRAGRetriever.load(root, source="legacy").search("lập trình phần mềm", **args)
    assert [h.chunk.chunk_id for h in before] == ["f1-target"]
    assert [h.chunk.chunk_id for h in after] == ["f1-target"]
    assert after[0].score == before[0].score


def test_unknown_or_wrong_version_does_not_fall_back(corpus):
    root, _ = corpus
    retriever = HUSRAGRetriever.load(root, source="legacy")
    assert not retriever.search("phần mềm", dataset="f1", major="mathematics", version="2023")
    assert not retriever.search("học máy", dataset="f3", major="mathematics", version="TEST-B")
    hits = retriever.search("phần mềm", dataset="f1", major="mathematics", version="2015")
    assert {h.chunk.version for h in hits} == {"2015"}
    all_versions = retriever.search("phần mềm", dataset="f1", major="mathematics")
    assert {h.chunk.version for h in all_versions} == {"2015", "2008", "unknown"}


def test_vietnamese_accents_unicode_forms_and_title_ranking(corpus):
    root, _ = corpus
    retriever = HUSRAGRetriever.load(root, source="legacy")
    args = dict(dataset="f3", major="mathematics", version="TEST-A", allow_generated=True)
    expected = retriever.search("Học máy", **args)
    assert expected[0].chunk.metadata["course_code"] == "TST0001"
    for query in ("hoc may", unicodedata.normalize("NFD", "Học máy")):
        assert retriever.search(query, **args) == expected


@pytest.mark.parametrize("query,explicit,expected", [("tst0001 học gì", None, {"TST0001"}),
                                                     ("TST9999 học máy", None, set()),
                                                     ("TST0001", "TST0002", set()),
                                                     ("TST0001 TST0002", None, {"TST0001", "TST0002"})])
def test_course_codes_in_query_are_hard_filters(corpus, query, explicit, expected):
    root, _ = corpus
    hits = HUSRAGRetriever.load(root, source="legacy").search(query, dataset="f3", major="mathematics", version="TEST-A",
                                            course_code=explicit, top_k=20, allow_generated=True)
    assert {h.chunk.metadata["course_code"] for h in hits} == expected


def test_warning_is_preserved_but_not_ranked_as_topic(corpus):
    root, _ = corpus
    retriever = HUSRAGRetriever.load(root, source="legacy")
    assert not retriever.search("CANHBAOCHUNG", dataset="f3", major="mathematics", allow_generated=True)
    hit, = retriever.search("học máy", dataset="f3", major="mathematics", version="TEST-A",
                            course_code="TST0001", field="content", allow_generated=True)
    assert hit.chunk.text.startswith("CANHBAOCHUNG")
    assert hit.chunk.metadata["review_status"] == "needs_review"
    assert hit.chunk.metadata["citation_label"].startswith("F3 do AI sinh — ")


def test_qa_and_unlisted_files_are_not_second_inputs_and_duplicate_slices_do_not_gain_weight(corpus):
    root, files = corpus
    args = dict(dataset="f1", major="mathematics", version="2015", program_variant="standard")
    before = HUSRAGRetriever.load(root, source="legacy").search("phần mềm", **args)
    qa = root.parent / "qa" / "release"
    qa.mkdir(parents=True)
    (qa / "rag_chunks.jsonl").write_bytes(files["f1/rag_chunks.jsonl"])
    (root / "unlisted.jsonl").write_bytes(b"INVALID JSON THAT MUST NOT BE READ")
    rows = list(map(json.loads, files["f1/rag_chunks.jsonl"].splitlines()))
    duplicate = deepcopy(rows[0])
    duplicate["chunk_id"] = "duplicate-slice"
    rows.append(duplicate)
    files["f1/rag_chunks.jsonl"] = b"".join(map(_json, rows))
    _write(root, files)
    after = HUSRAGRetriever.load(root, source="legacy").search("phần mềm", **args)
    assert len(before) == len(after) == 1
    assert before[0].score == after[0].score


def test_ties_have_stable_order_and_returned_metadata_is_not_shared(corpus):
    root, files = corpus
    rows = list(map(json.loads, files["f1/rag_chunks.jsonl"].splitlines()))
    for code in ("z-source", "a-source"):
        row = deepcopy(rows[0])
        row.update(chunk_id=code, source_url=f"https://example.test/{code}")
        rows.append(row)
    files["f1/rag_chunks.jsonl"] = b"".join(map(_json, rows))
    _write(root, files)
    retriever = HUSRAGRetriever.load(root, source="legacy")
    args = dict(dataset="f1", major="mathematics", version="2015", program_variant="standard", top_k=2)
    hits = retriever.search("phần mềm", **args)
    assert [h.chunk.chunk_id for h in hits] == ["a-source", "f1-target"]
    hits[0].chunk.metadata["review"]["status"] = "exclude"
    assert retriever.search("phần mềm", **args)[0].chunk.metadata["review"]["status"] == "include_markdown"


@pytest.mark.parametrize("query", ["", "   ", "là gì và cho tôi biết", "zzxxyyq"])
def test_no_meaningful_match_returns_empty(corpus, query):
    root, _ = corpus
    assert not HUSRAGRetriever.load(root, source="legacy").search(query, dataset="f1", major="mathematics")


@pytest.mark.parametrize("overrides", [{"top_k": 0}, {"top_k": 51}, {"top_k": True},
                                      {"major": "unknown"}, {"version": ""}, {"dataset": "f2"}])
def test_invalid_filters_do_not_silently_expand_search(corpus, overrides):
    root, _ = corpus
    args = dict(dataset="f1", major="mathematics")
    args.update(overrides)
    with pytest.raises(RAGDataError):
        HUSRAGRetriever.load(root, source="legacy").search("phần mềm", **args)


def test_actual_package_retrieves_contract_evidence_with_provenance_and_generated_labels():
    data = HUSRAGData.load()
    retriever = HUSRAGRetriever(data)
    root = Path("data/hus/rag")
    for line in (root / "f1/acceptance_questions.jsonl").read_bytes().splitlines():
        question = json.loads(line)
        hits = retriever.search(FIELD_LABELS[question["field"]], dataset="f1",
                                major=question["major"], field=question["field"])
        assert hits and any(h.chunk.chunk_id in question["evidence_chunk_ids"] for h in hits)
        assert all(h.chunk.metadata["source_url"] and h.chunk.metadata["locator"] for h in hits)
    programs = {c.metadata["program_id"]: (c.major, c.version)
                for major in MAJOR_CODES.values() for c in data.chunks("f3", major=major, allow_generated=True)}
    for line in (root / "f3/acceptance_questions.jsonl").read_bytes().splitlines():
        question = json.loads(line)
        major, version = programs[question["program_id"]]
        field = question["question_id"].rsplit(":", 1)[1]
        hits = retriever.search(question["question"], dataset="f3", major=major, version=version,
                                field="suggested_assessment" if field == "official_assessment" else field, allow_generated=True)
        assert hits and any(h.chunk.chunk_id in question["evidence_chunk_ids"] for h in hits)
        assert all(h.chunk.metadata["disclosure_required"] and not h.chunk.metadata["academic_verified"] for h in hits)
