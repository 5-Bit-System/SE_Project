"""Isolated browser process; credentials are stdin only and output is never logged."""

import json
import sys
from urllib.parse import urlsplit

from app.integrations.daotao.client import DaotaoClient
from app.integrations.daotao.snapshot import (
    PortalFailure,
    snapshot,
    source_profile,
    verified_subject,
)


def write_result(result):
    """The parent expects UTF-8 bytes, regardless of the Windows console locale."""
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.flush()


def collect(credentials):
    from playwright.sync_api import TimeoutError, sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, channel="chrome")
        try:
            context = browser.new_context(accept_downloads=False, service_workers="block")
            # Reject navigation/requests outside the reviewed portal host.
            context.route("**/*", lambda route: route.continue_()
                          if urlsplit(route.request.url).hostname == "daotao.vnu.edu.vn"
                          else route.abort())
            context.set_default_timeout(15000)
            client = DaotaoClient(context)
            authenticated_subject = client.login(credentials["username"], credentials["password"])
            texts = client.read_profile_texts()
            client.open_transcript()
            for page in context.pages:
                for frame in page.frames:
                    texts.append(frame.locator("body").inner_text())
            subject = verified_subject("\n".join(texts), credentials["username"],
                                       authenticated_subject=authenticated_subject)
            return {"subject": subject, "snapshot": snapshot(client.read_transcript()),
                    "profile": source_profile(texts)}
        except TimeoutError:
            raise PortalFailure("timeout") from None
        finally:
            browser.close()


if __name__ == "__main__":
    try:
        result = collect(json.loads(sys.stdin.read(8192)))
    except PortalFailure as exc:
        result = {"error": str(exc)}
    except ImportError:
        result = {"error": "browser_unavailable"}
    except Exception:
        result = {"error": "portal_unavailable"}
    write_result(result)
