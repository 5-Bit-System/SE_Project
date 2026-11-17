"""Portal enrollment automatically drives the board; all account/API data is invented."""

from copy import deepcopy
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.presentation_fixture import common_route


def main():
    state = {"owner": "a", "mode": "ready"}
    requests, pending, errors = [], [], []

    def profile():
        return {"subject": "synthetic-only", "profile": {
            "program": "Khoa học máy tính và thông tin" if state["owner"] == "a" else "Khoa học dữ liệu",
            "cohort": "68"}, "snapshot": {"schema_version": 1, "digest": state["owner"],
                "completeness": "complete", "attempts": [], "source_summary": [], "unknown_rows": []}}

    def board():
        def course(suffix):
            return {"code": state["owner"].upper() + suffix, "name": "Invented " + suffix,
                    "name_en": None, "credits": 3, "requirement_type": "required",
                    "counted_in_total": True, "groups": [], "reasons": [], "suggested": False}
        result = {"status": "ready", "blocking_reasons": [], "selections": {},
                  "courses": {"completed": [course("DONE")], "eligible": [course("NEXT")],
                              "blocked": [course("LATER")]},
                  "progress": {"total": {"earned_credits": 3, "required_credits": 120, "remaining_credits": 117}},
                  "plan": {"course_codes": [], "suggested_credits": 0, "max_credits": 20}}
        if state["mode"] in {"incomplete", "unresolved"}:
            result.update(status="needs_source_review", courses=None, progress=None, plan=None,
                          blocking_reasons=["source_incomplete" if state["mode"] == "incomplete" else "source_enrollment_unresolved"])
        return result

    def intercept(route):
        parsed = urlsplit(route.request.url)
        path = parsed.path
        requests.append((route.request.method, path))
        if parsed.hostname != "127.0.0.1":
            route.abort()
        elif path == "/auth/session":
            value = session_payload()
            digit = "1" if state["owner"] == "a" else "3"
            value["account"].update(account_id="00000000-0000-4000-8000-00000000000" + digit,
                                    session_id="00000000-0000-4000-8000-00000000000" + digit)
            route.fulfill(json=value)
        elif path == "/me/profile":
            route.fulfill(json=profile())
        elif path == "/me/course-status":
            if state["mode"] == "pending":
                pending.append((route, deepcopy(board())))
            else:
                route.fulfill(json=board())
        elif path == "/me/academic-program":
            raise AssertionError("Automatic curriculum must not request manual confirmation")
        elif common_route(route):
            return
        else:
            route.fulfill(status=404, json={"detail": "not_found"})

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1050})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/#rules")
        root = page.locator("#course-status-board")
        page.wait_for_selector('[data-course-code="ADONE"]')
        for section in ("completed", "eligible", "blocked"):
            assert root.locator(f".course-state-{section} .course-status-card").count() == 1
        assert page.locator("#academic-program-choice, #academic-program-consent, .course-program-confirmation").count() == 0
        assert "Xem bảng điểm VNU" not in root.inner_text()
        assert root.locator(".course-status-recovery").count() == 0
        page.reload()
        page.wait_for_selector('[data-course-code="ADONE"]')
        state["mode"] = "incomplete"
        root.get_by_role("button", name="Cập nhật", exact=True).click()
        page.wait_for_function("document.querySelector('#course-status-board').textContent.includes('Chưa xác minh bảng điểm')")
        assert root.locator(".course-status-card").count() == 0
        assert root.get_by_role("button", name="Cập nhật bảng điểm VNU", exact=True).is_visible()
        state["mode"] = "unresolved"
        root.get_by_role("button", name="Cập nhật", exact=True).click()
        page.wait_for_function("document.querySelector('#course-status-board').textContent.includes('Chưa xác định được chương trình')")
        assert root.locator(".course-status-card").count() == 0
        assert page.locator(".course-program-confirmation").count() == 0
        state["mode"] = "pending"
        root.get_by_role("button", name="Cập nhật", exact=True).click()
        page.wait_for_timeout(100)
        assert pending
        page.evaluate("document.dispatchEvent(new Event('workspace:session-expired'))")
        state.update(owner="b", mode="ready")
        page.evaluate("window.systemAuth.refresh()")
        page.evaluate("value => document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail:value}))", profile())
        page.wait_for_selector('[data-course-code="BDONE"]')
        for route, response in pending:
            try:
                route.fulfill(json=response)
            except Exception:
                pass  # The real AbortController may have already cancelled the old request.
        assert root.locator('[data-course-code="ADONE"]').count() == 0
        assert root.locator('[data-course-code="BDONE"]').count() == 1
        page.locator('[data-language-choice="en"]').click()
        assert root.get_by_role('heading', name='Eligibility', exact=True).count() == 1
        page.set_viewport_size({"width": 390, "height": 950})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.locator('[data-language-choice="vi"]').click()
        output = Path("backups/automatic_curriculum_20261113")
        output.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output / "automatic-mobile.png"), full_page=True)
        page.evaluate("document.dispatchEvent(new Event('workspace:session-expired'))")
        assert root.locator(".course-status-card").count() == 0
        assert not any(path == "/me/academic-program" for _, path in requests)
        assert not errors, errors
        browser.close()
    print("Automatic curriculum: direct course map, reload, no confirmation, source failures, two owners, stale responses, VI/EN and mobile passed")


if __name__ == "__main__":
    main()
