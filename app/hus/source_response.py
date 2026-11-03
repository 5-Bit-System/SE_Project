"""Serve verified source bytes, including the single ranges used by PDF viewers."""

import re
from urllib.parse import quote

from fastapi import HTTPException, Request, Response

from app.hus.citation_assets import CitationAssetError, CitationAssets, PDF_TYPE


def source_response(request: Request, assets: CitationAssets, source_id: str, page: int | None) -> Response:
    try:
        raw, info = assets.read(source_id, page)
    except CitationAssetError as exc:
        raise HTTPException(exc.status, detail={"availability": exc.availability, "message": str(exc)}) from None
    size, status = len(raw), 200
    disposition = "inline" if info["media_type"] == PDF_TYPE else "attachment"
    extension = "pdf" if info["media_type"] == PDF_TYPE else "docx"
    headers = {"Accept-Ranges": "bytes", "ETag": f'"{source_id}"',
               "X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-cache",
               "Content-Disposition": f'{disposition}; filename="{source_id}.{extension}"; '
                                      f"filename*=UTF-8''{quote(info['filename'], safe='')}"}
    requested = request.headers.get("range") if request.method == "GET" else None
    if requested and request.headers.get("if-range", headers["ETag"]) == headers["ETag"]:
        match = re.fullmatch(r"bytes=(\d*)-(\d*)", requested)
        if not match or not any(match.groups()) or any(len(v) > 20 for v in match.groups()):
            raise HTTPException(416, "Invalid byte range", headers={"Content-Range": f"bytes */{size}"})
        start_text, end_text = match.groups()
        if start_text:
            start, end = int(start_text), int(end_text) if end_text else size - 1
        else:
            start, end = max(0, size - int(end_text)), size - 1
        if start >= size or end < start:
            raise HTTPException(416, "Unsatisfiable byte range", headers={"Content-Range": f"bytes */{size}"})
        end = min(end, size - 1)
        raw, status = raw[start:end + 1], 206
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    headers["Content-Length"] = str(len(raw))
    return Response(b"" if request.method == "HEAD" else raw, status_code=status,
                    headers=headers, media_type=info["media_type"])
