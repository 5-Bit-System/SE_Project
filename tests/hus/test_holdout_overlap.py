"""Overlap checks flag leakage risks; they never assert semantic independence."""

import hashlib
import importlib
import json
from pathlib import Path

import pytest


def auditor():
    path = Path(__file__).resolve().parents[2] / "tools/audit_hus_holdout_overlap.py"
    assert path.exists(), "offline overlap auditor is not implemented"
    return importlib.import_module("tools.audit_hus_holdout_overlap")


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
                    encoding="utf-8")


def make_pack(root, new_question="MAT8888 có bao nhiêu tín chỉ?", old_question="Tin chi MAT7777?"):
    pack = root / "data/hus/evaluation/new_pack"
    old = root / "data/hus/evaluation/dev/questions.jsonl"
    write_rows(pack / "questions.jsonl", [{"question_id": "H2-Q001", "request": {
        "question": new_question, "major": "data_science"}}])
    write_rows(old, [{"question_id": "DEV-Q001", "request": {
        "question": old_question, "major": "data_science"}}])
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {"development_inputs_sha256": {old.relative_to(root).as_posix(): digest(old)},
                "files": {"questions.jsonl": digest(pack / "questions.jsonl")}}
    (pack / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return pack, old


def test_accent_punctuation_duplicate_is_flagged_with_input_hashes(tmp_path):
    module = auditor()
    pack, old = make_pack(tmp_path, "Tín chỉ MAT7777?", "Tin chi MAT7777!")
    report = module.audit_pack(pack, tmp_path / "audit", repo_root=tmp_path, regression_paths=[])
    assert report["exact_duplicate_cases"] == 1
    assert report["semantic_independence"] == "not_established_requires_human_review"
    assert report["human_accepted_reviews"] == 0
    assert old.relative_to(tmp_path).as_posix() in report["input_sha256"]
    row = json.loads((tmp_path / "audit/neighbors.jsonl").read_text(encoding="utf-8"))
    assert row["neighbors"][0]["source_id"] == "DEV-Q001"
    assert row["neighbors"][0]["same_course_codes"] == ["MAT7777"]


def test_near_neighbor_is_visible_without_claiming_equivalence(tmp_path):
    module = auditor()
    pack, _ = make_pack(tmp_path, "Học phần MAT7777 có bao nhiêu tín chỉ?",
                        "Môn MAT7777 có bao nhiêu tín chỉ?")
    report = module.audit_pack(pack, tmp_path / "audit", repo_root=tmp_path, regression_paths=[])
    assert report["strong_lexical_risk_cases"] == 1
    assert report["exact_duplicate_cases"] == 0
    row = json.loads((tmp_path / "audit/neighbors.jsonl").read_text(encoding="utf-8"))
    assert 0 < row["neighbors"][0]["token_jaccard"] < 1
    assert row["human_review_required"] is True


def test_zero_lexical_overlap_does_not_approve_holdout(tmp_path):
    module = auditor()
    pack, _ = make_pack(tmp_path, "Lập trình hướng đối tượng?", "Số giờ thực hành?")
    report = module.audit_pack(pack, tmp_path / "audit", repo_root=tmp_path, regression_paths=[])
    assert report["exact_duplicate_cases"] == 0
    assert report["holdout_approved"] is False
    assert report["new_rag_inference"] is False


def test_test_prompts_are_extracted_statically_without_import(tmp_path):
    module = auditor()
    pack, _ = make_pack(tmp_path, "Tín chỉ MAT7777?", "Một câu khác?")
    test_path = tmp_path / "tests/hus/test_prompts.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text('raise RuntimeError("must not import this file")\n'
                         '@pytest.mark.parametrize("question", ["Tin chi MAT7777!"])\n'
                         'def test_prompt(question): pass\n'
                         'payload = {"question": "Nội dung MAT8888?"}\n', encoding="utf-8")
    report = module.audit_pack(pack, tmp_path / "audit", repo_root=tmp_path,
                               regression_paths=[test_path])
    assert report["exact_duplicate_cases"] == 1
    assert report["regression_prompt_count"] == 2
    assert test_path.relative_to(tmp_path).as_posix() in report["input_sha256"]


def test_changed_pinned_development_is_rejected(tmp_path):
    module = auditor()
    pack, old = make_pack(tmp_path)
    old.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        module.audit_pack(pack, tmp_path / "audit", repo_root=tmp_path, regression_paths=[])


def test_keyword_question_literals_are_extracted_without_importing_tests(tmp_path):
    module = auditor()
    pack, _ = make_pack(tmp_path, "Tín chỉ MAT7777?", "Một câu khác?")
    test_path = tmp_path / "tests/hus/test_keywords.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text('raise RuntimeError("never import")\n'
                         'request = HUSQuestion(question="Tin chi MAT7777!")\n', encoding="utf-8")
    report = module.audit_pack(pack, tmp_path / "audit", repo_root=tmp_path,
                               regression_paths=[test_path])
    assert report["exact_duplicate_cases"] == 1
    assert report["regression_prompt_count"] == 1


def test_refuses_overwrite_and_output_inside_frozen_inputs(tmp_path):
    module = auditor()
    pack, _ = make_pack(tmp_path)
    with pytest.raises(ValueError, match="protected"):
        module.audit_pack(pack, pack / "audit", repo_root=tmp_path, regression_paths=[])
    out = tmp_path / "audit"
    module.audit_pack(pack, out, repo_root=tmp_path, regression_paths=[])
    with pytest.raises(ValueError, match="exists"):
        module.audit_pack(pack, out, repo_root=tmp_path, regression_paths=[])
