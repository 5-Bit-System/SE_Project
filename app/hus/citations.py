"""Build AI/PDF/web/file citations from the selected release, not generated URLs."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re
from urllib.parse import urlsplit

from app.hus.citation_assets import CitationAssetError, CitationAssets, DEFAULT_ASSET_ROOT
from app.hus.rag_loader import F2Course, HUSRAGData, RAGChunk
from app.hus.release_text import display_text
from app.schemas.hus import HUSCitation


def _compact(value):
    # Retain Vietnamese letters/accents so a different word cannot establish a page.
    return re.sub(r"[\W_]", "", display_text(value)[0].casefold())


def _web_url(value):
    if not isinstance(value, str) or any(c.isspace() for c in value):
        return None
    url = urlsplit(value)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password:
        return None
    return value


class CitationResolver:
    def __init__(self, data: HUSRAGData, asset_root: Path = DEFAULT_ASSET_ROOT):
        context = data.citation_context
        self.sources = context["sources"]
        self.pdfs = {p["source_ref"]: p for p in context["canonical_pdfs"]}
        allowed = {p["sha256"] for p in self.pdfs.values()}
        allowed.update(c["sha256"] for s in self.sources.values()
                       if (c := s.get("recovered_capture")) and c["file_type"] in {"pdf", "docx"})
        self.assets = CitationAssets(asset_root, data.release_identity["release_sha256"], allowed)
        pages = defaultdict(list)
        for page in context["recovered_pages"]:
            pages[page["document_id"]].append(page)
        self.pages = {key: sorted(values, key=lambda v: v["page"]) for key, values in pages.items()}

    def _file(self, base, sha, kind, pages=None, note=None):
        pages = pages or []
        base.update(evidence_kind=kind, display_label=base["label"], document_sha256=sha,
                    pdf_page=pages[0] if pages else None, pdf_pages=pages,
                    open_url=None, availability="missing", availability_note=note)
        try:
            if not sha:
                raise CitationAssetError(404, "missing", "Chưa có bản nguồn đã kiểm để mở.")
            info = self.assets.inspect(sha, base["pdf_page"])
            if pages and pages[-1] > info["page_count"]:
                raise CitationAssetError(422, "invalid_page", "Trang PDF không khớp văn bản.")
            url = f"/hus/sources/{sha}"
            if pages:
                url += f"?page={pages[0]}#page={pages[0]}"
            if kind == "pdf" and not pages:
                note = "Chưa xác định được trang trích dẫn; mở toàn văn PDF." + (" " + note if note else "")
            base.update(open_url=url, availability="available", media_type=info["media_type"], availability_note=note)
        except CitationAssetError as exc:
            base.update(availability=exc.availability, availability_note=str(exc))
        return HUSCitation(**base)

    def _quote_pages(self, source_id, quote):
        needle = _compact(quote)
        pages = self.pages.get(source_id, [])
        values = [_compact(p["text"]) for p in pages]
        joined = "".join(values)
        if not needle:
            return []
        matches = []
        start = joined.find(needle)
        while start >= 0:
            end, cursor, found = start + len(needle), 0, []
            for page, value in zip(pages, values):
                if cursor < end and cursor + len(value) > start:
                    found.append(page["page"])
                cursor += len(value)
            matches.append(found)
            start = joined.find(needle, start + 1)
        return matches[0] if matches and all(m == matches[0] for m in matches) else []

    def chunk(self, chunk: RAGChunk, quote: str, number: int) -> HUSCitation:
        meta = chunk.metadata
        label = meta.get("citation_title", meta.get("citation_label", meta.get("title", chunk.chunk_id)))
        base = dict(citation_id=str(number), dataset=chunk.dataset, label=label,
                    source_url=_web_url(meta.get("source_url")), quote=quote, locator=meta["locator"],
                    review_status=meta["review_status"], content_origin=meta["content_origin"],
                    metadata={**meta, "package_path": chunk.package_path, "package_sha256": chunk.package_sha256})
        if meta["content_origin"] == "generated":
            base.update(label=f"kiến thức AI — {meta.get('course_code', '')} — {meta.get('course_name', '')}",
                        display_label="kiến thức AI", evidence_kind="ai", source_url=None,
                        source_id=meta.get("record_id"), availability="available", open_url=None)
            return HUSCitation(**base)
        sid = meta.get("document_id")
        source = self.sources.get(sid, meta.get("source_record", {}))
        capture = source.get("recovered_capture") or {}
        kind = capture.get("file_type")
        suffix = urlsplit(base["source_url"] or "").path.casefold()
        base["source_id"] = sid
        if kind == "pdf" or suffix.endswith(".pdf"):
            note = "Bản PDF khôi phục; chưa xác minh tương đương bản gốc lịch sử." if capture else None
            base["metadata"]["page_locator_basis"] = "normalized_quote_match_in_hash_bound_capture_not_visual_review"
            return self._file(base, capture.get("sha256"), "pdf", self._quote_pages(sid, quote), note)
        if kind == "docx" or suffix.endswith((".docx", ".doc")):
            return self._file(base, capture.get("sha256"), "file", note="Tệp DOCX nguồn; không phải PDF.")
        return HUSCitation(**base, evidence_kind="web" if base["source_url"] else "unavailable",
                           display_label=label, open_url=base["source_url"],
                           availability="unverified" if base["source_url"] else "unavailable",
                           availability_note="URL web nguồn; chưa kiểm tra truy cập lại trong request.")

    def course_row(self, course: F2Course, row: dict, number: int, quote: str) -> HUSCitation:
        record = course.provenance.get("portable_record", {})
        locators = record.get("citation", {}).get("pdf_locators", [])
        pdf = next((p for p in locators if p["document"] == row["pdf_document"] and p["page"] == row["pdf_page"]), {})
        source = self.pdfs.get(row["pdf_document"], {})
        sha = pdf.get("sha256", source.get("sha256"))
        base = dict(citation_id=str(number), dataset="f2", label=row["pdf_document"],
                    source_id="canonical_f2:" + row["pdf_document"], source_url=_web_url(pdf.get("url")),
                    quote=quote, locator=row, review_status=course.review_status,
                    content_origin="structured_source_draft",
                    metadata={"provenance": course.provenance, "course_metadata": course.course_metadata,
                              "source_row_pointer": course.provenance["source_row_pointers"][number - 1]})
        return self._file(base, sha, "pdf", [row["pdf_page"]],
                          "Trang vật lý theo bản chép nguồn; giữ nguyên trạng thái review học vụ.")


def citation_line(citation: HUSCitation) -> str:
    label = citation.label
    if citation.evidence_kind == "file":
        label = "Tệp DOCX — " + label
    if citation.pdf_pages:
        label += "; trang PDF " + ", ".join(map(str, citation.pdf_pages))
    if citation.open_url:
        label += "; " + citation.open_url
    if citation.availability_note:
        label += "; " + citation.availability_note
    return f"Nguồn [{citation.citation_id}]: {label}"
