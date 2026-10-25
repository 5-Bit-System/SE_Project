"""Create/check pinned inputs and build an offline HUS candidate corpus.

Run python -m tools.prepare_hus_corpus --help for commands. No HTTP or model calls.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

from pydantic import ValidationError
from app.hus.metadata import ApplicabilityFile

from app.hus.corpus import (
    BuildConfig, CorpusError, ReviewFile, SourceManifest, build_artifacts,
    create_source_manifest, initial_reviews, json_bytes, read_json, verify_artifacts,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = REPO_ROOT / "data/hus/corpus/build_config.json"


def write_new_file(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inventory = commands.add_parser("manifest", help="Pin current source files; refuses overwrite")
    inventory.add_argument("--source-root", type=Path, required=True)
    inventory.add_argument("--snapshot-id", required=True)
    inventory.add_argument("--source-location", required=True, help="Immutable Git/archive location")
    inventory.add_argument("--out", type=Path, required=True)
    review = commands.add_parser("init-reviews", help="Create an unapproved review queue")
    review.add_argument("--source-root", type=Path, required=True)
    review.add_argument("--manifest", type=Path, required=True)
    review.add_argument("--out", type=Path, required=True)
    for name in ("build", "verify"):
        command = commands.add_parser(name, help="Build new artifacts" if name == "build"
                                      else "Rebuild in memory and compare every output byte")
        command.add_argument("--source-root", type=Path, default=REPO_ROOT / "data/hus")
        command.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
        command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "manifest":
            manifest = create_source_manifest(args.source_root, args.snapshot_id, args.source_location)
            write_new_file(args.out, json_bytes(manifest.model_dump()))
            print(f"Pinned {manifest.document_count} documents / {len(manifest.files)} source files")
            return 0
        if args.command == "init-reviews":
            manifest = SourceManifest.model_validate(read_json(args.manifest))
            reviews = initial_reviews(args.source_root, manifest)
            write_new_file(args.out, json_bytes(reviews.model_dump()))
            print(f"Created {len(reviews.decisions)} unapproved review decisions")
            return 0
        config = BuildConfig.model_validate(read_json(args.config))
        manifest = SourceManifest.model_validate(read_json(args.config.parent / config.source_manifest))
        reviews = ReviewFile.model_validate(read_json(args.config.parent / config.review_decisions))
        out = args.out.resolve()
        root = args.source_root.resolve()
        if out == root or out.is_relative_to(root) or root.is_relative_to(out):
            raise CorpusError("Build output must be outside the source snapshot tree")
        applicability = (ApplicabilityFile.model_validate(read_json(args.config.parent / config.applicability_metadata))
                         if config.applicability_metadata else None)
        artifacts = build_artifacts(root, manifest, reviews, config, applicability)
        if args.command == "verify":
            verify_artifacts(out, artifacts)
            print(f"Verified byte-identical reproduction: {len(artifacts)} files")
        else:
            if out.exists():
                raise CorpusError(f"Output already exists; use a new build directory: {out}")
            out.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".hus-build-", dir=out.parent) as temp:
                staged = Path(temp) / "build"
                staged.mkdir()
                for name, data in artifacts.items():
                    write_new_file(staged / name, data)
                staged.rename(out)
            print(f"Created candidate build: {out}")
        report = json.loads(artifacts["validation_report.json"])
        print(f"Documents={report['document_count']}; review={report['review_counts']}; "
              f"chunks={report['chunk_count']}; active_release=False")
        return 0
    except (OSError, ValueError, KeyError, TypeError, ValidationError) as exc:
        print(f"Corpus preparation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
