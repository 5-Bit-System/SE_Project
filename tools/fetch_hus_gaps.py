"""Fetch explicit gap URLs only, using existing robots/rate/allowlist/raw policies.

This creates acquisition evidence; it never alters a pinned snapshot or grants review.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import time
from urllib.parse import urlsplit

import httpx

from app.hus.allowlist import Allowlist
from app.hus.corpus import json_bytes, read_json
from app.hus.crawler import Robots, fetch_attachment, fetch_html
from app.hus.storage import RawStorage
from app.hus.urls import CrawlError


def fetch(config_path: Path, targets_path: Path, out: Path) -> dict:
    if out.exists():
        raise ValueError("Acquisition directory exists; choose a new run")
    allowlist = Allowlist.load(config_path)
    targets = read_json(targets_path)["targets"]
    out.mkdir(parents=True)
    storage = RawStorage(out)
    attempts = []
    # Record robots requests as well as blocked target attempts, without treating them as successes.
    def requested(request: httpx.Request) -> None:
        attempts.append({"url": str(request.url), "status": None,
                         "purpose": "robots" if request.url.path == "/robots.txt" else "source"})

    def observe(response: httpx.Response) -> None:
        for attempt in reversed(attempts):
            if attempt["url"] == str(response.request.url) and attempt["status"] is None:
                attempt["status"] = response.status_code
                break

    results = []
    with httpx.Client(timeout=15.0, event_hooks={"request": [requested], "response": [observe]}) as client:
        robots = Robots(client, allowlist.user_agent, delay_seconds=allowlist.delay_seconds)
        for target in targets:
            url = target["url"]
            row = {**target, "attempted_at": datetime.now(timezone.utc).isoformat(),
                   "review_status": "needs_review", "answer_eligible": False}
            ext = Path(urlsplit(url).path).suffix.lower().lstrip(".")
            try:
                method = fetch_attachment if ext in {"pdf", "docx"} else fetch_html
                final, headers, raw = method(url, allowlist, client, robots, sleep=time.sleep, headers={})
                if not raw:
                    raise CrawlError("Empty response without a usable archived version")
                if ext in {"pdf", "docx"}:
                    storage.save_raw_document(final, raw, ext, title=Path(urlsplit(final).path).name,
                                              content_type=headers.get("content-type"))
                else:
                    storage.save_raw_html(final, raw, title="targeted-discovery",
                                          content_type=headers.get("content-type"))
                row.update(status="captured_unreviewed", final_url=final,
                           raw_source=storage.archive.latest(final).model_dump())
            except (CrawlError, httpx.HTTPError) as exc:
                storage.archive.record_failure(url, str(exc))
                row.update(status="blocked", reason=str(exc))
            results.append(row)
    report = {"schema_version": "1.0", "results": results, "http_attempts": attempts,
              "policy": "Existing robots fail-closed, >=2s per host, no validators or recursive discovery",
              "snapshot_modified": False, "academic_review_completed": 0}
    (out / "report.json").write_bytes(json_bytes(report))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("data/hus/config/qa_sources.json"))
    parser.add_argument("--targets", type=Path, default=Path("data/hus/qa/20261028/targets.json"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = fetch(args.config, args.targets, args.out)
    print({status: sum(r["status"] == status for r in report["results"])
           for status in {r["status"] for r in report["results"]}})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
