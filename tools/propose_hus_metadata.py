"""Create evidence-bound metadata proposals for a pinned snapshot; never verify values."""

import argparse
from collections import Counter
from pathlib import Path

from app.hus.corpus import SourceManifest, json_bytes, read_json, verify_sources
from app.hus.metadata import ApplicabilityFile, propose_metadata, validate_metadata
from app.hus.models import MajorCategory
from app.hus.urls import canonicalize_url


def propose(root: Path, manifest: SourceManifest) -> ApplicabilityFile:
    docs = verify_sources(root, manifest)
    parents = {canonicalize_url(doc.url): propose_metadata(doc).major.proposed for doc in docs.values()}
    proposals = {}
    for key, doc in sorted(docs.items()):
        parent_major = MajorCategory(parents.get(canonicalize_url(doc.parent_url), "unknown")) if doc.parent_url else MajorCategory.UNKNOWN
        metadata = propose_metadata(doc, parent_major)
        # A proposal pass must not erase reviewed values already present on a source document.
        if doc.applicability.content_hash:
            from app.hus.metadata import assign_proposal

            assign_proposal(doc, parent_major)
            metadata = doc.applicability
        proposals[key] = validate_metadata(doc, metadata)
    return ApplicabilityFile(source_snapshot_id=manifest.source_snapshot_id, documents=proposals)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path("data/hus"))
    parser.add_argument("--manifest", type=Path, default=Path("data/hus/corpus/source_manifest.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        metadata = propose(args.source_root, SourceManifest.model_validate(read_json(args.manifest)))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("xb") as stream:
            stream.write(json_bytes(metadata.model_dump()))
        print(f"Proposed {len(metadata.documents)} documents: " + str(dict(Counter(
            doc.major.proposed for doc in metadata.documents.values()
        ))))
        return 0
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Metadata proposal failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
