"""Import exact original files already in pinned Git objects; no network or conversion.

python -X utf8 -m tools.prepare_hus_citation_assets
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit

import pdfplumber

from app.hus.data_release import checked_path, encoded
from app.hus.rag_loader import HUSRAGData


def prepare(repo: Path, out: Path) -> dict:
    repo, out = repo.resolve(), out.resolve()
    if not out.is_relative_to(repo) or out.exists():
        raise ValueError("Choose a new citation asset directory within this repository")
    package = repo / "data/hus/rag"
    data = HUSRAGData.load_current(package)
    context = data.citation_context
    imported = json.loads((package / "PORTABLE_IMPORT.json").read_bytes())
    entries, bindings = {}, {}
    referenced = {loc["sha256"] for course in data._courses.values()
                  for loc in course.provenance["portable_record"]["citation"]["pdf_locators"]}
    targets = []
    for source in context["sources"].values():
        capture = source.get("recovered_capture") or {}
        if capture.get("file_type") not in {"pdf", "docx"}:
            continue
        filename = unquote(urlsplit(capture["final_url"]).path.rsplit("/", 1)[-1])
        targets.append({"binding": "f1:" + source["source_id"], "sha256": capture["sha256"],
                        "kind": capture["file_type"], "git_commit": imported["source_commit"],
                        "git_path": capture["repository_asset_path"], "filename": filename,
                        "expected_pages": capture["page_count"] if capture["file_type"] == "pdf" else None})
    for source in context["canonical_pdfs"]:
        if source["sha256"] in referenced:
            targets.append({"binding": "pdf:" + source["sha256"], "sha256": source["sha256"],
                            "kind": "pdf", "git_commit": imported["source_commit"], "git_path": source["path"],
                            "declared_origin_commit": source["origin_commit"],
                            "filename": source["source_ref"], "expected_pages": None})
    out.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".citation-assets-", dir=out.parent) as temporary:
        staging = Path(temporary) / "assets"
        staging.mkdir()
        for target in targets:
            checked_path(repo, target["git_path"])
            sha = target["sha256"]
            raw = subprocess.check_output(["git", "show", target["git_commit"] + ":" + target["git_path"]], cwd=repo)
            if hashlib.sha256(raw).hexdigest() != sha:
                raise ValueError(f"Original hash differs: {target['binding']}")
            count = None
            if target["kind"] == "pdf":
                if not raw.startswith(b"%PDF-"):
                    raise ValueError("Original is not a PDF")
                with pdfplumber.open(io.BytesIO(raw)) as pdf:
                    count = len(pdf.pages)
                if count < 1 or (target["expected_pages"] is not None and count != target["expected_pages"]):
                    raise ValueError("Original PDF page count differs from captured text")
            else:
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    if "word/document.xml" not in archive.namelist():
                        raise ValueError("Original is not DOCX")
            path = f"files/{sha}.{target['kind']}"
            file = staging / path
            file.parent.mkdir(exist_ok=True)
            file.write_bytes(raw)
            entry = entries.setdefault(sha, {"sha256": sha, "path": path, "bytes": len(raw),
                                            "file_type": target["kind"], "page_count": count,
                                            "filename": target["filename"], "origins": []})
            entry["origins"].append(target)
            bindings[target["binding"]] = sha
        registry = {"schema_version": "1.0", "release_id": data.release_identity["release_id"],
                    "release_sha256": data.release_identity["release_sha256"],
                    "assets": entries, "bindings": bindings, "academic_verification_added": False}
        registry["registry_sha256"] = hashlib.sha256(encoded(registry)).hexdigest()
        (staging / "registry.json").write_bytes(encoded(registry))
        assert staging.resolve().is_relative_to(repo) and out.is_relative_to(repo)
        staging.rename(out)
    return {"assets": len(entries), "pdfs": sum(e["file_type"] == "pdf" for e in entries.values()),
            "docx": sum(e["file_type"] == "docx" for e in entries.values()),
            "registry_sha256": registry["registry_sha256"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("data/hus/citation_assets"))
    args = parser.parse_args(argv)
    print(json.dumps(prepare(Path.cwd(), args.out)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
