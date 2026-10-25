"""Explicit reauthentication only when VNU expires; no real account or network."""

import json
import mimetypes
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import session_payload


def main():
    root = Path(__file__).resolve().parents[2] / "app" / "static"
    evidence = Path("backups/portal_reuse_20261025")
    evidence.mkdir(parents=True, exist_ok=True)
    state = {"authenticated": True, "missing": False, "job_error": None, "hold_reauth": False}
    calls, pending, errors, console_errors, failed_sync = [], [], [], [], []
    sample = {"subject": "synthetic-only", "expires_in": 1800,
              "profile": {"name": "Synthetic student", "program": "Synthetic program"},
              "snapshot": {"attempts": [], "source_summary": [], "unknown_rows": []}}

    def route_request(route):
        request = route.request
        path = urlsplit(request.url).path
        calls.append(path)
        if path == "/auth/session":
            route.fulfill(json=session_payload(state['authenticated']))
        elif path == "/me/profile":
            route.fulfill(json=sample)
        elif path == "/me/portal-sync":
            assert request.post_data is None, "Sync must not submit credentials or cookie state"
            if state["missing"]:
                route.fulfill(status=200, json={'state': 'reauth_required'})
            else:
                route.fulfill(status=202, json={"id": "synthetic-job"})
        elif path == "/me/portal-reauth":
            body = json.loads(request.post_data)
            assert body == {"password": "synthetic-password"}
            if state["hold_reauth"]:
                pending.append(route)
            else:
                state["missing"] = False
                route.fulfill(status=202, json={"id": "synthetic-job"})
        elif path == "/me/portal-sync/synthetic-job":
            error = state["job_error"]
            route.fulfill(json={"state": "failed", "error": error} if error
                          else {"state": "done", "result": "unchanged"})
        elif path == "/auth/logout":
            state["authenticated"] = False
            route.fulfill(json={"logged_out": True})
        elif path.startswith(("/auth/", "/me/")):
            raise AssertionError(f"Unexpected API: {path}")
        else:
            file = root / ("index.html" if path == "/" else path.removeprefix("/static/"))
            if file.is_file():
                route.fulfill(body=file.read_bytes(), content_type=mimetypes.guess_type(str(file))[0] or "text/plain")
            else:
                route.fulfill(status=404, body="")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.context.set_offline(True)
            page.route("**/*", route_request)
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.on('console', lambda message: console_errors.append(message.text) if message.type == 'error' else None)
            page.on('response', lambda response: failed_sync.append(response.status)
                    if urlsplit(response.url).path.startswith('/me/portal-sync') and response.status >= 400 else None)
            page.goto("http://127.0.0.1:8000/#profile")
            page.wait_for_function("!document.getElementById('portal-profile').hidden")

            def sync():
                page.locator("#portal-sync").click()
                page.wait_for_function("!document.getElementById('portal-sync').disabled")

            sync()
            assert page.locator("#portal-login").is_hidden()
            assert page.locator("#portal-reauth").is_hidden()
            assert calls.count("/me/portal-sync") == 1
            assert "/auth/portal" not in calls and "/me/portal-reauth" not in calls
            state["job_error"] = "portal_unavailable"
            sync()
            assert page.locator("#portal-reauth").is_hidden()
            assert "lỗi kỹ thuật" in page.locator("#portal-status").inner_text()

            state["job_error"] = "vnu_reauth_required"
            sync()
            assert page.locator("#portal-reauth").is_visible()
            assert page.locator("#portal-profile").is_visible()
            assert page.locator("#portal-login").is_hidden()
            assert page.locator("#portal-reauth-account").input_value() == "synthetic-only"
            assert page.locator("#portal-reauth-account").get_attribute("readonly") is not None
            page.locator("#portal-reauth-password").fill("synthetic-password")
            page.locator("#portal-reauth-dismiss").click()
            assert page.locator("#portal-reauth-password").input_value() == ""

            state["missing"] = True
            errors_before_expiry = len(console_errors)
            polls_before_expiry = calls.count('/me/portal-sync/synthetic-job')
            profile_reads_before_expiry = calls.count('/me/profile')
            sync()  # Pre-job expiry uses the same reauth flow as expiry inside a job.
            assert page.locator("#portal-reauth").is_visible()
            assert len(console_errors) == errors_before_expiry
            assert not failed_sync
            assert calls.count('/me/portal-sync/synthetic-job') == polls_before_expiry
            assert calls.count('/me/profile') == profile_reads_before_expiry
            for theme in ("light", "dark"):
                page.locator(f'[data-theme-choice="{theme}"]').click()
                for width in (1440, 390):
                    page.set_viewport_size({"width": width, "height": 1000})
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    page.screenshot(path=str(evidence / f"reauth-{theme}-{width}.png"), full_page=True)
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.locator('[data-language-choice="en"]').click()
            assert page.locator("#portal-reauth-submit").inner_text() == "Verify and update"
            state["job_error"] = None
            page.locator("#portal-reauth-password").fill("synthetic-password")
            page.locator("#portal-reauth-submit").click()
            page.wait_for_function("!document.getElementById('portal-sync').disabled")
            assert page.locator("#portal-reauth").is_hidden()
            assert page.locator("#portal-reauth-password").input_value() == ""
            assert page.locator("#portal-profile").is_visible()
            sync()
            assert calls.count("/me/portal-reauth") == 1

            state["missing"] = True
            sync()
            state["hold_reauth"] = True
            page.locator("#portal-reauth-password").fill("synthetic-password")
            page.locator("#portal-reauth-submit").click()
            page.wait_for_timeout(100)
            assert pending
            before = calls.count("/me/portal-sync/synthetic-job")
            page.locator("#system-logout").click()
            page.wait_for_function("!document.getElementById('portal-sync').disabled")
            pending.pop().fulfill(status=202, json={"id": "synthetic-job"})
            page.wait_for_timeout(100)
            assert page.locator("#portal-reauth").is_hidden()
            assert page.locator("#portal-profile").is_hidden()
            assert page.locator("#portal-reauth-account").input_value() == ""
            assert page.locator("#portal-reauth-password").input_value() == ""
            assert calls.count("/me/portal-sync/synthetic-job") == before
            assert not errors, errors
        finally:
            browser.close()
    print("Portal reauth: password-free sync, source expiry, technical error, explicit reauth, logout race and VI/EN/mobile passed")


if __name__ == "__main__":
    main()
