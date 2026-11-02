"""Citation identity, truthful availability and actual binary delivery contracts."""

import hashlib
import io
from dataclasses import replace
from types import SimpleNamespace
import zipfile

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from app.api.routes import hus_answerer, router
from app.hus.answering import HUSAnswerer
from app.hus.citation_assets import CitationAssetError, CitationAssets, DOCX_TYPE, PDF_TYPE
from app.hus.citations import CitationResolver
from app.hus.data_release import encoded
from app.hus.rag_loader import HUSRAGData
from app.hus.retrieval import _body
from app.schemas.hus import HUSCitation, HUSQuestion


def _pdf():
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               b"<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>"]
    raw, offsets = b"%PDF-1.4\n", [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(raw))
        raw += f"{number} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(raw)
    raw += b"xref\n0 5\n0000000000 65535 f \n"
    raw += b"".join(f"{offset:010} 00000 n \n".encode() for offset in offsets[1:])
    return raw + f"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


def _registry(root, raw=None, kind="pdf", **updates):
    raw = _pdf() if raw is None else raw
    sha = hashlib.sha256(raw).hexdigest()
    root.mkdir(exist_ok=True)
    (root / f"{sha}.{kind}").write_bytes(raw)
    entry = {"sha256": sha, "bytes": len(raw), "path": f"{sha}.{kind}", "file_type": kind,
             "page_count": 2 if kind == "pdf" else None, "filename": "Source." + kind, **updates}
    registry = {"release_sha256": "a" * 64, "assets": {sha: entry}}
    registry["registry_sha256"] = hashlib.sha256(encoded(registry)).hexdigest()
    (root / "registry.json").write_bytes(encoded(registry))
    return CitationAssets(root, "a" * 64, {sha}), sha


@pytest.fixture(scope="module")
def current():
    return HUSRAGData.load_current()


def test_real_release_sources_are_typed_hash_bound_and_review_is_preserved(current):
    resolver = CitationResolver(current)
    kinds = set()
    for major in current.program_scopes().values():
        # program_scopes maps program IDs to (major, version).
        for chunk in current.chunks("f1", major=major[0]):
            citation = resolver.chunk(chunk, _body(chunk), 1)
            kinds.add(citation.evidence_kind)
            assert citation.review_status == chunk.metadata["review_status"]
            if citation.evidence_kind in {"pdf", "file"}:
                assert citation.availability == "available" and citation.open_url
                assert citation.document_sha256 in resolver.assets.allowed
                if citation.evidence_kind == "pdf" and not citation.pdf_pages:
                    assert "Chưa xác định được trang" in citation.availability_note
            else:
                assert citation.evidence_kind == "web"
                assert citation.open_url == citation.source_url
    assert kinds == {"pdf", "file", "web"}


def test_generated_identity_wins_over_incidental_pdf_metadata(current):
    resolver = CitationResolver(current)
    chunk = current.chunks("f3", major="data_science", allow_generated=True)[0]
    chunk = replace(chunk, metadata=chunk.metadata | {"source_url": "https://example.test/ai.pdf"})
    citation = resolver.chunk(chunk, _body(chunk), 1)
    assert citation.evidence_kind == "ai" and citation.display_label == "kiến thức AI"
    assert citation.open_url is citation.source_url is citation.document_sha256 is None
    invalid = citation.model_dump() | {"source_url": "https://example.test/official.pdf"}
    with pytest.raises(ValidationError):
        HUSCitation.model_validate(invalid)


def test_quote_mapping_spanning_repeated_and_unknown_pages():
    resolver = object.__new__(CitationResolver)
    resolver.pages = {"s": [{"page": 2, "text": "Mục tiêu duy nhất"},
                            {"page": 3, "text": "Nội dung khác"},
                            {"page": 4, "text": "Mục tiêu lặp"}]}
    assert resolver._quote_pages("s", "tiêu duy nhất Nội dung") == [2, 3]
    assert resolver._quote_pages("s", "Mục tiêu") == []
    assert resolver._quote_pages("s", "không có") == []
    assert resolver._quote_pages("s", "Muc tieu") == []  # Accents carry source identity.


def test_assets_verify_actual_served_bytes_after_cached_inspection(tmp_path):
    assets, sha = _registry(tmp_path)
    assert assets.inspect(sha, 2)["page_count"] == 2
    raw, info = assets.read(sha, 2)
    assert raw.startswith(b"%PDF-") and info["media_type"] == PDF_TYPE
    (tmp_path / assets.entries[sha]["path"]).write_bytes(raw + b"tampered")
    with pytest.raises(CitationAssetError, match="checksum") as error:
        assets.read(sha, 2)
    assert error.value.status == 409 and error.value.availability == "hash_mismatch"


