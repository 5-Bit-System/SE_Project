"""Read the packaged F1/F2/F3 handoff without publishing an index or changing review.

Checksums validate a local package snapshot, not academic accuracy or current source review.
F1 version labels and F2/F3 decision identifiers are deliberately not interchangeable.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Literal


DEFAULT_RAG_ROOT = Path(__file__).resolve().parents[2] / "data/hus/rag"
MAJOR_CODES = {
    "7460101": "mathematics",
    "7460117": "mathematics_informatics",
    "7480113QTD": "computer_science",
    "7460108": "data_science",
}
ChunkDataset = Literal["f1", "f3"]
Row = dict[str, Any]


class RAGDataError(ValueError):
    """The package is incomplete, inconsistent or has changed since it was built."""


@dataclass(frozen=True)
class RAGChunk:
    dataset: ChunkDataset
    chunk_id: str
    text: str
    major: str
    version: str
    metadata: Row
    package_path: str
    package_sha256: str


@dataclass(frozen=True)
class F2Course:
    course_code: str
    major: str
    version: str
    review_status: str
    course: Row
    curriculum: Row
    membership: Row
    source_rows: tuple[Row, ...]
    groups: tuple[Row, ...]
    prerequisites: tuple[Row, ...]
    course_metadata: Row
    unresolved_prerequisites: tuple[str, ...]
    has_prerequisite_conflict: bool
    provenance: Row


def _object(raw: bytes, label: str) -> Row:
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise RAGDataError(f"Invalid JSON: {label}") from exc
    if not isinstance(value, dict):
        raise RAGDataError(f"Expected JSON object: {label}")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RAGDataError(f"Expected nonempty string: {label}")
    return value


def _major(value: str) -> str:
    if value not in MAJOR_CODES.values():
        raise RAGDataError(f"Unsupported major: {value}")
    return value


def _unique(rows: list[Row], *keys: str) -> dict[tuple, Row]:
    result = {}
    for row in rows:
        identity = tuple(row[k] for k in keys)
        if identity in result:
            raise RAGDataError(f"Duplicate identity {keys}: {identity}")
        result[identity] = row
    return result


def _package(root: Path) -> tuple[Row, dict[str, bytes]]:
    manifest = _object((root / "manifest.json").read_bytes(), "manifest.json")
    payloads = {}
    if not isinstance(manifest.get("files"), list):
        raise RAGDataError("Manifest must contain a files list")
    for entry in manifest["files"]:
        name = _text(entry["path"], "manifest path")
        relative = PurePosixPath(name)
        target = (root / name).resolve()
        if (relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name
                or not target.is_relative_to(root) or name != relative.as_posix()):
            raise RAGDataError(f"Invalid package path: {name}")
        if name in payloads:
            raise RAGDataError(f"Duplicate manifest path: {name}")
        raw = target.read_bytes()
        if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise RAGDataError(f"Package checksum/size mismatch: {name}")
        payloads[name] = raw
    return manifest, payloads


class HUSRAGData:
    """Explicitly loaded snapshot. Reload after changing the package or its reviews.

    Queries return independent copies, including nested metadata. There is no implicit
    fallback between majors/versions, no ranking and no write to the legacy review gate.
    """

    _manifest: Row
    _courses: dict[tuple, F2Course]
    _chunks: dict[str, tuple[RAGChunk, ...]]

    @classmethod
    def load(cls, root: Path = DEFAULT_RAG_ROOT) -> HUSRAGData:
        """Explicit legacy-format audit loader; runtime selection uses load_current()."""
        root = Path(root).resolve()
        try:
            manifest, payloads = _package(root)
            instance = cls()
            instance._manifest = manifest
            instance._courses = instance._load_f2(payloads)
            instance._chunks = {
                dataset: instance._load_chunks(dataset, payloads)
                for dataset in ("f1", "f3")
            }
            return instance
        except RAGDataError:
            raise
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise RAGDataError(f"Cannot load RAG package {root}: {exc}") from exc

    @property
    def manifest(self) -> Row:
        return deepcopy(self._manifest)

    @classmethod
    def load_current(cls, root: Path = DEFAULT_RAG_ROOT) -> HUSRAGData:
        """Strict portable selection; a missing/bad CURRENT never falls back to legacy."""
        from app.hus.portable_adapter import load_current
        return load_current(root)

    @property
    def release_identity(self) -> Row:
        raw = (json.dumps(self._manifest, ensure_ascii=False, sort_keys=True) + "\n").encode()
        return {"release_id": "legacy-" + hashlib.sha256(raw).hexdigest()[:16],
                "release_sha256": hashlib.sha256(raw).hexdigest(), "format": "legacy"}

    @property
    def citation_context(self) -> Row:
        return {"sources": {}, "recovered_pages": [], "canonical_pdfs": [],
                "release_identity": self.release_identity}

    def program_scopes(self) -> dict[str, tuple[str, str]]:
        result = {}
        for course in self._courses.values():
            pid = course.course_metadata["program_id"]
            scope = (course.major, course.version)
            if pid in result and result[pid] != scope:
                raise RAGDataError(f"Ambiguous program identity: {pid}")
            result[pid] = scope
        return result

    def chunks(
        self, dataset: ChunkDataset, *, major: str, version: str | None = None,
        course_code: str | None = None, field: str | None = None,
        program_variant: str | None = None, allow_generated: bool = False,
    ) -> tuple[RAGChunk, ...]:
        """Filter exact identities; an explicit version excludes unknown versions.

        F1 uses program_version (e.g. '2015'), F3 uses curriculum_version
        (e.g. 'QD3569-2023'). A course_code filter only matches F3 chunks.
        """
        if dataset not in self._chunks:
            raise RAGDataError(f"Unsupported chunk dataset: {dataset}")
        if type(allow_generated) is not bool:
            raise RAGDataError("allow_generated must be a boolean")
        _major(major)
        if version is not None:
            _text(version, "version")
        code = _text(course_code, "course_code").strip().upper() if course_code is not None else None
        return deepcopy(tuple(
            c for c in self._chunks[dataset]
            if c.major == major and (version is None or c.version == version)
            and (allow_generated or c.metadata.get("content_origin") != "generated")
            and (code is None or c.metadata.get("course_code") == code)
            and (field is None or c.metadata.get("field") == field)
            and (program_variant is None or c.metadata.get("program_variant") == program_variant)
        ))

    def get_f2_course(self, course_code: str, *, major: str, version: str) -> F2Course | None:
        """Return the exact curriculum membership, never a global-code fallback.

        Prerequisite group_no and raw source rows are preserved, not evaluated.
        Missing/reference-only courses return None; unknown majors raise RAGDataError.
        """
        code = _text(course_code, "course_code").strip().upper()
        return deepcopy(self._courses.get((code, _major(major), _text(version, "version"))))

    def get_f2_program(self, *, major: str, version: str) -> Row | None:
        """Portable, exact-scope program snapshot; no legacy/source fallback."""
        return deepcopy(getattr(self, "_program_records", {}).get(
            (_major(major), _text(version, "version"))))

    def f2_group_rules(self, *, major: str, version: str) -> tuple[Row, ...]:
        """Independent parent/child rows in recorded order, never aggregated."""
        return deepcopy(getattr(self, "_program_groups", {}).get(
            (_major(major), _text(version, "version")), ()))

    def f2_courses(self, *, major: str, version: str) -> tuple[F2Course, ...]:
        """Scoped memberships for exact name resolution; no cross-edition fallback."""
        scope = (_major(major), _text(version, "version"))
        return deepcopy(tuple(course for course in self._courses.values()
                              if (course.major, course.version) == scope))

    def _load_f2(self, payloads: dict[str, bytes]) -> dict[tuple, F2Course]:
        path = "f2/hus_source.json"
        bundle = _object(payloads[path], path)
        comparison = _object(payloads["f2/source_comparison.json"], "f2/source_comparison.json")
        tables = bundle["tables"]
        courses = _unique(tables["courses"], "course_code")
        curricula = _unique(tables["curricula"], "curriculum_id")
        _unique(tables["curricula"], "major_code", "curriculum_version")
        memberships = _unique(tables["curriculum_courses"], "curriculum_id", "course_code")
        groups = _unique(tables["official_curriculum_groups"], "curriculum_id", "group_key")
        metadata = _unique(bundle["course_metadata"], "program_id", "code")
        source_rows, prerequisites = defaultdict(list), defaultdict(list)
        for table, target in (("official_curriculum_entries", source_rows),
                              ("course_prerequisites", prerequisites)):
            for row in tables[table]:
                if (row["curriculum_id"], row["course_code"]) not in memberships:
                    raise RAGDataError(f"F2 {table} row has no curriculum membership")
                target[row["curriculum_id"], row["course_code"]].append(row)
        review = bundle["prerequisite_pdf_review"]
        result = {}
        for membership in tables["curriculum_courses"]:
            cid, code = membership["curriculum_id"], membership["course_code"]
            curriculum = curricula[cid,]
            major_code, version = curriculum["major_code"], curriculum["curriculum_version"]
            major = MAJOR_CODES[major_code]
            _text(version, "curriculum_version")
            entries = source_rows[cid, code]
            if not entries:
                raise RAGDataError(f"F2 membership has no source rows: {cid}/{code}")
            manifests = [m for m in bundle["metadata_source_manifest"]
                         if m["decision"] == version and m["cohort_year"] == curriculum["cohort_year"]]
            statuses = {m["status"] for m in manifests}
            if len(statuses) != 1:
                raise RAGDataError(f"Missing or ambiguous F2 source status: {cid}/{code}")
            if not {e["pdf_document"] for e in entries} <= {m["source_ref"] for m in manifests}:
                raise RAGDataError(f"F2 source rows differ from source manifest: {cid}/{code}")
            # The program prefix is not guessed from a display name or curriculum number.
            candidates = [m for (_, c), m in metadata.items() if c == code
                          and m["program_id"].endswith(f"_{major_code.lower()}_{curriculum['cohort_year']}")]
            if len(candidates) != 1:
                raise RAGDataError(f"Missing or ambiguous F2 course metadata: {cid}/{code}")
            prereqs = prerequisites[cid, code]
            mentioned_prerequisites = {p["prerequisite_course_code"] for p in prereqs}
            for entry in entries:
                # Unresolved references may intentionally be absent from parsed edges.
                mentioned_prerequisites.update(re.findall(r"\b[A-Z]{3}\d{4}[A-Z]?\b",
                                                          entry.get("prerequisite_source_text") or ""))
            group_keys = dict.fromkeys([membership["course_group"]] + [e["group_key"] for e in entries])
            result[code, major, version] = F2Course(
                course_code=code, major=major, version=version, review_status=next(iter(statuses)),
                course=courses[code,], curriculum=curriculum, membership=membership,
                source_rows=tuple(entries), groups=tuple(groups[cid, key] for key in group_keys),
                prerequisites=tuple(prereqs), course_metadata=candidates[0],
                unresolved_prerequisites=tuple(sorted(mentioned_prerequisites & set(review["unresolved_codes"]))),
                has_prerequisite_conflict=any(c["major_code"] == major_code and c["course_code"] == code
                                              for c in review["conflicting_courses"]),
                provenance={"package_path": path, "package_sha256": hashlib.sha256(payloads[path]).hexdigest(),
                            "source_description": bundle["source"], "source_comparison": comparison,
                            "metadata_source_archive": bundle["metadata_source_archive"],
                            "source_manifests": manifests, "prerequisite_pdf_review": review,
                            "source_row_pointers": [f"/tables/official_curriculum_entries/{i}"
                                                   for i, e in enumerate(tables["official_curriculum_entries"])
                                                   if e["curriculum_id"] == cid and e["course_code"] == code]},
            )
        return result

    def _load_chunks(self, dataset: ChunkDataset, payloads: dict[str, bytes]) -> tuple[RAGChunk, ...]:
        path = f"{dataset}/rag_chunks.jsonl"
        raw = payloads[path]
        result, ids = [], set()
        for line, content in enumerate(raw.splitlines(), 1):
            if not content.strip():
                continue
            row = _object(content, f"{path}:{line}")
            chunk_id = _text(row["chunk_id"], "chunk_id")
            if chunk_id in ids:
                raise RAGDataError(f"Duplicate chunk_id: {path}:{line}")
            ids.add(chunk_id)
            text, major = _text(row["text"], "chunk text"), _major(row["major"])
            version_key = "program_version" if dataset == "f1" else "curriculum_version"
            version = _text(row[version_key], version_key)
            if dataset == "f1":
                review = row["review"]
                if (row["answer_eligible"] is not True or row["review_status"] not in {"include", "include_markdown"}
                        or review["status"] != row["review_status"] or row["usage_scope"] != "descriptive"):
                    raise RAGDataError(f"F1 chunk is not approved for descriptive use: {chunk_id}")
                _text(row["source_url"], "F1 source_url")
            else:
                if (row["content_origin"] != "generated" or row["academic_verified"] is not False
                        or row["review_status"] != "needs_review" or row["disclosure_required"] is not True
                        or row["usage_scope"] != "reference_only"
                        or not text.startswith(_text(row["warning"], "F3 warning"))
                        or not row["citation_label"].startswith("F3 do AI sinh — ")):
                    raise RAGDataError(f"F3 generated-reference labels are inconsistent: {chunk_id}")
                course = self._courses.get((row["course_code"], major, version))
                if (course is None or row["cohort_year"] != course.curriculum["cohort_year"]
                        or row["program_id"] != course.course_metadata["program_id"]):
                    raise RAGDataError(f"F3 has no matching F2 membership: {chunk_id}")
            result.append(RAGChunk(dataset, chunk_id, text, major, version,
                                   {k: v for k, v in row.items() if k != "text"},
                                   path, hashlib.sha256(raw).hexdigest()))
        return tuple(result)
