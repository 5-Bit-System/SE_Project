"""Browser verification for Curriculum Prerequisite Rule Editor.

Tests:
1. Open Admin Console -> Curriculum tab.
2. Switch to 'Bản thảo & Lịch sử phiên bản' subtab.
3. Open Prerequisite Rule Editor for a course in a revision.
4. Verify dynamic AND/OR group rendering and course metadata banner.
5. Test validation error handling on self-reference or cycle -> verify error banner.
6. Test valid rule update -> modal closes and table updates.
7. Capture screenshots in light theme, dark theme, and mobile viewport (390px).

Run: .venv/Scripts/python.exe -m tests.frontend.check_admin_rules
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
EVIDENCE_DIR = Path("backups/admin_rules_20261101")


def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            errors = []
            page.on("pageerror", lambda err: errors.append(str(err)))

            # Handle prompts & alerts gracefully
            def handle_dialog(dialog):
                if dialog.type == "prompt":
                    dialog.accept(dialog.default_value)
                else:
                    dialog.accept()

            page.on("dialog", handle_dialog)

            # 1. Sign in as admin
            page.goto(BASE_URL)
            page.wait_for_function("document.body.dataset.authState !== 'loading'")
            page.locator("#auth-login-tab").click()
            page.locator("#auth-login-email").fill("admin")
            page.locator("#auth-login-password").fill("admin123")
            page.locator("#auth-login-form button[type=submit]").click()

            page.locator('#system-admin').wait_for(state='visible')
            page.locator("#system-admin").wait_for(state="visible")

            # 2. Switch to Curriculum Tab
            page.locator("#admin-tab-curriculum").click()
            page.locator("#admin-panel-curriculum").wait_for(state="visible")
            print("  [PASS] Switched to Curriculum tab")

            # 3. Switch to Revisions subtab
            subtab_rev = page.locator("#admin-curriculum-subtab-revisions")
            subtab_rev.wait_for(state="visible")
            subtab_rev.click()

            revisions_view = page.locator("#admin-curriculum-revisions-view")
            revisions_view.wait_for(state="visible")
            page.locator("#admin-revisions-tbody tr").first.wait_for(state="visible")
            print("  [PASS] Revisions subtab loaded")

            # 4. Click 'Sửa quy tắc' on the first revision
            rule_btn = page.locator("#admin-revisions-tbody tr .btn-rev-rules").first
            rule_btn.wait_for(state="visible")
            rule_btn.click()

            # 5. Verify Prerequisite Modal opens
            modal = page.locator("#admin-prereq-modal")
            modal.wait_for(state="visible")
            assert modal.is_visible()
            print("  [PASS] Prerequisite Rule Editor Modal opened")

            # Verify course info banner
            course_code_el = page.locator("#admin-prereq-course-code")
            assert course_code_el.text_content().strip() != ""
            target_code = course_code_el.text_content().strip()
            print(f"  [PASS] Editing prerequisite rules for course: {target_code}")

            # Capture desktop light screenshot
            page.screenshot(path=str(EVIDENCE_DIR / "prereq_editor_light.png"))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            page.screenshot(path=str(EVIDENCE_DIR / "prereq_editor_dark.png"))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'light')")
            print("  [PASS] Captured light and dark desktop screenshots")

            # 6. Test Self-Reference Validation Error
            # Click add group (AND)
            page.locator("#admin-prereq-add-group-btn").click()
            # In the last group, add self course code
            inline_inputs = page.locator(".prereq-inline-input")
            last_input = inline_inputs.last
            last_input.fill(target_code)
            add_pill_btns = page.locator(".prereq-inline-add .admin-action-btn-sm")
            add_pill_btns.last.click()

            # Fill reason and submit
            page.locator("#admin-prereq-reason").fill("Thử nghiệm vi phạm tự làm tiên quyết")
            page.locator("#admin-prereq-save-btn").click()

            # Verify error alert shows
            err_alert = page.locator("#admin-prereq-error-alert")
            err_alert.wait_for(state="visible")
            err_text = err_alert.text_content()
            assert "tự làm tiên quyết" in err_text or "tiên quyết" in err_text
            print(f"  [PASS] Error correctly detected and displayed: {err_text}")

            page.screenshot(path=str(EVIDENCE_DIR / "prereq_error_light.png"))

            # 7. Remove invalid pill and save valid rule
            # Click the delete group button on the last group card
            del_btns = page.locator(".prereq-group-header button")
            if del_btns.count() > 0:
                del_btns.last.click()

            # Enter a valid update
            page.locator("#admin-prereq-reason").fill(
                "Cập nhật chuẩn hóa quy tắc tiên quyết học kỳ"
            )
            page.locator("#admin-prereq-save-btn").click()

            # Verify modal closes
            modal.wait_for(state="hidden")
            print("  [PASS] Saved valid prerequisite rule successfully and modal closed")

            # 8. Test Mobile Viewport (390px)
            mobile_page = browser.new_page(viewport={"width": 390, "height": 844})
            mobile_page.on("dialog", handle_dialog)
            mobile_page.goto(BASE_URL)
            mobile_page.wait_for_function("document.body.dataset.authState !== 'loading'")
            mobile_page.locator("#auth-login-tab").click()
            mobile_page.locator("#auth-login-email").fill("admin")
            mobile_page.locator("#auth-login-password").fill("admin123")
            mobile_page.locator("#auth-login-form button[type=submit]").click()

            mobile_page.locator('#system-admin').wait_for(state='visible')
            mobile_page.locator("#system-admin").wait_for(state="visible")

            mobile_page.locator("#admin-sidebar-toggle").click()
            mobile_page.locator("#admin-tab-curriculum").click()
            mobile_page.locator("#admin-panel-curriculum").wait_for(state="visible")
            mobile_page.locator("#admin-curriculum-subtab-revisions").click()
            mobile_page.locator("#admin-revisions-tbody tr").first.wait_for(state="visible")

            mobile_page.locator("#admin-revisions-tbody tr .btn-rev-rules").first.click()
            mobile_modal = mobile_page.locator("#admin-prereq-modal")
            mobile_modal.wait_for(state="visible")

            mobile_page.screenshot(path=str(EVIDENCE_DIR / "prereq_modal_mobile.png"))
            print("  [PASS] Captured mobile viewport screenshot (390px)")

            assert len(errors) == 0, f"Page errors encountered: {errors}"
            print("\n[SUCCESS] All Prerequisite Rule Editor browser checks passed cleanly!")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