@pytest.mark.parametrize("page", [0, 3, True])
def test_invalid_physical_page(tmp_path, page):
    assets, sha = _registry(tmp_path)
    with pytest.raises(CitationAssetError) as error:
        assets.read(sha, page)
    assert error.value.status == 422


@pytest.mark.parametrize("update", [{"path": "../outside.pdf"}, {"page_count": 99}])
def test_registry_cannot_escape_or_misdeclare_page_count(tmp_path, update):
    assets, sha = _registry(tmp_path, **update)
    with pytest.raises(CitationAssetError):
        assets.read(sha)


def test_invalid_pdf_missing_and_unknown_assets(tmp_path):
    assets, sha = _registry(tmp_path, b"Not a PDF")
    with pytest.raises(CitationAssetError) as error:
        assets.read(sha)
    assert error.value.availability == "invalid_file"
    with pytest.raises(CitationAssetError) as error:
        assets.read("b" * 64)
    assert error.value.status == 404
    missing = CitationAssets(tmp_path / "absent", "a" * 64, {sha})
    with pytest.raises(CitationAssetError):
        missing.read(sha)
    mismatched = CitationAssets(tmp_path, "b" * 64, {sha})
    with pytest.raises(CitationAssetError):
        mismatched.read(sha)
    registry = tmp_path / "registry.json"
    registry.write_bytes(registry.read_bytes().replace(b'Source.pdf', b'Changed.pdf'))
    tampered = CitationAssets(tmp_path, "a" * 64, {sha})
    with pytest.raises(CitationAssetError):
        tampered.read(sha)


def _client(assets):
    application = FastAPI()
    application.include_router(router)
    application.dependency_overrides[hus_answerer] = lambda: SimpleNamespace(
        citation_resolver=SimpleNamespace(assets=assets))
    return TestClient(application)


def test_http_pdf_binary_ranges_head_and_integrity_failure(tmp_path):
    assets, sha = _registry(tmp_path)
    client, url = _client(assets), f"/hus/sources/{sha}?page=2"
    response = client.get(url)
    assert response.status_code == 200 and response.content == _pdf()
    assert response.headers["content-type"] == PDF_TYPE
    assert response.headers["content-disposition"].startswith("inline;")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert hashlib.sha256(response.content).hexdigest() == sha
    partial = client.get(url, headers={"Range": "bytes=0-4"})
    assert partial.status_code == 206 and partial.content == b"%PDF-"
    assert partial.headers["content-range"].startswith("bytes 0-4/")
    assert client.get(url, headers={"Range": "bytes=-5"}).content == _pdf()[-5:]
    assert client.get(url, headers={"Range": "bytes=99999-"}).status_code == 416
    assert client.get(url, headers={"Range": "bytes=0-2,4-6"}).status_code == 416
    assert client.head(url).content == b"" and int(client.head(url).headers["content-length"]) == len(_pdf())
    assert client.get(url.replace("page=2", "page=3")).status_code == 422
    assert client.get("/hus/sources/unknown").status_code == 404
    (tmp_path / assets.entries[sha]["path"]).write_bytes(b"wrong")
    assert client.get(url).status_code == 409


def test_docx_is_attachment_without_pdf_page(tmp_path):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("word/document.xml", "<document/>")
    assets, sha = _registry(tmp_path, stream.getvalue(), "docx")
    client = _client(assets)
    response = client.get(f"/hus/sources/{sha}")
    assert response.status_code == 200 and response.headers["content-type"] == DOCX_TYPE
    assert response.headers["content-disposition"].startswith("attachment;")
    assert client.get(f"/hus/sources/{sha}?page=1").status_code == 422


def test_missing_store_does_not_hide_evidence_or_invent_links(current, tmp_path):
    answerer = HUSAnswerer(current, asset_root=tmp_path)
    answer = answerer.answer(HUSQuestion(question="Số tín chỉ MAT3533", major="data_science", version="QD3569-2023"))
    assert answer.status == "answered" and answer.facts["value"] == 3
    assert all(c.open_url is None and c.availability == "missing" for c in answer.citations)
    assert "chưa khả dụng" in answer.reply


def test_schema_rejects_wrong_hash_page_and_web_rewrites(current):
    answerer = HUSAnswerer(current)
    citation = answerer.answer(HUSQuestion(question="Số tín chỉ MAT3533", major="data_science", version="QD3569-2023")).citations[0]
    for updates in [{"document_sha256": "b" * 64}, {"pdf_page": 1},
                    {"open_url": "https://example.test/source.pdf"}, {"availability": "missing"}]:
        with pytest.raises(ValidationError):
            HUSCitation.model_validate(citation.model_dump() | updates)
    web = citation.model_dump() | {"evidence_kind": "web", "pdf_page": None, "pdf_pages": [],
                                  "source_url": "https://example.test/source", "open_url": "https://evil.test/"}
    with pytest.raises(ValidationError):
        HUSCitation.model_validate(web)
