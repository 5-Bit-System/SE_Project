"""Adapt one immutable portable release to the existing RAG query interfaces.

Upstream validation modules are imported unchanged from a543cf8d. Legacy data is never
read here: canonical F2, F1, F3 and review state all come from the same release snapshot.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.hus.data_release import checked_path, digest, encoded, f2_data
from app.hus.rag_loader import DEFAULT_RAG_ROOT, HUSRAGData, RAGChunk, RAGDataError, Row
from app.hus.release_validation import validate_release


class PortableRAGData(HUSRAGData):
    _identity: Row
    _citation_context: Row

    @property
    def release_identity(self) -> Row:
        return deepcopy(self._identity)

    @property
    def citation_context(self) -> Row:
        return deepcopy(self._citation_context)


def _rows(payloads: dict[str, bytes], name: str) -> list[Row]:
    return [json.loads(line) for line in payloads[name].splitlines() if line.strip()]


def _snapshot(root: Path) -> tuple[Row, Row, dict[str, bytes]]:
    current = json.loads((root / "CURRENT.json").read_bytes())
    if (not isinstance(current, dict) or current["schema_version"] != "2.0" or current["index_entrypoint"] != "chunks.jsonl"
            or current["generated_reference_requires_opt_in"] is not True):
        raise RAGDataError("Unsupported release pointer/policy")
    path = checked_path(root, current["release_path"])
    manifest_raw = (path / "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
        raise RAGDataError("Invalid portable manifest")
    unsigned = {k: v for k, v in manifest.items() if k != "release_sha256"}
    if (digest(encoded(unsigned)) != current["release_sha256"]
            or manifest["release_sha256"] != current["release_sha256"]
            or manifest["release_id"] != current["release_id"]):
        raise RAGDataError("Portable release identity differs from CURRENT")
    payloads = {"manifest.json": manifest_raw}
    expected = set(manifest["files"]) | {"manifest.json"}
    present = {p.relative_to(path).as_posix() for p in path.rglob("*") if p.is_file()}
    if present != expected:
        raise RAGDataError("Portable release inventory differs")
    for name, identity in manifest["files"].items():
        raw = checked_path(path, name).read_bytes()
        if len(raw) != identity["bytes"] or digest(raw) != identity["sha256"]:
            raise RAGDataError(f"Portable file changed: {name}")
        payloads[name] = raw
    # Validate only the bytes captured above. Validation and later adaptation must
    # not observe two filesystem versions if a deployment changes CURRENT/files.
    with TemporaryDirectory(prefix="hus-release-validation-") as temporary:
        snapshot = Path(temporary)
        for name, raw in payloads.items():
            target = checked_path(snapshot, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        validate_release(snapshot)
    return current, manifest, payloads


def load_current(root: Path = DEFAULT_RAG_ROOT) -> PortableRAGData:
    try:
        current, manifest, payloads = _snapshot(Path(root).resolve())
        data = PortableRAGData()
        data._manifest = manifest
        data._identity = {"release_id": current["release_id"], "release_sha256": current["release_sha256"],
                          "format": "portable-2.0", "source_state": current["state"]}
        canonical = payloads["evidence/canonical_f2.json"]
        records = {r["record_id"]: r for r in _rows(payloads, "f2_records.jsonl")}
        programs = {r["program_id"]: r for r in _rows(payloads, "programs.jsonl")}
        data._program_records = {}
        data._program_groups = {}
        groups = _rows(payloads, "groups.jsonl")
        # Reproduce only in memory using the pinned source/provenance. This
        # binds review, variant, URL/blob and pointer as well as numeric facts.
        _, _, expected_programs, expected_groups, _ = f2_data(
            json.loads(canonical), json.loads(payloads["input_manifest.json"]))
        if _rows(payloads, "programs.jsonl") != expected_programs or groups != expected_groups:
            raise RAGDataError("Program/group facts, scope, review or citation differ from canonical snapshot")
        for program in programs.values():
            scope = program["scope"]
            key = (scope["major"], scope["curriculum_version"])
            if key in data._program_records:
                raise RAGDataError("Ambiguous program scope")
            data._program_records[key] = deepcopy(program)
            selected = [group for group in groups if group["program_id"] == program["program_id"]]
            data._program_groups[key] = tuple(deepcopy(selected))
        # Reuse the structured table joins, not F2 text chunks, for exact lookups.
        first_citation = next(iter(records.values()))["citation"]
        comparison = {"source": {"url": first_citation["url"], "git_blob_sha": first_citation["source_git_blob"]},
                      "release_identity": data.release_identity}
        data._courses = data._load_f2({"f2/hus_source.json": canonical,
                                      "f2/source_comparison.json": json.dumps(comparison).encode()})
        for key, course in tuple(data._courses.items()):
            pid = course.course_metadata["program_id"]
            record = records[f"{pid}:{course.course_code}"]
            # Import exact signed-off state; never propagate one program's review.
            data._courses[key] = replace(
                course, review_status=record["catalog_review"]["status"],
                unresolved_prerequisites=tuple(record["prerequisites"]["external_codes"]),
                has_prerequisite_conflict=record["prerequisites"]["has_conflict"],
                provenance={**course.provenance, "catalog_review": record["catalog_review"],
                            "prerequisite_review": record["prerequisites"],
                            "portable_record": record, "release_identity": data.release_identity})
        sources = {s["source_id"]: s for s in _rows(payloads, "sources.jsonl")}
        data._citation_context = {"sources": sources,
                                  "recovered_pages": _rows(payloads, "evidence/recovered_text.jsonl"),
                                  "canonical_pdfs": json.loads(payloads["input_manifest.json"])["pdfs"],
                                  "release_identity": data.release_identity}
        f3_records = {r["record_id"]: r for r in _rows(payloads, "f3_records.jsonl")}
        chunks = {"f1": [], "f3": []}
        for chunk in _rows(payloads, "chunks.jsonl"):
            family = chunk["family"].lower()
            if family not in chunks:
                continue  # F2 stays structured; no duplicate semantic/text import.
            scope, citation = chunk["scope"], chunk["citation"]
            meta = {**deepcopy(chunk), "portable_chunk": deepcopy(chunk), **data.release_identity,
                    "major": scope["major"], "program_variant": scope["program_variant"],
                    "source_url": citation["url"], "academic_verified": False}
            meta.pop("text", None)
            if family == "f1":
                source_record = sources[citation["source_id"]]
                meta.update(document_id=citation["source_id"], unit_id=chunk["source_unit_id"],
                            title=citation["title"], citation_title=citation["title"],
                            program_version=scope["curriculum_version"], admission_cohort="unknown",
                            source_content_hash=citation["source_sha256"],
                            review_status=citation["review_status"], review_scope=source_record["review_scope"],
                            review={"status": citation["review_status"]}, source_record=source_record,
                            raw_original_verified=citation["raw_original_verified"],
                            answer_eligible=True, usage_scope="descriptive", validity_status="unknown",
                            locator={"start_char": citation["start_char"], "end_char": citation["end_char"],
                                     "evidence_path": citation["evidence_path"], "field": "content_markdown"})
            else:
                record = f3_records[chunk["record_id"]]
                meta.update(course_name=record["course_name"], major_name=programs[scope["program_id"]]["major_name"],
                            program_id=scope["program_id"], cohort_year=scope["cohort_year"],
                            curriculum_version=scope["curriculum_version"], review_status=record["review_status"],
                            provenance=record["provenance"], warning=record["warning"],
                            dataset_kind=record["dataset_kind"], usage_scope=record["usage_scope"],
                            citation_label=f"F3 do AI sinh — {record['course_code']} — {record['major_name']}",
                            locator={"record_id": record["record_id"], "field": chunk["field"],
                                     "evidence_path": citation["evidence_path"]})
            meta["locator"]["release_id"] = current["release_id"]
            version = scope["curriculum_version"]
            name = f"{family}_chunks.jsonl"
            chunks[family].append(RAGChunk(family, chunk["chunk_id"], chunk["text"], scope["major"], version,
                                           meta, current["release_path"] + "/" + name,
                                           hashlib.sha256(payloads[name]).hexdigest()))
        data._chunks = {kind: tuple(values) for kind, values in chunks.items()}
        return data
    except RAGDataError:
        raise
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError, StopIteration) as exc:
        raise RAGDataError(f"Cannot load pinned portable release: {exc}") from exc
