"""Boundary and corruption checks for resumable OCR, without model inference."""

import copy
import json

import pytest

from tools.audit_hus_source_review import ROOT, SourceReviewError, digest, write_json
from tools.ocr_hus_review import (
    queue_key,
    restore_checkpoint,
    run,
    safe_paths,
    validate_observation,
)


@pytest.mark.parametrize("bad", [ROOT / "data/hus/citation_assets", ROOT / "data/hus/rag/releases/ocr", ROOT.parent / "ocr"])
def test_ocr_rejects_source_or_external_output_before_io(bad, monkeypatch):
    def no_mkdir(*args, **kwargs):
        raise AssertionError("must reject before creating directories")
    monkeypatch.setattr(type(ROOT), "mkdir", no_mkdir)
    with pytest.raises(SourceReviewError, match="output"):
        run(bad, ROOT / "backups/ocr-images-test", ROOT / "backups/ocr-models-test")


def test_ocr_rejects_overlapping_cache_and_runtime_models():
    with pytest.raises(SourceReviewError, match="overlap"):
        safe_paths(ROOT / "data/hus/review/test", ROOT / "backups/ocr", ROOT / "backups/ocr/models")
    with pytest.raises(SourceReviewError, match="backups"):
        safe_paths(ROOT / "data/hus/review/test", ROOT / "backups/ocr", ROOT / "data/hus/raw/models")


@pytest.mark.parametrize("row", [{"source_sha256": "../../escape", "pdf_page": 1},
                                  {"source_sha256": "a" * 64, "pdf_page": 0},
                                  {"source_sha256": "a" * 64, "pdf_page": True}])
def test_ocr_queue_cannot_escape_or_use_nonphysical_pages(row):
    with pytest.raises(SourceReviewError):
        queue_key(row)


def observation():
    return {"source_sha256": "a" * 64, "pdf_page": 3, "text": "printed text", "text_sha256": digest(b"printed text"),
            "boxes": [{"text": "printed text", "confidence": 0.9, "bbox_pixels": [[0, 0], [1, 0], [1, 1], [0, 1]]}],
            "review_status": "machine_ocr_pending_visual_and_academic_review", "academic_verified": False,
            "default_retrieval_enabled": False, "table_structure_verified": False}


@pytest.mark.parametrize("change", [{"pdf_page": 4}, {"academic_verified": True}, {"default_retrieval_enabled": True},
                                     {"table_structure_verified": True}, {"text": "changed"}])
def test_ocr_checkpoint_cannot_upgrade_review_or_rebind_page(change):
    original = observation()
    changed = {**original, **change}
    with pytest.raises(SourceReviewError):
        validate_observation(changed, original)


def test_nonfinite_ocr_confidence_cannot_pass_validation():
    row = copy.deepcopy(observation())
    row["boxes"][0]["confidence"] = float("nan")
    with pytest.raises(SourceReviewError, match="confidence"):
        validate_observation(row, observation())


def test_resume_rejects_changed_model_identity_before_image_read(tmp_path):
    checkpoint = tmp_path / "checkpoint.json"
    write_json(checkpoint, {"run_identity_sha256": "old", "observation": observation()})
    with pytest.raises(SourceReviewError, match="identity"):
        restore_checkpoint(checkpoint, observation(), "new")


def test_resume_rejects_text_corruption_even_if_well_formed(tmp_path):
    row = observation()
    checkpoint = tmp_path / "checkpoint.json"
    pin = digest(json.dumps(row, sort_keys=True, ensure_ascii=False).encode())
    row["text"] = "forged"
    write_json(checkpoint, {"run_identity_sha256": "run", "observation": row, "observation_sha256": pin})
    with pytest.raises(SourceReviewError, match="observation hash"):
        restore_checkpoint(checkpoint, observation(), "run")
