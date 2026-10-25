"""Synthetic browser regression; never connects to VNU or uses real student data."""

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import EMPTY_PROFILE, session_payload


def main():
    evidence = Path("backups/portal_integration_20261023")
    evidence.mkdir(parents=True, exist_ok=True)
    state = {"authenticated": False, 'app': True}
    sample = {"subject": "synthetic-only", "fetched_at": "2026-10-23T00:00:00+00:00",
              "profile": {"name": "Sinh viên giả lập", "program": "Ngành nguồn thử",
                          "cohort": "79"},
              "snapshot": {"source_summary": [["Tổng tín chỉ: 6"]], "unknown_rows": [],
                           "attempts": [
                               {"term": "HỌC KỲ 1 - 2099-2100", "code": "TEST001E",
                                "name": "<script>synthetic</script>", "credits": "3",
                                "grade10": "8,5", "letter": "B+", "grade4": "3,5"},
                               {"term": "HỌC KỲ 2 - 2100-2101", "code": "TEST001E",
                                "name": "Môn giả lập", "credits": "3",
                                "grade10": "", "letter": "", "grade4": ""}]}}

    def intercept(route):
        path = route.request.url.split("8000")[-1]
        if path.startswith(("/auth/", "/me/")):
            if path == "/auth/session":
                result, code = session_payload(state['app'] and time.monotonic() < state.get('expires_at', float('inf'))), 200
            elif path == "/me/portal-connection":
                if state.get("challenge"):
                    result, code = {"detail": "interaction_required"}, 409
                else:
                    state["authenticated"] = True
                    result, code = {"authenticated": True}, 200
            elif path in {"/auth/logout", "/me/portal-data"}:
                state["authenticated"] = False
                if path == '/auth/logout':
                    state['app'] = False
                result, code = {}, 200
            elif state["authenticated"]:
                result, code = sample, 200
            else:
                result, code = EMPTY_PROFILE, 200
            route.fulfill(status=code, content_type="application/json", body=json.dumps(result))
        elif not route.request.url.startswith("http://127.0.0.1:8000/"):
            route.abort()
        else:
            route.continue_()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/")
        page.locator("#tab-btn-profile").click()
        page.wait_for_function("!document.getElementById('portal-submit').disabled")
        page.locator("#portal-username").fill("synthetic-only")
        page.locator("#portal-password").fill("synthetic-password")
        page.locator("#portal-show").click()
        assert page.locator("#portal-password").get_attribute("type") == "text"
        page.locator("#portal-submit").click()
        page.wait_for_function("!document.getElementById('portal-profile').hidden")
        assert page.locator("#portal-password").input_value() == ""
        assert page.locator("#portal-name").inner_text() == "Sinh viên giả lập"
        assert page.locator("#portal-program").inner_text() == "Ngành nguồn thử"
        assert page.locator("#portal-cohort").inner_text() == "79"
        assert page.locator("#portal-summary").inner_text() == "Tổng tín chỉ: 6"
        assert page.locator("#portal-sync").inner_text() == "Cập nhật bảng điểm"
        assert page.locator("#portal-table tbody tr:not(.portal-term)").count() == 2
        assert "2100-2101" in page.locator("#portal-table .portal-term").first.inner_text()
        assert "<script>synthetic</script>" in page.locator("#portal-table").inner_text()
        assert page.locator("#portal-table script").count() == 0
        for theme in ("light", "dark"):
            page.locator(f'[data-theme-choice="{theme}"]').click()
            for width in (1440, 390):
                page.set_viewport_size({"width": width, "height": 1000})
                page.screenshot(path=str(evidence / f"profile-{theme}-{width}.png"))
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.locator('[data-language-choice="en"]').click()
        assert page.locator("#portal-heading").inner_text() == "Academic profile"
        assert page.locator("#portal-summary").inner_text() == "Total credits: 6"
        assert page.locator("#portal-name").inner_text() == "Sinh viên giả lập"
        assert page.locator("#portal-program").inner_text() == "Ngành nguồn thử"
        assert page.locator("#portal-cohort").inner_text() == "79"
        assert page.locator("#portal-sync").inner_text() == "Update transcript"
        sample["profile"]["cohort"] = None
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        page.wait_for_function("document.getElementById('portal-cohort').textContent === 'Unavailable'")
        assert "Môn giả lập" in page.locator("#portal-table").inner_text()
        page.locator("#portal-delete").click()
        page.locator("#portal-keep").click()
        assert page.locator("#portal-confirm").is_hidden()
        # A response started before logout must never restore personal UI/chart state.
        pending = []
        page.route("**/me/profile", lambda route: pending.append(route))
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        page.wait_for_timeout(150)
        assert pending
        page.locator("#system-logout").click()
        page.wait_for_function("document.getElementById('portal-profile').hidden")
        for route in pending:
            route.fulfill(content_type="application/json", body=json.dumps(sample))
        page.wait_for_timeout(150)
        assert page.locator("#portal-table").inner_text() == ""
        assert page.locator("#portal-identity").inner_text() == ""
        for field in ("name", "program", "cohort"):
            assert page.locator(f"#portal-{field}").inner_text() == ""
        assert page.locator("#portal-profile").is_hidden()
        page.unroute("**/me/profile")
        # A new login still works, and local expiry clears all source DOM.
        state.update(app=True, authenticated=False)
        page.evaluate('window.systemAuth.refresh()')
        page.wait_for_function("document.body.dataset.authState === 'workspace'")
        sample["expires_in"] = 1
        page.locator("#portal-username").fill("synthetic-only")
        page.locator("#portal-password").fill("synthetic-password")
        page.locator("#portal-submit").click()
        page.wait_for_function("!document.getElementById('portal-profile').hidden")
        state['expires_at'] = time.monotonic() + .5
        page.wait_for_function("document.getElementById('portal-profile').hidden")
        assert page.locator("#portal-table").inner_text() == ""
        assert page.locator('#auth-student-form').is_visible()
        state.update(app=True, authenticated=False, expires_at=float('inf'))
        page.evaluate('window.systemAuth.refresh()')
        page.wait_for_function("document.body.dataset.authState === 'workspace'")
        state["challenge"] = True
        for language in ("en", "vi"):
            page.locator(f'[data-language-choice="{language}"]').click()
            page.locator("#portal-username").fill("synthetic-only")
            page.locator("#portal-password").fill("synthetic-password")
            page.locator("#portal-submit").click()
            page.wait_for_function("document.getElementById('portal-status').textContent.includes('CAPTCHA')")
            assert page.locator("#portal-profile").is_hidden()
            assert page.locator("#portal-password").input_value() == ""
        assert not errors, errors
        browser.close()
    print("Portal UI: synthetic login, source preservation, VI/EN, themes, mobile, logout passed")


if __name__ == "__main__":
    main()
