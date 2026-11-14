"""TC20 browser contract: lost ACK, same key, milestone progress and one completion."""

import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.presentation_fixture import common_route


def main():
    keys, errors = [], []
    state = {"phase": "collecting", "percent": 25, "done": False, "authenticated": True}
    source = {"subject": "vt102-browser-synthetic", "profile": {"program": "Synthetic", "cohort": "68"},
              "snapshot": {"completeness": "complete", "attempts": [], "unknown_rows": [], "source_summary": []}}

    def intercept(route):
        path = urlsplit(route.request.url).path
        if path == "/auth/session":
            route.fulfill(json=session_payload(state["authenticated"]))
        elif path == "/me/profile":
            route.fulfill(json={**source, "latest_collection": {"save_status": "saved", "completeness": "complete"}})
        elif path == "/me/portal-sync":
            keys.append(route.request.headers.get("idempotency-key"))
            if len(keys) == 1:
                route.abort("failed")
            else:
                route.fulfill(status=202, json={"id": "vt102-browser-job", "state": "running",
                    "phase": "queued", "progress_percent": 0, "error": None, "result": None})
        elif path == "/me/portal-sync/vt102-browser-job":
            route.fulfill(json={"id": "vt102-browser-job", "state": "done" if state["done"] else "running",
                "phase": "finished" if state["done"] else state["phase"],
                "progress_percent": 100 if state["done"] else state["percent"],
                "result": "saved" if state["done"] else None, "error": None})
        elif path == "/auth/logout":
            state["authenticated"] = False
            route.fulfill(json={"logged_out": True})
        elif path.startswith("/me/") and not path.startswith("/me/semester-plans"):
            route.fulfill(json={"status": "needs_source_review", "courses": None, "blocking_reasons": []})
        elif not common_route(route):
            route.abort()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/#profile")
        expect(page.locator("#portal-sync")).to_be_visible()
        page.locator("#portal-sync").click()
        expect(page.locator("#portal-sync")).to_be_enabled()
        page.locator("#portal-sync").click()
        assert keys[0] and keys[0] == keys[1], "Lost-ACK retry must reuse the original key"
        expect(page.locator("#portal-task-progress")).to_be_visible()
        expect(page.locator("#portal-progress")).to_have_attribute("value", "25")
        expect(page.locator("#portal-progress-label")).to_contain_text("25%")
        page.evaluate("""() => {
          window.vt102Feedback = 0;
          const original = window.workspaceMotion.statusFeedback;
          window.workspaceMotion.statusFeedback = (node, status) => {
            if (status === 'success') window.vt102Feedback++;
            return original(node, status);
          };
        }""")
        state["done"] = True
        expect(page.locator("#portal-progress")).to_have_attribute("value", "100")
        expect(page.locator("#portal-progress-label")).to_contain_text("100%")
        assert page.evaluate("window.vt102Feedback") == 1
        page.locator("[data-language-choice=en]").click()
        expect(page.locator("#portal-progress-label")).to_contain_text("Completed")
        page.set_viewport_size({"width": 390, "height": 900})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.locator("#system-logout").click()
        expect(page.locator("#portal-task-progress")).not_to_be_visible()
        assert not errors, errors
        browser.close()
    root = Path("docs/vt102/evidence/browser")
    root.mkdir(parents=True, exist_ok=True)
    (root / "verification.json").write_text(json.dumps({"passed": True, "lost_ack_same_key": True,
        "milestones": [25, 100], "completion_feedback": 1, "real_personal_data": False}), encoding="utf-8")
    print("TC20 browser: lost ACK/same key, progress, one completion, EN/mobile/logout passed")


if __name__ == "__main__":
    main()
