"""Development data must remain grounded, isolated and explicitly exposed."""

import hashlib
import importlib
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "data/hus/evaluation/diagnostic_dev_v1"


def validator():
    path = ROOT / "tools/validate_hus_diagnostic.py"
    assert path.exists(), "diagnostic validator is not implemented"
    return importlib.import_module("tools.validate_hus_diagnostic")


def test_development_pack_is_balanced_and_never_holdout():
    report = validator().validate_pack(PACK, ROOT)
    assert report["questions"] == 96
    assert set(report["by_major"].values()) == {24}
    assert report["holdout_eligible"] is False
    assert report["rag_inference_run"] is False
    assert report["retrieval_metrics"] is None
    assert report["baseline_preserved"] is True


def edit(pack, filename, mutate):
    path = pack / filename
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    mutate(rows)
    path.write_bytes("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode("utf-8"))
    manifest_path = pack / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


@pytest.mark.parametrize(("filename", "mutate", "message"), [
    ("gold.jsonl", lambda rows: rows[0].update(expected_answer="fabricated"), "gold"),
    ("gold.jsonl", lambda rows: rows[0].update(evidence_ids=["P11-E016"]), "gold"),
    ("questions.jsonl", lambda rows: rows[0]["request"].update(major="computer_science"), "scope"),
    ("questions.jsonl", lambda rows: rows[0]["request"].update(field="introduction"), "hints"),
    ("questions.jsonl", lambda rows: rows[0]["request"].update(question="   "), "empty"),
    ("questions.jsonl", lambda rows: rows[-1]["request"].update(question="Một nội dung AI khác"), "contrast"),
    ("questions.jsonl", lambda rows: rows[1].update(request=rows[0]["request"].copy()), "duplicate"),
    ("questions.jsonl", lambda rows: rows[-1]["request"].update(
        allow_generated_reference=True, question="Nội dung MAT3535 gồm những gì?"), "opt-in"),
    ("cases.jsonl", lambda rows: rows[0].update(parent_question_id="P11-Q013"), "scope|gold"),
])
def test_rejects_semantic_corruption_even_after_rehash(tmp_path, filename, mutate, message):
    module = validator()
    copied = Path(shutil.copytree(PACK, tmp_path / "pack"))
    edit(copied, filename, mutate)
    with pytest.raises(ValueError, match=message):
        module.validate_pack(copied, ROOT)


def test_rejects_payload_tampering(tmp_path):
    module = validator()
    copied = Path(shutil.copytree(PACK, tmp_path / "pack"))
    with (copied / "questions.jsonl").open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(ValueError, match="hash"):
        module.validate_pack(copied, ROOT)


def test_rejects_claim_of_independent_holdout(tmp_path):
    module = validator()
    copied = Path(shutil.copytree(PACK, tmp_path / "pack"))
    path = copied / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["holdout_eligible"] = True
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="holdout"):
        module.validate_pack(copied, ROOT)
