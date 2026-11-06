"""Content-addressed source files. Never fetch a caller URL or serve a caller path."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import re
import zipfile

import pdfplumber

from app.hus.data_release import checked_path, encoded

DEFAULT_ASSET_ROOT = Path(__file__).resolve().parents[2] / "data/hus/citation_assets"
PDF_TYPE = "application/pdf"
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class CitationAssetError(ValueError):
    def __init__(self, status: int, availability: str, message: str):
        super().__init__(message)
        self.status, self.availability = status, availability


class CitationAssets:
    def __init__(self, root: Path, release_sha256: str, allowed: set[str]):
        self.root, self.allowed = Path(root).resolve(), frozenset(allowed)
        self.entries = {}
        self.problem = None
        self._checked = {}
        try:
            registry = json.loads((self.root / "registry.json").read_bytes())
            unsigned = {k: v for k, v in registry.items() if k != "registry_sha256"}
            if (registry["release_sha256"] != release_sha256
                    or hashlib.sha256(encoded(unsigned)).hexdigest() != registry["registry_sha256"]
                    or not isinstance(registry["assets"], dict)):
                raise ValueError("Registry binding changed")
            self.entries = registry["assets"]
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            self.problem = "Kho tệp dẫn chứng chưa khả dụng hoặc không khớp release."

    def _entry(self, asset_id: str):
        if not re.fullmatch(r"[0-9a-f]{64}", asset_id) or asset_id not in self.allowed or asset_id not in self.entries:
            raise CitationAssetError(404, "missing", self.problem or "Chưa có bản tệp nguồn đã kiểm để mở.")
        entry = self.entries[asset_id]
        try:
            if entry["sha256"] != asset_id or entry["file_type"] not in {"pdf", "docx"}:
                raise ValueError("Invalid asset entry")
            if (type(entry["bytes"]) is not int or entry["bytes"] < 1
                    or not isinstance(entry["filename"], str) or not entry["filename"]
                    or (entry["file_type"] == "pdf" and
                        (type(entry["page_count"]) is not int or entry["page_count"] < 1))):
                raise ValueError("Invalid asset metadata")
            path = checked_path(self.root, entry["path"])
        except (ValueError, KeyError, TypeError):
            raise CitationAssetError(409, "unavailable", "Thông tin tệp nguồn không hợp lệ.") from None
        return entry, path

    def _verify(self, asset_id: str, entry, raw: bytes):
        if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != asset_id:
            raise CitationAssetError(409, "hash_mismatch", "Tệp nguồn không khớp checksum; không mở bản khác thay thế.")
        try:
            if entry["file_type"] == "pdf":
                if not raw.startswith(b"%PDF-"):
                    raise ValueError("Not PDF")
                with pdfplumber.open(io.BytesIO(raw)) as pdf:
                    pages = len(pdf.pages)
                if pages < 1 or pages != entry["page_count"]:
                    raise ValueError("Page count differs")
                return {"media_type": PDF_TYPE, "page_count": pages, "filename": entry["filename"]}
            with zipfile.ZipFile(io.BytesIO(raw)) as doc:
                if "word/document.xml" not in doc.namelist():
                    raise ValueError("Not DOCX")
            return {"media_type": DOCX_TYPE, "page_count": None, "filename": entry["filename"]}
        except CitationAssetError:
            raise
        except Exception as exc:
            raise CitationAssetError(409, "invalid_file", "Tệp không phải PDF/DOCX hợp lệ đã đăng ký.") from exc

    def inspect(self, asset_id: str, page: int | None = None) -> dict:
        entry, path = self._entry(asset_id)
        try:
            stat = path.stat()
            signature = (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
            cached = self._checked.get(asset_id)
            if cached is None or cached[0] != signature:
                info = self._verify(asset_id, entry, path.read_bytes())
                self._checked[asset_id] = (signature, info)
            else:
                info = cached[1]
        except OSError:
            raise CitationAssetError(404, "missing", "Tệp nguồn đang thiếu hoặc không đọc được.") from None
        self._page(info, page)
        return info.copy()

    @staticmethod
    def _page(info, page):
        if page is not None and (info["media_type"] != PDF_TYPE or type(page) is not int
                                 or page < 1 or page > info["page_count"]):
            raise CitationAssetError(422, "invalid_page", "Trang PDF được yêu cầu không tồn tại.")

    def read(self, asset_id: str, page: int | None = None) -> tuple[bytes, dict]:
        entry, path = self._entry(asset_id)
        try:
            raw = path.read_bytes()
        except OSError:
            raise CitationAssetError(404, "missing", "Tệp nguồn đang thiếu hoặc không đọc được.") from None
        # Always hash the bytes actually served, regardless of cached inspection/stat.
        info = self._verify(asset_id, entry, raw)
        self._page(info, page)
        return raw, info
