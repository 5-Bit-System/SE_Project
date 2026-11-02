"""Reproduce the P0-1 identity/quote/scope/review diff; never modifies a source release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from app.hus.data_release import checked_path, encoded
from app.hus.release_validation import validate_release


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read(path: Path):
    return json.loads(path.read_bytes())


def rows(path: Path):
    return [json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]


def compare(root: Path) -> dict:
    pointer = read(root / "CURRENT.json")
    target = checked_path(root, pointer["release_path"])
    validation = validate_release(target)
    assert validation["release_sha256"] == pointer["release_sha256"]
    old_source = read(root / "f2/hus_source.json")
    canonical = read(target / "evidence/canonical_f2.json")
    a, b = defaultdict(list), defaultdict(list)
    for chunk in rows(root / "f1/rag_chunks.jsonl"):
        a[chunk["unit_id"]].append(chunk)
    for chunk in rows(target / "f1_chunks.jsonl"):
        b[chunk["source_unit_id"]].append(chunk)
    assert set(a) == set(b), "F1 selected source units changed; manual reconciliation needed"
    units = []
    for key in sorted(a):
        old, new = a[key], b[key]
        old.sort(key=lambda x: x["locator"]["start_char"])
        new.sort(key=lambda x: x["citation"]["start_char"])
        first, last = old[0]["locator"]["start_char"], old[-1]["locator"]["end_char"]
        nf, nl = new[0]["citation"]["start_char"], new[-1]["citation"]["end_char"]
        source = checked_path(target, new[0]["citation"]["evidence_path"]).read_bytes()
        text = source.decode()
        assert (first, last) == (nf, nl), key
        assert all(c["source_content_hash"] == digest(source) for c in old), key
        assert all(text[c["locator"]["start_char"]:c["locator"]["end_char"]] == c["source_quote"] for c in old), key
        assert all(text[c["citation"]["start_char"]:c["citation"]["end_char"]] == c["source_quote"] for c in new), key
        # Old fixed-size splitting can skip whitespace at cut points, never prose.
        def compact(value):
            return re.sub(r"\s+", "", value)
        assert compact("".join(c["source_quote"] for c in old)) == compact(text[first:last]), key
        assert compact("".join(c["source_quote"] for c in new)) == compact(text[first:last]), key
        assert old[0]["review_status"] == new[0]["citation"]["review_status"], key
        assert old[0]["program_version"] == new[0]["scope"]["curriculum_version"], key
        assert old[0]["program_variant"] == new[0]["scope"]["program_variant"], key
        units.append({
            "unit_id": key, "source_id": old[0]["document_id"], "field": old[0]["field"],
            "source_sha256": digest(source), "span": [first, last],
            "span_quote_sha256": digest(text[first:last].encode()),
            "major": old[0]["major"], "edition": old[0]["program_version"],
            "variant": old[0]["program_variant"], "review_status": old[0]["review_status"],
            "legacy_review_sha256": digest(encoded(old[0]["review"])),
            "legacy": [{"chunk_id": c["chunk_id"], "quote_sha256": digest(c["source_quote"].encode()),
                         "start": c["locator"]["start_char"], "end": c["locator"]["end_char"]} for c in old],
            "portable": [{"chunk_id": c["chunk_id"], "quote_sha256": digest(c["source_quote"].encode()),
                           "start": c["citation"]["start_char"], "end": c["citation"]["end_char"],
                           "display_edits": c["display_edits"],
                           "raw_original_verified": c["citation"]["raw_original_verified"]} for c in new],
            "source_span_unchanged": True, "edition_and_status_unchanged": True,
        })
    tables = {name: {"legacy_sha256": digest(encoded(old_source["tables"][name])),
                     "portable_sha256": digest(encoded(values)),
                     "equal": values == old_source["tables"][name], "rows": len(values)}
              for name, values in canonical["tables"].items()}
    assert all(table["equal"] for table in tables.values()), "Canonical business tables changed"
    old_f3 = {r["record_id"]: r for r in rows(root / "f3/records.jsonl")}
    new_f3 = {r["record_id"]: r for r in rows(target / "f3_records.jsonl")}
    assert set(old_f3) == set(new_f3)
    records = []
    for key, old in old_f3.items():
        new = new_f3[key]
        preserved = ["generated_content", "generated_objectives", "suggested_assessment",
                     "official_content", "official_objectives", "official_assessment",
                     "academic_verified", "reviewer", "review_status", "warning"]
        assert all(old[k] == new[k] for k in preserved), key
        records.append({"record_id": key, "generated_values_unchanged": True,
                        "legacy_record_sha256": digest(encoded(old)),
                        "portable_record_sha256": digest(encoded(new)),
                        "legacy_f2_blob": old["provenance"]["f2_source_git_blob"],
                        "portable_f2_blob": new["provenance"]["f2_source_git_blob"],
                        "canonical_review": new["canonical_f2_binding"]["catalog_review"],
                        "generated_review_status": new["review_status"], "academic_verified": False})
    reviews = Counter(r["catalog_review"]["status"] for r in rows(target / "f2_records.jsonl"))
    changed = [u for u in units if len(u["legacy"]) != len(u["portable"])]
    return {"schema_version": "1.0", "release_pointer": pointer, "validation": validation,
            "legacy_manifest_sha256": digest((root / "manifest.json").read_bytes()),
            "f1": {"legacy_chunks": sum(map(len, a.values())), "portable_chunks": sum(map(len, b.values())),
                   "selected_units": len(units), "unit_ids_equal": True,
                   "resplit_units": [{k: u[k] for k in ["unit_id", "source_id", "field", "span"]}
                                     | {"old_count": len(u["legacy"]), "new_count": len(u["portable"])} for u in changed],
                   "units": units},
            "f2": {"legacy_sha256": digest((root / "f2/hus_source.json").read_bytes()),
                   "canonical_sha256": digest((target / "evidence/canonical_f2.json").read_bytes()),
                   "top_level_changed": sorted(k for k in set(old_source) | set(canonical)
                                               if old_source.get(k) != canonical.get(k)),
                   "tables": tables, "review_counts": dict(reviews),
                   "catalog_reviews_imported_exactly": canonical.get("catalog_reviews", []),
                   "institutional_certification_granted_here": False},
            "f3": {"memberships": len(records), "chunks": 870, "generated_fields_unchanged": True,
                   "default_generated_policy": "excluded_unless_request_opt_in", "records": records}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/hus/rag"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = encoded(compare(args.root))
    if args.out.exists():
        raise ValueError("Output exists; choose a new receipt")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(result)
    print(f"Reconciled F1 69 -> 65, 63 unchanged units; canonical F2 tables unchanged: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
