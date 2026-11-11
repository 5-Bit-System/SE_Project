"""Portable detailed-F3 release, derived only from two sealed public snapshots."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from app.hus.data_release import (
    checked_path,
    common_chunk,
    digest,
    encoded,
    evaluation_questions,
    jsonl,
)
from app.hus.f3_detail import SOURCE_MANIFEST_SHA, load_candidate

PARENT = Path("data/hus/rag/releases/hus-data-20261031-v3")
CANDIDATE = Path("data/hus/qa/20261110/f3_reference_v2/release")
RELEASE_ID = "hus-data-20261111-v4"
CANDIDATE_SHA = "970aec760c6fdc371f01e1a8b7019d954e140ab51598a92a277492b239c6c56e"
PREFIX = "evidence/f3_v2/candidate/"
PARENT_FILE = "evidence/f3_v2/parent_manifest.json"
REPLACED = {
    "f3_records.jsonl",
    "f3_chunks.jsonl",
    "chunks.jsonl",
    "evaluation/questions.jsonl",
    "quality_report.json",
}
DESCRIPTOR = {
    "schema": "detailed-f3-v2",
    "parent_manifest_sha256": SOURCE_MANIFEST_SHA,
    "candidate_manifest_sha256": CANDIDATE_SHA,
    "fields": ["content", "objectives"],
}


def _rows(raw):
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def _capture(root: Path) -> tuple[dict, dict[str, bytes]]:
    raw = (root / "manifest.json").read_bytes()
    manifest = json.loads(raw)
    names = set(manifest["files"]) | {"manifest.json"}
    if names != {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}:
        raise ValueError("Release file inventory differs")
    output = {"manifest.json": raw}
    for name, identity in manifest["files"].items():
        data = checked_path(root, name).read_bytes()
        if identity != {"bytes": len(data), "sha256": digest(data)}:
            raise ValueError("Release checksum mismatch: " + name)
        output[name] = data
    return manifest, output


def _check_candidate(payloads: dict[str, bytes]) -> None:
    if digest(payloads["manifest.json"]) != CANDIDATE_SHA:
        raise ValueError("Unpinned detailed candidate")
    manifest = json.loads(payloads["manifest.json"])
    if set(payloads) != set(manifest["files"]) | {"manifest.json"}:
        raise ValueError("Detailed candidate inventory differs from sealed manifest")
    with TemporaryDirectory(prefix="hus-f3-candidate-") as temporary:
        root = Path(temporary)
        for name, raw in payloads.items():
            target = checked_path(root, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        load_candidate(root, allow_generated=True)


def _derived(inherited: dict[str, bytes], candidate: dict[str, bytes]) -> dict[str, bytes]:
    records = _rows(candidate["records.jsonl"])
    canonical = {r["record_id"]: r for r in _rows(inherited["f2_records.jsonl"])}
    if {r["record_id"] for r in records} != set(canonical) or len(records) != len(canonical):
        raise ValueError("Detailed F3 membership differs")
    for record in records:
        if record["f2_identity"] != canonical[record["record_id"]]:
            raise ValueError("Detailed F3 canonical facts differ")
    f3 = []
    for part in _rows(candidate["rag_chunks.jsonl"]):
        facts = canonical[part["record_id"]]
        citation = {
            "source_id": "generated_f3:" + part["record_id"],
            "source_kind": "ai_generated_reference",
            "title": part["citation_label"],
            "url": None,
            "evidence_path": "f3_records.jsonl",
            "record_id": part["record_id"],
            "field": part["field"],
            "authored_by": "Codex",
            "method": "codex_authored_detailed_reference_v2",
            "official_source_citation": False,
            "canonical_identity_citation": facts["citation"],
            **part["locator"],
        }
        chunk = common_chunk(
            "F3",
            part["field"],
            part["text"],
            facts["scope"],
            citation,
            "generated",
            code=part["course_code"],
            record_id=part["record_id"],
        )
        chunk.update(
            academic_verified=False,
            official_answer_available=False,
            official_content=None,
            official_objectives=None,
            official_assessment=None,
            unit_index=part["unit_index"],
        )
        f3.append(chunk)
    f1, f2 = _rows(inherited["f1_chunks.jsonl"]), _rows(inherited["f2_chunks.jsonl"])
    unified = sorted(f1 + f2 + f3, key=lambda c: (c["family"], c["scope"]["major"], c["chunk_id"]))
    questions = evaluation_questions(f1 + f2, list(canonical.values()))
    questions += [
        {
            "question_id": RELEASE_ID + ":" + c["chunk_id"],
            "query": c["course_code"] + " " + c["field"] + " tham khảo?",
            "family": "F3",
            "major": c["scope"]["major"],
            "program_id": c["scope"]["program_id"],
            "course_code": c["course_code"],
            "field": c["field"],
            "expected_chunk_ids": [c["chunk_id"]],
            "allow_generated": True,
            "expected_mode": "disclosed_generated_reference",
            "type": "exposed_release_structure_check_not_semantic_acceptance",
        }
        for c in f3
    ]
    counts = {"F1": len(f1), "F2": len(f2), "F3": len(f3)}
    quality = {
        "schema_version": "2.0",
        "release_id": RELEASE_ID,
        "family_counts": counts,
        "total_chunks": len(unified),
        "f2_memberships": len(canonical),
        "f3_records": len(records),
        "f1_f2_preserved_from": "hus-data-20261031-v3",
        "f3_fields": ["content", "objectives"],
        "active_runtime_release": False,
        "all_official_academic_facts_verified": False,
        "human_review_count": 0,
        "llm_quality_accepted": False,
    }
    return {
        "f3_records.jsonl": candidate["records.jsonl"],
        "f3_chunks.jsonl": jsonl(f3),
        "chunks.jsonl": jsonl(unified),
        "evaluation/questions.jsonl": jsonl(questions),
        "quality_report.json": encoded(quality),
    }


def build_release(parent: Path = PARENT, candidate: Path = CANDIDATE) -> dict[str, bytes]:
    parent_manifest, parent_files = _capture(Path(parent))
    if digest(parent_files["manifest.json"]) != SOURCE_MANIFEST_SHA:
        raise ValueError("Unpinned parent release")
    _, candidate_files = _capture(Path(candidate))
    _check_candidate(candidate_files)
    inherited = {k: v for k, v in parent_files.items() if k not in REPLACED | {"manifest.json"}}
    output = {
        **inherited,
        **_derived(inherited, candidate_files),
        PARENT_FILE: parent_files["manifest.json"],
        **{PREFIX + name: raw for name, raw in candidate_files.items()},
    }
    manifest = {
        "schema_version": "2.0",
        "release_id": RELEASE_ID,
        "f3_detail": DESCRIPTOR,
        "input_identity": parent_manifest["input_identity"],
        "implementation": {
            "f3_runtime_release.py": digest(Path(__file__).read_bytes().replace(b"\r\n", b"\n"))
        },
        "files": {
            name: {"bytes": len(raw), "sha256": digest(raw)} for name, raw in sorted(output.items())
        },
    }
    manifest["release_sha256"] = digest(encoded(manifest))
    return {**output, "manifest.json": encoded(manifest)}


def validate_detail_release(root: Path) -> dict:
    manifest, files = _capture(Path(root))
    unsigned = {k: v for k, v in manifest.items() if k != "release_sha256"}
    if (
        manifest.get("schema_version") != "2.0"
        or manifest.get("release_id") != RELEASE_ID
        or manifest.get("f3_detail") != DESCRIPTOR
        or digest(encoded(unsigned)) != manifest.get("release_sha256")
    ):
        raise ValueError("Detailed release identity/policy differs")
    if digest(files[PARENT_FILE]) != SOURCE_MANIFEST_SHA:
        raise ValueError("Unpinned parent manifest")
    parent = json.loads(files[PARENT_FILE])
    inherited_names = set(parent["files"]) - REPLACED
    inherited = {}
    for name in inherited_names:
        raw = files[name]
        if parent["files"][name] != {"bytes": len(raw), "sha256": digest(raw)}:
            raise ValueError("Inherited parent asset differs: " + name)
        inherited[name] = raw
    candidate = {
        name.removeprefix(PREFIX): raw for name, raw in files.items() if name.startswith(PREFIX)
    }
    _check_candidate(candidate)
    expected = {
        **inherited,
        **_derived(inherited, candidate),
        PARENT_FILE: files[PARENT_FILE],
        **{PREFIX + name: raw for name, raw in candidate.items()},
        "manifest.json": files["manifest.json"],
    }
    if files != expected or manifest["input_identity"] != parent["input_identity"]:
        raise ValueError("Derived F3 release binding differs")
    return {
        "validation": "pass",
        "release_sha256": manifest["release_sha256"],
        "files": len(manifest["files"]),
        "chunks": len(_rows(files["chunks.jsonl"])),
        "family_counts": json.loads(files["quality_report.json"])["family_counts"],
        "f2_records": 290,
        "f3_records": 290,
        "evaluation_questions": len(_rows(files["evaluation/questions.jsonl"])),
    }


def stage_preview(release: Path, out: Path) -> None:
    """Write a new explicit preview root; never modify an existing selector."""
    out = Path(out).resolve()
    protected = [
        Path("data/hus/rag").resolve(),
        Path("data/hus/qa").resolve(),
        Path("data/hus/evaluation").resolve(),
        Path(release).resolve(),
    ]
    if out.exists() or any(out.is_relative_to(p) or p.is_relative_to(out) for p in protected):
        raise ValueError("Preview must be a new isolated directory")
    validate_detail_release(release)
    destination = out / "releases" / RELEASE_ID
    destination.parent.mkdir(parents=True)
    shutil.copytree(release, destination)
    manifest = json.loads((destination / "manifest.json").read_bytes())
    (out / "CURRENT.json").write_bytes(
        encoded(
            {
                "schema_version": "2.0",
                "state": "prepared_preview_not_shared_selection",
                "release_id": RELEASE_ID,
                "release_path": "releases/" + RELEASE_ID,
                "release_sha256": manifest["release_sha256"],
                "index_entrypoint": "chunks.jsonl",
                "generated_reference_requires_opt_in": True,
            }
        )
    )
