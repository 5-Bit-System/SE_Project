"""Multiple invented accounts through the same confirmation/board UI; no VNU I/O."""

import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

KHMT = "khmtt_7480113qtd_2022"
KHDL = "khdl_7460108_2022"


def course(code):
    return {"code": code, "name": "Invented " + code, "name_en": None, "credits": 3,
            "requirement_type": "required", "counted_in_total": True,
            "groups": [], "reasons": [], "suggested": False}


def main():
    owner = "a"
    confirmed = {"a": False, "b": False}
    complete = {"a": True, "b": False}
    waiting, errors, writes = [], [], []
    delayed = False
    programs = [{"program_id": KHMT, "name": "Khoa học máy tính và thông tin", "catalog_revision": "a" * 64},
                {"program_id": KHDL, "name": "Khoa học dữ liệu", "catalog_revision": "b" * 64}]

    def source():
        return {"profile": {"program": programs[0 if owner == "a" else 1]["name"],
                            "cohort": "68" if owner == "a" else "67"},
                "snapshot": {"completeness": "complete" if complete[owner] else "unknown"}}

    def saved_profile():
        value = source()
        value["subject"] = "synthetic-only"
        value["snapshot"].update(attempts=[], source_summary=[], unknown_rows=[])
        return value

    def setup():
        return {"programs": programs, "cohorts": [67, 68, 69],
                "suggested_program_id": KHMT if owner == "a" else KHDL,
                "suggested_cohort": 68 if owner == "a" else 67,
                "source_program": source()["profile"]["program"],
                "source_cohort": source()["profile"]["cohort"],
                "snapshot_digest": "invented-" + owner, "source_scope": owner * 64,
                "policy_source": "/academic-policy/vnu-3626-2022"}

    def ready_board():
        code = "TESTA" if owner == "a" else "TESTB"
        return {"status": "ready", "blocking_reasons": [],
                "courses": {"completed": [course(code)], "eligible": [course(code + "NEXT")],
                            "blocked": [{**course(code + "LATER"), "reasons": [{
                                "kind": "missing_prerequisites", "missing_prerequisites": [[code + "NEXT"]]}]}]},
                "progress": {"total": {"earned_credits": 3, "required_credits": 120, "remaining_credits": 117}},
                "plan": {"course_codes": [], "suggested_credits": 0, "max_credits": 20},
                "selections": {}}

    def intercept(route):
        parsed = urlparse(route.request.url)
        path = parsed.path
        if path == "/me/course-status":
            if not confirmed[owner]:
                result = {"status": "needs_program_binding", "courses": None,
                          "blocking_reasons": ["program_binding_unverified"], "program_selection": setup()}
            elif not complete[owner]:
                result = {"status": "needs_source_review", "courses": None,
                          "blocking_reasons": ["source_incomplete"],
                          "collection_status": {"completeness": "unknown"}}
            else:
                result = ready_board()
            route.fulfill(content_type="application/json", body=json.dumps(result))
        elif path == "/me/profile":
            route.fulfill(content_type="application/json", body=json.dumps(saved_profile()))
        elif path == "/me/academic-program":
            body = route.request.post_data_json
            assert body["program_id"] == setup()["suggested_program_id"]
            assert body["cohort"] == setup()["suggested_cohort"]
            assert body["expected_source_scope"] == owner * 64
            assert body["confirm"] is True
            assert not set(body) & {"owner", "records", "passed_course_codes", "verified"}
            writes.append(owner)
            if delayed:
                waiting.append(route)
                return
            confirmed[owner] = True
            route.fulfill(content_type="application/json", body='{"confirmed":true}')
        elif path.startswith(("/me/", "/auth/")):
            route.fulfill(status=401, content_type="application/json", body='{"detail":"session_expired"}')
        elif path == "/static/course-status.js" and not parsed.query:
            # Model a browser still holding the pre-confirmation script at the old URL.
            route.fulfill(content_type="application/javascript", body="window.obsoleteBoardLoaded = true;")
        elif parsed.hostname == "127.0.0.1" and (path == "/" or path.startswith("/static/")):
            route.continue_()
        else:
            route.abort()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1050})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/?course-mode=personal#rules")
        assert page.locator("#course-status-board").is_visible()
        assert page.evaluate("window.obsoleteBoardLoaded") is None
        root = page.locator("#course-status-board")

        def emit():
            page.evaluate("value => document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail:value}))", source())

        # Restore the existing session from HTTP on page load, then open personal mode.
        page.wait_for_selector("#academic-program-choice")
        assert page.locator("#academic-program-choice").input_value() == KHMT
        assert page.locator("#academic-cohort-choice").input_value() == "68"
        assert not writes
        evidence = Path("backups/personal_academic_20261025/ui")
        evidence.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(evidence / "confirmation-desktop.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 1050})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.screenshot(path=str(evidence / "confirmation-mobile.png"), full_page=True)
        page.set_viewport_size({"width": 1440, "height": 1050})
        page.locator("#academic-program-consent").check()
        root.get_by_role("button", name="Xác nhận và đối chiếu bảng điểm", exact=True).click()
        page.wait_for_selector('[data-course-code="TESTA"]')
        assert root.locator(".course-state-completed .course-status-card").count() == 1
        assert root.locator(".course-state-eligible .course-status-card").count() == 1
        assert root.locator(".course-state-blocked .course-status-card").count() == 1
        assert page.locator("#course-credit-budget").input_value() == "20"
        # Switching account clears the first account before the second response.
        page.evaluate("document.dispatchEvent(new Event('workspace:session-expired'))")
        assert root.locator('[data-course-code="TESTA"]').count() == 0
        owner = "b"
        emit()
        page.wait_for_selector("#academic-program-choice")
        assert page.locator("#academic-program-choice").input_value() == KHDL
        assert page.locator("#academic-cohort-choice").input_value() == "67"
        page.locator("#academic-program-consent").check()
        root.get_by_role("button", name="Xác nhận và đối chiếu bảng điểm", exact=True).click()
        page.wait_for_function("document.querySelector('#course-status-board').textContent.includes('bộ đọc mới')")
        assert root.locator(".course-status-card").count() == 0
        complete["b"] = True
        emit()
        page.wait_for_selector('[data-course-code="TESTB"]')
        assert root.locator('[data-course-code="TESTA"]').count() == 0
        assert writes == ["a", "b"]
        page.locator('[data-language-choice="en"]').click()
        assert 'Your course map' in root.inner_text()
        page.locator('[data-language-choice="vi"]').click()
        evidence = Path("backups/personal_academic_20261025/ui")
        evidence.mkdir(parents=True, exist_ok=True)
        for theme in ("light", "dark"):
            page.locator(f'[data-theme-choice="{theme}"]').click()
            for width in (1440, 390):
                page.set_viewport_size({"width": width, "height": 1050})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                page.screenshot(path=str(evidence / f"personal-{theme}-{width}.png"), full_page=True)
        # A confirmation response arriving after logout must not restore the old profile.
        # The old incomplete snapshot exposes an action that opens the actual update form.
        complete["b"] = False
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        root.get_by_role("button", name="Cập nhật", exact=True).click()
        root.get_by_role("button", name="Cập nhật bảng điểm VNU", exact=True).click()
        assert page.locator("#portal-login").is_visible()
        assert page.locator("#portal-username").input_value() == "synthetic-only"
        assert page.locator("#portal-password").evaluate("node => node === document.activeElement")
        page.locator("#tab-btn-rules").click()
        complete["b"] = True
        confirmed["b"] = False
        emit()
        page.wait_for_selector("#academic-program-choice")
        delayed = True
        page.locator("#academic-program-consent").check()
        root.get_by_role("button", name="Xác nhận và đối chiếu bảng điểm", exact=True).click()
        page.wait_for_timeout(100)
        assert waiting
        page.evaluate("document.dispatchEvent(new Event('workspace:session-expired'))")
        for route in waiting:
            route.fulfill(content_type="application/json", body='{"confirmed":true}')
        page.wait_for_timeout(100)
        assert root.locator(".course-status-card, #academic-program-choice").count() == 0
        assert 'Đăng nhập VNU' in root.inner_text()
        assert not errors, errors
        browser.close()
    print("Personal curriculum: two owners, distinct programs/cohorts, source verification, three states, VI/EN/mobile and stale confirmation passed")


if __name__ == "__main__":
    main()
