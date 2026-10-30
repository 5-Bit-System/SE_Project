"""Full F2 membership coverage and explicit separation of generated/official F3."""

from collections import Counter
import copy
import json
from pathlib import Path

import pytest

from app.hus.corpus import verify_artifacts
from app.hus.f3_reference import (
    DATASET_KIND, PROGRAMS, build_reference, load_inputs, section_texts, validate_record,
)

ROOT = Path("data/hus/qa/20261028/f3_reference")
AUDIT = Path("data/hus/qa/20261028/audit")


@pytest.fixture(scope="module")
def built():
    return build_reference(ROOT / "inputs", AUDIT)


def rows(built, name):
    return [json.loads(line) for line in built[name].splitlines()]


def test_every_real_F2_membership_has_three_nonempty_generated_fields(built):
    records = rows(built, "records.jsonl")
    source = json.loads((ROOT / "inputs/hus_source.json").read_text(encoding="utf-8"))
    curriculum_ids = {c["curriculum_id"]: PROGRAMS[c["major_code"]][0] for c in source["tables"]["curricula"]}
    expected = {(curriculum_ids[m["curriculum_id"]], m["course_code"])
                for m in source["tables"]["curriculum_courses"]}
    assert {(r["program_id"], r["course_code"]) for r in records} == expected
    assert len(records) == len(expected) == 290
    assert Counter(r["program_id"] for r in records) == Counter({v[0]: v[3] for v in PROGRAMS.values()})
    assert len({r["course_code"] for r in records}) == 174
    for r in records:
        assert len(r["generated_content"]["topics"]) >= 3
        assert len(r["generated_objectives"]) >= 2
        assert len(r["suggested_assessment"]["tasks"]) >= 2
        assert len(r["suggested_assessment"]["criteria"]) >= 2


def test_all_generated_records_trace_to_exact_F2_rows_and_credits(built):
    source = json.loads((ROOT / "inputs/hus_source.json").read_text(encoding="utf-8"))["tables"]
    courses = {c["course_code"]: c for c in source["courses"]}
    for r in rows(built, "records.jsonl"):
        assert r["course_name"] == courses[r["course_code"]]["course_name"]
        assert r["f2"]["credits_transcribed"] == courses[r["course_code"]]["credits"]
        for pointer in r["provenance"]["f2_pointers"]:
            entry = source["official_curriculum_entries"][int(pointer.rsplit("/", 1)[1])]
            assert entry["course_code"] == r["course_code"]
            curriculum = next(c for c in source["curricula"] if c["curriculum_id"] == entry["curriculum_id"])
            assert r["program_id"] == PROGRAMS[curriculum["major_code"]][0]
            assert r["curriculum_version"] == curriculum["curriculum_version"]
        assert r["f2"]["prerequisite_answer_status"] == "not_revalidated_here"


def test_no_reference_only_codes_or_fixture_courses_enter_generated_dataset(built):
    codes = {r["course_code"] for r in rows(built, "records.jsonl")}
    assert not codes & {"MAT2320", "MAT2321", "MAT2322", "MAT2313", "MAT3340", "TST0001"}


def test_every_standalone_RAG_chunk_discloses_generation_and_scope(built):
    chunks = rows(built, "rag_chunks.jsonl")
    assert len(chunks) == 870
    assert len({c["chunk_id"] for c in chunks}) == len(chunks)
    assert Counter(c["field"] for c in chunks) == {"content": 290, "objectives": 290, "suggested_assessment": 290}
    records = {r["record_id"]: r for r in rows(built, "records.jsonl")}
    for c in chunks:
        assert c["text"].startswith("Học phần: ")
        assert "warning" not in c
        assert c["citation_label"] == f"{c['course_code']} — {c['major_name']}"
        assert c["content_origin"] == "generated" and c["dataset_kind"] == DATASET_KIND
        assert c["usage_scope"] == "reference_only" and c["disclosure_required"]
        assert not c["academic_verified"]
        assert c["course_code"] in c["text"] and c["major_name"] in c["text"]
        locator = c["locator"]
        field = section_texts(records[c["record_id"]])[locator["field"]]
        assert c["text"].endswith(field[locator["start_char"]:locator["end_char"]])


@pytest.mark.parametrize("mutation", ["reviewer", "verified", "official_content", "official_objectives",
                                     "official_assessment", "weights", "exam_format", "disclosure"])
def test_generated_content_cannot_be_promoted_to_official_facts(built, mutation):
    r = copy.deepcopy(rows(built, "records.jsonl")[0])
    if mutation.startswith("official_"):
        r[mutation] = "Unsupported official claim"
    elif mutation == "reviewer":
        r["reviewer"] = "Invented university reviewer"
    elif mutation == "verified":
        r["academic_verified"] = True
    elif mutation == "weights":
        r["suggested_assessment"]["weights_percent"] = [30, 70]
    elif mutation == "exam_format":
        r["suggested_assessment"]["official_exam_format"] = "Final exam"
    else:
        r["disclosure_required"] = False
    with pytest.raises(ValueError):
        validate_record(r)


def test_source_and_blueprint_changes_cannot_silently_preserve_release(tmp_path, built):
    for name in ("hus_source.json", "blueprints.psv"):
        (tmp_path / name).write_bytes((ROOT / "inputs" / name).read_bytes())
    source = tmp_path / "hus_source.json"
    source.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(ValueError, match="Git blob"):
        load_inputs(tmp_path)
    source.write_bytes((ROOT / "inputs/hus_source.json").read_bytes())
    blueprint = tmp_path / "blueprints.psv"
    lines = blueprint.read_text(encoding="utf-8").splitlines()
    blueprint.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="coverage"):
        load_inputs(tmp_path)


def test_source_candidates_remain_unverified_and_do_not_supply_official_fields(built):
    records = rows(built, "records.jsonl")
    assert any(r["official_source_candidates"] for r in records)
    for r in records:
        assert r["official_content"] is r["official_objectives"] is r["official_assessment"] is None
        for candidate in r["official_source_candidates"]:
            assert not candidate["official_answer_eligible"]
            assert candidate["status"] == "unverified_source_candidate"
    original = [json.loads(line) for line in (AUDIT / "answer_chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(original) == 8 and all(c["review_status"] == "include" for c in original)
    assert not {c["chunk_id"] for c in original} & {c["chunk_id"] for c in rows(built, "rag_chunks.jsonl")}


def test_official_assessment_questions_explicitly_require_unknown(built):
    questions = rows(built, "acceptance_questions.jsonl")
    assert len(questions) == 16 and all(q["result"] == "pass" for q in questions)
    assert sum(q["expected_answer_mode"] == "disclose_official_unknown" for q in questions) == 4
    assert all(not q["official_answer_available"] and q["disclosure_required"] for q in questions)


def test_versioned_release_reproduces_every_output_byte(built):
    verify_artifacts(ROOT / "release", built)


def test_cli_build_verify_and_overwrite_protection(tmp_path):
    from tools.prepare_hus_f3_reference import main
    out = tmp_path / "new-release"
    assert main(["build", "--out", str(out)]) == 0
    assert main(["verify", "--out", str(out)]) == 0
    with pytest.raises(SystemExit):
        main(["build", "--out", str(out)])
    with pytest.raises(SystemExit):
        main(["build", "--out", "data/hus/corpus"])
