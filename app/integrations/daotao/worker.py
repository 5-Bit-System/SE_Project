"""Isolated browser process; credentials are stdin only and output is never logged."""

import json
import sys
from urllib.parse import urlsplit

from app.integrations.daotao.client import DaotaoClient
from app.integrations.daotao.session_state import HOST, MAX_INPUT_BYTES, validated_cookies
from app.integrations.daotao.snapshot import (
    PortalFailure,
    snapshot,
    source_profile,
    verified_subject,
)


def portal_context(browser):
    """Use the same restricted browser context for the worker and startup probe."""
    context = browser.new_context(accept_downloads=False, service_workers="block")
    context.route("**/*", lambda route: route.continue_()
                  if urlsplit(route.request.url).hostname == "daotao.vnu.edu.vn"
                  else route.abort())
    context.set_default_timeout(15000)
    return context


def browser_error_code(stage, error):
    """Classify only the observed Chromium code; never return provider text."""
    if stage in {"browser_start", "browser_context"}:
        return "browser_unavailable"
    if "net::ERR_NETWORK_ACCESS_DENIED" in str(error):
        return "network_access_denied"
    return "portal_unavailable"


def write_result(result):
    """The parent expects UTF-8 bytes, regardless of the Windows console locale."""
    sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.flush()


def collect(credentials):
    stage = "browser_start"
    try:
        from playwright.sync_api import Error, TimeoutError, sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, channel="chrome")
            try:
                stage = "browser_context"
                context = portal_context(browser)
                client = DaotaoClient(context)
                mode = credentials.get("mode", "login")
                if mode in {"login", "signin"}:
                    stage = "login"
                    expected_subject = credentials["username"]
                    authenticated_subject = client.login(expected_subject, credentials["password"])
                elif mode == "resume":
                    stage = "resume"
                    if set(credentials) != {"mode", "subject", "cookies"}:
                        raise PortalFailure("portal_state_invalid")
                    expected_subject = credentials["subject"]
                    if not isinstance(expected_subject, str) or not 0 < len(expected_subject) <= 128:
                        raise PortalFailure("portal_state_invalid")
                    authenticated_subject = client.resume(expected_subject, credentials["cookies"])
                else:
                    raise PortalFailure("portal_state_invalid")
                # A fresh accepted student-portal login establishes identity;
                # failures fetching academic data must not invent a snapshot.
                subject = verified_subject('', expected_subject, authenticated_subject=authenticated_subject)
                payload, details, warning = None, None, None
                try:
                    stage = "profile"
                    texts = client.read_profile_texts()
                    verified_subject('\n'.join(texts), expected_subject,
                                     authenticated_subject=authenticated_subject)
                    stage = "transcript"
                    client.open_transcript()
                    for page in context.pages:
                        for frame in page.frames:
                            texts.append(frame.locator("body").inner_text())
                    stage = "identity"
                    subject = verified_subject("\n".join(texts), expected_subject,
                                               authenticated_subject=authenticated_subject)
                    stage = "parse"
                    rows, evidence = client.read_transcript_capture()
                    payload = snapshot(rows, evidence)
                    details = source_profile(texts)
                except (Error, PortalFailure) as exc:
                    if mode != 'signin' or (isinstance(exc, PortalFailure) and str(exc) != 'structure_changed'):
                        raise
                    warning = 'source_unavailable'
                cookies = validated_cookies([cookie for cookie in context.cookies()
                                             if cookie.get("domain") in {HOST, "." + HOST}])
                result = {"subject": subject, "snapshot": payload,
                          "profile": details, "cookies": cookies}
                if mode == 'signin':
                    result.update(authenticated=True, warning=warning)
                return result
            finally:
                browser.close()
    except ImportError:
        code, kind = "browser_unavailable", "missing_dependency"
    except PortalFailure as exc:
        code, kind = str(exc), "source_rejected"
    except TimeoutError:
        code, kind = "timeout", "timeout"
    except Error as exc:
        code = browser_error_code(stage, exc)
        kind = "browser_error"
    except Exception:
        code, kind = "portal_unavailable", "unexpected_error"
    # Never include exception messages, DOM, credentials or provider responses.
    return {"error": code, "stage": stage, "kind": kind}


if __name__ == "__main__":
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise PortalFailure("portal_state_invalid")
        request = json.loads(raw.decode("utf-8"))
        if not isinstance(request, dict):
            raise PortalFailure("portal_state_invalid")
        result = collect(request)
        request.clear()
    except PortalFailure as exc:
        result = {"error": str(exc)}
    except ImportError:
        result = {"error": "browser_unavailable"}
    except Exception:
        result = {"error": "portal_unavailable"}
    write_result(result)
