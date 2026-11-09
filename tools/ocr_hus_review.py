"""Offline, resumable OCR evidence for the frozen P1-3 queue; no runtime writes."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
from pathlib import Path

from tools.audit_hus_source_review import (
    RELEASE,
    ROOT,
    SourceReviewError,
    check_binary_hash,
    digest,
    read_rows,
    require,
    write_json,
    write_rows,
)

AUDIT = ROOT / "data/hus/review/p13_source_audit_v1"
DEFAULT_MODELS = ROOT / "backups/hus_source_review/p13/ocr_models"
DEFAULT_IMAGES = ROOT / "backups/hus_source_review/p13/ocr_images_v1"
PARAMETERS = {"languages": ["vi", "en"], "gpu": False, "render_scale": 2,
              "decoder": "greedy", "batch_size": 1, "workers": 0,
              "paragraph": False, "canvas_size": 2560, "mag_ratio": 1,
              "torch_threads": 4, "low_confidence_threshold": 0.8}


def local_path(value):
    path = (ROOT / value).resolve()
    require(path.is_relative_to(ROOT), "input path escapes workspace")
    return path


def safe_paths(out, images, models):
    out, images, models = (Path(p).resolve() for p in (out, images, models))
    require(any(out.is_relative_to(base) and out != base
                for base in [ROOT / "data/hus/review", ROOT / "backups"]),
            "output must be a dedicated review or backups directory")
    for path in (images, models):
        require(path.is_relative_to(ROOT / "backups") and path != ROOT / "backups",
                "images/models must be dedicated backups directories")
    for a, b in ((out, images), (out, models), (images, models)):
        require(not a.is_relative_to(b) and not b.is_relative_to(a), "directories overlap")
    return out, images, models


def queue_key(row):
    sha, page = row["source_sha256"], row["pdf_page"]
    require(isinstance(sha, str) and len(sha) == 64 and all(c in "0123456789abcdef" for c in sha),
            "invalid source hash")
    require(type(page) is int and page > 0, "invalid physical page")
    return f"{sha}-p{page:04d}"


def prepare_inputs(models):
    # Verify the old pack before trusting either its queue or its summary.
    manifest = json.loads((AUDIT / "manifest.json").read_bytes())
    paths = [AUDIT / "manifest.json"]
    for name, expected in manifest["files_sha256"].items():
        path = local_path((AUDIT / name).relative_to(ROOT))
        require(path.is_relative_to(AUDIT), "audit path escape")
        check_binary_hash(path.read_bytes(), expected)
        paths.append(path)
    release = json.loads((RELEASE / "manifest.json").read_bytes())
    for name, pin in release["files"].items():
        path = local_path((RELEASE / name).relative_to(ROOT))
        require(path.is_relative_to(RELEASE), "release path escape")
        raw = path.read_bytes()
        require(len(raw) == pin["bytes"], "release size mismatch")
        check_binary_hash(raw, pin["sha256"])
        paths.append(path)
    paths.extend(local_path(p) for p in json.loads((AUDIT / "report.json").read_bytes())["source_inputs_sha256"])
    for name, expected in json.loads((AUDIT / "report.json").read_bytes())["source_inputs_sha256"].items():
        check_binary_hash(local_path(name).read_bytes(), expected)
    registry = json.loads((ROOT / "data/hus/citation_assets/registry.json").read_bytes())
    assets = {sha: local_path("data/hus/citation_assets/" + asset["path"])
              for sha, asset in registry["assets"].items()}
    for pdf in json.loads((RELEASE / "input_manifest.json").read_bytes())["pdfs"]:
        assets.setdefault(pdf["sha256"], local_path(pdf["path"]))
    for asset in read_rows(AUDIT / "binary_assets.jsonl"):
        if "review_only_syllabus_not_active_registry" in asset["bindings"]:
            assets[asset["sha256"]] = local_path(f"backups/hus_source_review/p13/originals/{asset['sha256']}.pdf")
    queue = read_rows(AUDIT / "ocr_queue.jsonl")
    require(len({queue_key(q) for q in queue}) == len(queue), "duplicate queue page")
    import pypdfium2 as pdfium

    for sha in sorted({q["source_sha256"] for q in queue}):
        require(sha in assets, "missing queue source binding")
        raw = assets[sha].read_bytes()
        check_binary_hash(raw, sha)
        with pdfium.PdfDocument(raw) as doc:
            require(all(q["pdf_page"] <= len(doc) for q in queue if q["source_sha256"] == sha),
                    "physical page outside source")
    paths.extend(assets.values())
    # The model filenames and upstream checksum must match the installed engine.
    import hashlib

    from easyocr.config import detection_models, recognition_models

    model_pins = []
    for cfg in (detection_models["craft"], recognition_models["gen2"]["latin_g2"]):
        raw = (models / cfg["filename"]).read_bytes()
        require(hashlib.md5(raw).hexdigest() == cfg["md5sum"], "OCR model checksum mismatch")
        model_pins.append({"filename": cfg["filename"], "url": cfg["url"], "sha256": digest(raw),
                           "upstream_md5": cfg["md5sum"], "bytes": len(raw)})
    versions = {name: importlib.metadata.version(name)
                for name in ["easyocr", "torch", "pypdfium2", "Pillow", "numpy"]}
    identity = {"schema_version": "1.0", "tool_sha256": digest(Path(__file__).read_bytes()),
                "parameters": PARAMETERS, "versions": versions, "model_pins": model_pins,
                "source_inputs_sha256": {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in sorted(set(paths))},
                "queue_pages": len(queue), "review_status": "machine_ocr_pending_visual_and_academic_review",
                "source_review_upgraded": False, "official_F3_enabled": False}
    return queue, assets, identity


def validate_observation(row, queued):
    require(row["source_sha256"] == queued["source_sha256"] and row["pdf_page"] == queued["pdf_page"],
            "OCR source/page mismatch")
    require(row["review_status"] == "machine_ocr_pending_visual_and_academic_review"
            and row["academic_verified"] is False and row["default_retrieval_enabled"] is False
            and row["table_structure_verified"] is False, "OCR cannot grant review")
    require(row["text"] == "\n".join(box["text"] for box in row["boxes"]), "OCR text/boxes disagree")
    for box in row["boxes"]:
        require(math.isfinite(box["confidence"]) and 0 <= box["confidence"] <= 1, "invalid confidence")
        require(len(box["bbox_pixels"]) == 4 and all(len(point) == 2 and all(math.isfinite(v) for v in point)
                                                   for point in box["bbox_pixels"]), "invalid OCR box")
    require(row["text_sha256"] == digest(row["text"].encode("utf-8")), "OCR text hash mismatch")


def restore_checkpoint(path, queued, identity):
    checkpoint = json.loads(path.read_bytes())
    require(checkpoint["run_identity_sha256"] == identity, "checkpoint identity mismatch")
    row = checkpoint["observation"]
    require(checkpoint["observation_sha256"] == digest(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()),
            "checkpoint observation hash mismatch")
    validate_observation(row, queued)
    check_binary_hash(local_path(row["image_path"]).read_bytes(), row["image_sha256"])
    return row


def run(out, images, models, resume=False):
    out, images, models = safe_paths(out, images, models)
    require(resume == out.exists(), "use a new output or --resume on an existing run")
    queue, assets, identity = prepare_inputs(models)
    identity_sha = digest(json.dumps(identity, sort_keys=True, ensure_ascii=False).encode())
    if resume:
        require(json.loads((out / "run_inputs.json").read_bytes()) == identity, "resume inputs/tool/models changed")
    else:
        require(not images.exists(), "use a new images directory")
        out.mkdir(parents=True)
        (out / "pages").mkdir()
        images.mkdir(parents=True)
        write_json(out / "run_inputs.json", identity)
    import easyocr
    import numpy as np
    import pypdfium2 as pdfium
    import torch

    torch.set_num_threads(PARAMETERS["torch_threads"])
    reader = easyocr.Reader(PARAMETERS["languages"], gpu=False, download_enabled=False,
                            model_storage_directory=str(models), user_network_directory=str(models / "user_network"),
                            verbose=False)
    results = []
    for index, queued in enumerate(queue):
        key = queue_key(queued)
        checkpoint = out / "pages" / f"{key}.json"
        if checkpoint.exists():
            row = restore_checkpoint(checkpoint, queued, identity_sha)
        else:
            raw = assets[queued["source_sha256"]].read_bytes()
            check_binary_hash(raw, queued["source_sha256"])
            with pdfium.PdfDocument(raw) as doc:
                page = doc[queued["pdf_page"] - 1]
                try:
                    bitmap = page.render(scale=PARAMETERS["render_scale"])
                    try:
                        image = bitmap.to_pil().convert("RGB")
                    finally:
                        bitmap.close()
                finally:
                    page.close()
            image_path = images / f"{key}.png"
            image.save(image_path)
            try:
                recognized = reader.readtext(np.array(image), decoder="greedy", batch_size=1, workers=0,
                                             paragraph=False, canvas_size=2560, mag_ratio=1, detail=1)
                size = list(image.size)
            finally:
                image.close()
            boxes = [{"bbox_pixels": [[float(x), float(y)] for x, y in bbox],
                      "text": text, "confidence": float(confidence)} for bbox, text, confidence in recognized]
            text = "\n".join(box["text"] for box in boxes)
            row = {"source_sha256": queued["source_sha256"], "pdf_page": queued["pdf_page"],
                   "original_text_layer_sha256": queued["text_sha256"], "image_path": image_path.relative_to(ROOT).as_posix(),
                   "image_sha256": digest(image_path.read_bytes()), "image_size_pixels": size,
                   "text": text, "text_sha256": digest(text.encode()), "boxes": boxes,
                   "low_confidence_boxes": sum(box["confidence"] < 0.8 for box in boxes),
                   "ocr_executed": True, "blank_verified": False, "table_structure_verified": False,
                   "review_status": "machine_ocr_pending_visual_and_academic_review",
                   "academic_verified": False, "default_retrieval_enabled": False}
            validate_observation(row, queued)
            write_json(checkpoint, {"run_identity_sha256": identity_sha, "observation": row,
                                   "observation_sha256": digest(json.dumps(row, sort_keys=True, ensure_ascii=False).encode())})
        results.append(row)
        print(f"{index + 1}/{len(queue)} {key[:12]} page={row['pdf_page']} boxes={len(row['boxes'])}", flush=True)
    for name, sha in identity["source_inputs_sha256"].items():
        check_binary_hash(local_path(name).read_bytes(), sha)
    write_rows(out / "ocr_pages.jsonl", results)
    summary = {"status": "machine_ocr_complete_visual_and_academic_review_pending", "queue_pages": len(queue),
               "ocr_pages": len(results), "pages_with_text": sum(bool(r["boxes"]) for r in results),
               "boxes": sum(len(r["boxes"]) for r in results),
               "low_confidence_boxes": sum(r["low_confidence_boxes"] for r in results),
               "images": len(results), "source_inputs_unchanged": len(identity["source_inputs_sha256"]),
               "academic_verification_added": 0, "official_F3_enabled": False, "runtime_changed": False,
               "table_structure_verified": False, "P1_3_accepted": False}
    write_json(out / "report.json", summary)
    write_json(out / "manifest.json", {"run_identity_sha256": identity_sha,
               "files_sha256": {p.relative_to(out).as_posix(): digest(p.read_bytes())
                                for p in sorted(out.rglob("*")) if p.is_file() and p.name != "manifest.json"}})
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--images", type=Path, default=DEFAULT_IMAGES)
    parser.add_argument("--models", type=Path, default=DEFAULT_MODELS)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.out, args.images, args.models, args.resume), ensure_ascii=False))
    except (SourceReviewError, OSError) as error:
        parser.exit(1, f"OCR review failed: {error}\n")


if __name__ == "__main__":
    main()
