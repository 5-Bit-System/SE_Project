"""Portable F3 v2 derives from sealed evidence without changing parent families."""

import json
from pathlib import Path

import pytest

PARENT = Path("data/hus/rag/releases/hus-data-20261031-v3")
CANDIDATE = Path("data/hus/qa/20261110/f3_reference_v2/release")


@pytest.fixture(scope="module")
def built():
    from app.hus.f3_runtime_release import build_release

    return build_release(PARENT, CANDIDATE)


def save(output, root):
    root.mkdir()
    for name, raw in output.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return root


def rows(raw):
    return [json.loads(line) for line in raw.splitlines()]


def reseal(output):
    from app.hus.data_release import digest, encoded

    manifest = json.loads(output["manifest.json"])
    manifest["files"] = {
        k: {"bytes": len(v), "sha256": digest(v)} for k, v in output.items() if k != "manifest.json"
    }
    manifest.pop("release_sha256")
    manifest["release_sha256"] = digest(encoded(manifest))
    output["manifest.json"] = encoded(manifest)


def test_inherits_exact_f1_f2_sources_facts_and_aliases(built):
    for name in (
        "f1_chunks.jsonl",
        "f2_chunks.jsonl",
        "f2_records.jsonl",
        "programs.jsonl",
        "groups.jsonl",
        "sources.jsonl",
        "search_aliases.jsonl",
        "evidence/canonical_f2.json",
    ):
        assert built[name] == (PARENT / name).read_bytes()
    assert built["f3_records.jsonl"] == (CANDIDATE / "records.jsonl").read_bytes()
    f3 = rows(built["f3_chunks.jsonl"])
    assert len(f3) == 1753 and {c["field"] for c in f3} == {"content", "objectives"}
    assert len({c["chunk_id"] for c in f3}) == 1753
    assert all(
        c["content_origin"] == "generated"
        and c["disclosure_required"]
        and c["citation"]["url"] is None
        for c in f3
    )


def test_new_release_validates_standalone_and_parent_still_valid(built, tmp_path):
    from app.hus.release_validation import validate_release

    report = validate_release(save(built, tmp_path / "v4"))
    assert report["validation"] == "pass" and report["family_counts"]["F3"] == 1753
    assert validate_release(PARENT)["family_counts"]["F3"] == 870


def test_every_quote_offset_and_example_binds_to_sealed_record(built):
    from app.hus.f3_detail import section_texts

    records = {r["record_id"]: r for r in rows(built["f3_records.jsonl"])}
    for c in rows(built["f3_chunks.jsonl"]):
        loc = c["citation"]
        field = section_texts(records[c["record_id"]])[c["field"]]
        quote = field[loc["start_char"] : loc["end_char"]]
        assert c["text"].endswith(quote)
        assert c["scope"] == records[c["record_id"]]["f2_identity"]["scope"]


@pytest.mark.parametrize(
    "mutation",
    [
        "f1",
        "f2",
        "f3_text",
        "f3_scope",
        "mixed",
        "official",
        "candidate",
        "candidate_extra",
        "parent",
    ],
)
def test_resealed_tampering_is_rejected(built, tmp_path, mutation):
    from app.hus.data_release import jsonl
    from app.hus.release_validation import validate_release

    output = dict(built)
    if mutation in {"f1", "f2"}:
        name = mutation + "_chunks.jsonl"
        values = rows(output[name])
        values[0]["text"] += " tampered"
        output[name] = jsonl(values)
    elif mutation in {"f3_text", "f3_scope", "mixed", "official"}:
        name = "f3_chunks.jsonl"
        values = rows(output[name])
        if mutation == "f3_text":
            values[0]["text"] += " fabricated"
        elif mutation == "f3_scope":
            values[0]["scope"]["major"] = "foreign"
        elif mutation == "official":
            values[0]["official_answer_available"] = True
        else:
            values.append(rows((PARENT / name).read_bytes())[0])
        output[name] = jsonl(values)
    elif mutation == "candidate":
        name = "evidence/f3_v2/candidate/records.jsonl"
        output[name] += b"\n"
    elif mutation == "candidate_extra":
        output["evidence/f3_v2/candidate/extra.json"] = b"{}\n"
    else:
        output["evidence/f3_v2/parent_manifest.json"] = b"{}\n"
    reseal(output)
    with pytest.raises(ValueError):
        validate_release(save(output, tmp_path / "v4"))


def test_cli_preview_is_explicit_and_never_changes_shared_selection(built, tmp_path):
    from app.hus.f3_runtime_release import stage_preview
    from app.hus.rag_loader import HUSRAGData

    release = save(built, tmp_path / "v4")
    pointer = Path("data/hus/rag/CURRENT.json").read_bytes()
    out = tmp_path / "preview"
    stage_preview(release, out)
    data = HUSRAGData.load_current(out)
    assert data.release_identity["release_id"] == json.loads(built["manifest.json"])["release_id"]
    assert Path("data/hus/rag/CURRENT.json").read_bytes() == pointer
    with pytest.raises(ValueError):
        stage_preview(release, out)
    with pytest.raises(ValueError):
        stage_preview(release, Path("data/hus/rag"))


def test_deterministic_build_and_cli_verify(built, tmp_path):
    from app.hus.f3_runtime_release import build_release
    from tools.prepare_hus_f3_runtime import main

    assert build_release(PARENT, CANDIDATE) == built
    root = save(built, tmp_path / "v4")
    assert main(["verify", "--out", str(root)]) == 0
    with pytest.raises(SystemExit):
        main(["build", "--out", str(root)])
