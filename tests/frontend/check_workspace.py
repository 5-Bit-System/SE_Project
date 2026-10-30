"""Dashboard/profile navigation and isolation regression with synthetic personal data."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.presentation_fixture import common_route


def main():
    evidence = Path("backups/workspace_redesign_20261023")
    evidence.mkdir(parents=True, exist_ok=True)
    sample = {"subject": "synthetic-only", "fetched_at": "2026-10-23T00:00:00+00:00",
              "snapshot": {"source_summary": [["Tổng tín chỉ: 6"]], "unknown_rows": [],
                           "attempts": [
                               {"term": "HỌC KỲ 1 - 2099-2100", "code": "TEST001",
                                "name": "Môn giả lập", "credits": "3", "grade10": "8,5",
                                "letter": "B+", "grade4": "3,5"},
                               {"term": "HỌC KỲ 2 - 2100-2101", "code": "TEST002",
                                "name": "<script>synthetic</script>", "credits": "3",
                                "grade10": "", "letter": "", "grade4": ""}]}}
    requests = []

    def intercept(route):
        url = route.request.url
        if '/auth/session' in url:
            route.fulfill(json=session_payload())
        elif url == 'http://127.0.0.1:8000/me/semester-plans':
            route.fulfill(json={'plans': []})
        elif '/me/course-status?' in url:
            route.fulfill(json={
                'status': 'needs_program_binding', 'can_plan': False,
                'blocking_reasons': ['source_incomplete', 'program_binding_unverified'],
                'courses': None, 'progress': None, 'plan': None})
        elif "/me/" in url or "/auth/" in url:
            requests.append(url)
            route.fulfill(content_type="application/json", body=json.dumps(sample))
        elif not url.startswith("http://127.0.0.1:8000/"):
            route.abort()
        else:
            assert common_route(route), url

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/")
        assert page.locator("#tab-dashboard").is_visible()
        assert page.locator(".tab-panel.active").count() == 1
        page.wait_for_function("document.querySelectorAll('#analytics-trend .chart-point').length>0")
        assert page.locator('#tab-transcript, #dashboard-manual-plan').count() == 0
        assert page.locator(".workspace-body > .tab-panel").count() == 4
        assert page.evaluate("new Set([...document.querySelectorAll('[id]')].map(e=>e.id)).size === document.querySelectorAll('[id]').length")
        page.locator("#tab-btn-profile").click()
        page.wait_for_function("!document.getElementById('portal-profile').hidden")
        assert page.locator("dialog").count() == 0
        assert page.locator("#portal-dialog").is_visible()
        assert page.evaluate("location.hash") == "#profile"
        assert page.locator("#portal-table tbody tr:not(.portal-term)").count() == 2
        page.locator("#portal-search").fill("TEST001")
        assert page.locator("#portal-table tbody tr:not(.portal-term)").count() == 1
        page.locator("#portal-search").fill("")
        page.locator("#portal-term").select_option(label="HỌC KỲ 2 - 2100-2101")
        assert "TEST002" in page.locator("#portal-table").inner_text()
        assert "TEST001" not in page.locator("#portal-table").inner_text()
        page.locator("#portal-term").select_option("")
        assert page.locator("#portal-table script").count() == 0
        for theme in ("light", "dark"):
            page.locator(f'[data-theme-choice="{theme}"]').click()
            page.screenshot(path=str(evidence / f"profile-{theme}.png"), full_page=True)
        page.locator('[data-language-choice="en"]').click()
        assert page.locator("#portal-heading").inner_text() == "Academic profile"
        assert "Môn giả lập" in page.locator("#portal-table").inner_text()
        page.locator("#tab-btn-dashboard").click()
        assert "Study dashboard" in page.locator("#dashboard-content").inner_text()
        page.set_viewport_size({"width": 390, "height": 900})
        for panel in ("tab-btn-dashboard", "tab-btn-profile", "tab-btn-rules", "tab-btn-recommend"):
            page.locator(f"#{panel}").click()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), panel
            if panel in {"tab-btn-dashboard", "tab-btn-profile"}:
                page.screenshot(path=str(evidence / f"{panel}-mobile.png"), full_page=True)
        assert page.locator("#program-select").count() == 0
        page.locator("#tab-btn-dashboard").click()
        assert page.locator('#tab-transcript, #dashboard-manual-plan').count() == 0
        page.locator("#tab-btn-profile").click()
        assert page.locator("#portal-identity").inner_text() == "synthetic-only"
        assert not errors, errors
        browser.close()
    print("Workspace: VNU dashboard/profile isolation, navigation, filters, VI/EN, themes/mobile passed")


if __name__ == "__main__":
    main()
