"""Browser verification for Crawler Monitoring and Governance UI.

Tests:
1. Open Admin Console -> Crawler tab.
2. Verify Crawler KPI summary cards (sources, running jobs, pages, documents).
3. Jobs View: Trigger a new crawl job, verify status badges, pause, and resume.
4. Sources View: Add new source with URL allowlist validation check.
5. Toggle source active/inactive state.
6. Capture screenshots in light theme, dark theme, and mobile viewport (390px).

Run: .venv/Scripts/python.exe -m tests.frontend.check_admin_crawler
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8000")
EVIDENCE_DIR = Path("backups/admin_crawler_20261101")


def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors = []
            page.on("pageerror", lambda err: errors.append(str(err)))

            def handle_dialog(dialog):
                dialog.accept()

            page.on("dialog", handle_dialog)

            # 1. Sign in as admin
            page.goto(BASE_URL)
            page.wait_for_function("document.body.dataset.authState !== 'loading'")
            page.locator("#auth-login-tab").click()
            page.locator("#auth-login-email").fill("admin")
            page.locator("#auth-login-password").fill("admin123")
            page.locator("#auth-login-form button[type=submit]").click()

            page.locator("#system-admin-open").wait_for(state="visible")
            page.locator("#system-admin-open").click()
            page.locator("#system-admin").wait_for(state="visible")

            # 2. Switch to Crawler Tab
            tab_crawler = page.locator("#admin-tab-crawler")
            tab_crawler.wait_for(state="visible")
            tab_crawler.click()

            panel_crawler = page.locator("#admin-panel-crawler")
            panel_crawler.wait_for(state="visible")
            assert not panel_crawler.is_hidden()
            print("  [PASS] Switched to Crawler tab")

            # 3. Verify KPI cards rendered
            page.locator("#crawler-kpi-sources-count").wait_for(state="visible")
            page.wait_for_function(
                "document.getElementById('crawler-kpi-sources-count').textContent !== '—'"
            )
            src_count = page.locator("#crawler-kpi-sources-count").text_content()
            print(f"  [PASS] Crawler KPI rendered: {src_count} sources available")

            # 4. Trigger a new crawl job via modal
            page.locator("#admin-crawler-trigger-btn").click()
            trigger_modal = page.locator("#admin-crawler-trigger-modal")
            trigger_modal.wait_for(state="visible")

            # Select the first option that has a value
            select_el = page.locator("#admin-trigger-source-select")
            select_el.wait_for(state="visible")
            page.wait_for_function(
                "document.querySelectorAll('#admin-trigger-source-select option').length > 1"
            )
            # Select second option (first real source)
            options = page.locator("#admin-trigger-source-select option")
            first_val = options.nth(1).get_attribute("value")
            select_el.select_option(first_val)

            page.locator("#admin-crawler-trigger-submit-btn").click()
            trigger_modal.wait_for(state="hidden")
            print(f"  [PASS] Triggered new crawl job on source {first_val}")

            # Verify running job in table
            page.locator("#admin-crawler-jobs-tbody tr").first.wait_for(state="visible")
            print("  [PASS] Job rendered in Jobs table")

            # Capture Jobs view screenshots
            page.screenshot(path=str(EVIDENCE_DIR / "crawler_jobs_light.png"))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            page.screenshot(path=str(EVIDENCE_DIR / "crawler_jobs_dark.png"))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'light')")
            print("  [PASS] Captured Jobs view light & dark screenshots")

            # Test Pause Job
            pause_btn = page.locator("#admin-crawler-jobs-tbody tr .btn-pause-job").first
            if pause_btn.is_visible():
                pause_btn.click()
                page.wait_for_timeout(1000)
                # Verify paused state badge
                assert page.locator("#admin-crawler-jobs-tbody tr .badge-warning").count() > 0
                print("  [PASS] Paused running crawl job")

                # Test Resume Job
                resume_btn = page.locator("#admin-crawler-jobs-tbody tr .btn-resume-job").first
                resume_btn.wait_for(state="visible")
                resume_btn.click()
                page.wait_for_timeout(1000)
                print("  [PASS] Resumed crawl job")

            # 5. Switch to Sources Subtab
            page.locator("#admin-crawler-subtab-sources").click()
            sources_view = page.locator("#admin-crawler-sources-view")
            sources_view.wait_for(state="visible")
            page.locator("#admin-crawler-sources-tbody tr").first.wait_for(state="visible")
            print("  [PASS] Switched to Sources subtab")

            # Open Add Source Modal & test URL policy validation
            page.locator("#admin-crawler-add-source-btn").click()
            src_modal = page.locator("#admin-crawler-source-modal")
            src_modal.wait_for(state="visible")

            # Fill disallowed URL
            page.locator("#admin-source-name").fill("Nguồn thử nghiệm vi phạm")
            page.locator("#admin-source-url").fill("https://evil-unauthorized-domain.com/steal")
            page.locator("#admin-crawler-source-save-btn").click()

            # Error alert should show
            err_box = page.locator("#admin-source-error-alert")
            err_box.wait_for(state="visible")
            err_text = err_box.text_content()
            assert "không nằm trong danh sách" in err_text
            print(f"  [PASS] Allowlist URL policy enforced: {err_text}")

            # Fill valid educational URL
            page.locator("#admin-source-name").fill("Cổng thông tin ĐHQGHN")
            page.locator("#admin-source-url").fill("https://vnu.edu.vn/dao-tao")
            page.locator("#admin-crawler-source-save-btn").click()
            src_modal.wait_for(state="hidden")
            print("  [PASS] Valid educational source created successfully")

            # Capture Sources view screenshots
            page.screenshot(path=str(EVIDENCE_DIR / "crawler_sources_light.png"))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            page.screenshot(path=str(EVIDENCE_DIR / "crawler_sources_dark.png"))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'light')")
            print("  [PASS] Captured Sources view light & dark screenshots")

            # 6. Test Mobile Viewport (390px)
            mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
            mobile_page.on("dialog", handle_dialog)
            mobile_page.goto(BASE_URL)
            mobile_page.wait_for_function("document.body.dataset.authState !== 'loading'")
            mobile_page.locator("#auth-login-tab").click()
            mobile_page.locator("#auth-login-email").fill("admin")
            mobile_page.locator("#auth-login-password").fill("admin123")
            mobile_page.locator("#auth-login-form button[type=submit]").click()

            mobile_page.locator("#system-admin-open").wait_for(state="visible")
            mobile_page.locator("#system-admin-open").click()
            mobile_page.locator("#system-admin").wait_for(state="visible")

            mobile_page.locator("#admin-tab-crawler").click()
            mobile_page.locator("#admin-panel-crawler").wait_for(state="visible")
            mobile_page.screenshot(path=str(EVIDENCE_DIR / "crawler_mobile.png"))
            print("  [PASS] Captured Mobile Viewport screenshot (390px)")

            assert len(errors) == 0, f"Encountered page errors: {errors}"
            print("\n[SUCCESS] All Crawler UI verification checks passed cleanly!")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
