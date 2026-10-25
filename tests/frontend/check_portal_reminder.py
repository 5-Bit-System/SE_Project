"""Seven-day reminders and explicit sync, with synthetic data and no outbound requests."""

import mimetypes
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import session_payload


def main():
    static_root = Path(__file__).resolve().parents[2] / "app" / "static"
    evidence = Path("backups/portal_reminder_20261025")
    evidence.mkdir(parents=True, exist_ok=True)
    now = datetime(2099, 6, 20, 12, tzinfo=timezone.utc)
    state = {"authenticated": True, "job_error": "portal_unavailable"}
    requests, errors = [], []
    sample = {"subject": "synthetic-reminder", "expires_in": 1800,
              "fetched_at": (now - timedelta(days=30)).isoformat(),
              "last_synced_at": (now - timedelta(days=7) + timedelta(milliseconds=1)).isoformat(),
              "profile": {"name": "Synthetic reminder student"},
              "snapshot": {"attempts": [], "source_summary": [], "unknown_rows": []}}

    def intercept(route):
        path = urlsplit(route.request.url).path
        requests.append(path)
        if path == "/auth/session":
            route.fulfill(json=session_payload(state['authenticated']))
        elif path == "/me/profile":
            route.fulfill(json=sample)
        elif path == "/me/portal-sync":
            route.fulfill(status=202, json={"id": "synthetic-job", "state": "running"})
        elif path == "/me/portal-sync/synthetic-job":
            if state["job_error"]:
                route.fulfill(json={"state": "failed", "error": state["job_error"]})
            else:
                sample["last_synced_at"] = now.isoformat()
                route.fulfill(json={"state": "done", "result": "unchanged"})
        elif path == "/auth/logout":
            state["authenticated"] = False
            route.fulfill(json={"logged_out": True})
        elif path.startswith(("/auth/", "/me/")):
            raise AssertionError(f"Unexpected API: {path}")
        else:
            file = static_root / ("index.html" if path == "/" else path.removeprefix("/static/"))
            if file.is_file():
                route.fulfill(body=file.read_bytes(),
                              content_type=mimetypes.guess_type(str(file))[0] or "text/plain")
            else:
                route.fulfill(status=404, body="")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.add_init_script(f"Date.now = () => {int(now.timestamp() * 1000)};")
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route("**/*", intercept)
            page.goto("http://127.0.0.1:8000/#profile")
            page.wait_for_function("!document.getElementById('portal-profile').hidden")
            assert not page.locator(".transcript-refresh-bar.is-due").count()
            assert "Nhắc cập nhật tiếp theo" in page.locator("#portal-refresh-message").inner_text()
            assert page.locator(".source-notice:visible").count() == 0

            sample["last_synced_at"] = (now - timedelta(days=7)).isoformat()
            page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
            page.wait_for_function("document.querySelector('.transcript-refresh-bar').classList.contains('is-due')")
            assert "7 ngày" in page.locator("#portal-refresh-message").inner_text()
            # No reminder opens VNU or submits credentials automatically.
            assert requests.count("/me/portal-sync") == 0

            for theme in ("light", "dark"):
                page.locator(f'[data-theme-choice="{theme}"]').click()
                for width in (1440, 390):
                    page.set_viewport_size({"width": width, "height": 1000})
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    assert page.locator("#portal-sync").is_visible()
                    page.screenshot(path=str(evidence / f"{theme}-{width}.png"), full_page=True)
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.locator('[data-language-choice="en"]').click()
            assert "7 days" in page.locator("#portal-refresh-message").inner_text()
            assert page.locator("#portal-sync").inner_text() == "Update transcript"

            def update():
                page.locator("#tab-btn-dashboard").click()
                assert page.locator(".source-notice:visible").count() == 0
                page.locator("#portal-sync").click()
                assert page.evaluate("location.hash") == "#profile"
                page.wait_for_function("!document.getElementById('portal-sync').disabled")
                assert page.locator("#portal-login").is_hidden()
                assert page.locator("#portal-reauth").is_hidden()

            update()
            assert "technical error" in page.locator("#portal-status").inner_text()
            assert page.locator(".transcript-refresh-bar.is-due").count() == 1
            state["job_error"] = "incomplete_snapshot"
            update()
            assert "not verified complete" in page.locator("#portal-status").inner_text()
            assert page.locator(".transcript-refresh-bar.is-due").count() == 1
            state["job_error"] = None
            update()
            assert not page.locator(".transcript-refresh-bar.is-due").count()
            assert "Next update reminder" in page.locator("#portal-refresh-message").inner_text()
            assert sample["fetched_at"] == (now - timedelta(days=30)).isoformat()

            # Invalid or future timestamps never pretend data is fresh.
            for invalid in ("bad-date", (now + timedelta(days=1)).isoformat()):
                sample["last_synced_at"] = invalid
                page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
                page.wait_for_function("document.getElementById('portal-refresh-message').textContent.includes('unknown')")
                assert not page.locator(".transcript-refresh-bar.is-due").count()
                assert page.locator("#portal-refresh-time").inner_text() == ""

            for tab in ("rules", "recommend"):
                page.locator(f"#tab-btn-{tab}").click()
                assert page.locator(".source-notice:visible").count() == 1
            page.locator("#tab-btn-profile").click()
            page.locator("#system-logout").click()
            page.wait_for_function("!document.getElementById('portal-sync').disabled")
            assert page.locator("#portal-refresh-time").inner_text() == ""
            assert "Sign in" in page.locator("#portal-refresh-message").inner_text()
            assert page.locator('#auth-student-form').is_visible()
            assert requests.count("/me/portal-sync") == 3
            assert not errors, errors
        finally:
            browser.close()
    print("Portal reminders: 7-day boundary, manual sync, failure/unchanged results, privacy, VI/EN and mobile passed")


if __name__ == "__main__":
    main()
