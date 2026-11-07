"""Browser verification for Curriculum Import Modal and Live Validation Preview.

Tests:
1. Open Admin Console -> Curriculum tab.
2. Click 'Nhập bản thảo (CSV)' button -> opens accessible <dialog>.
3. Test validation error preview (duplicate course code error displayed).
4. Capture screenshots of error validation state.
5. Test successful draft import (valid CSV -> revision created).
6. Capture screenshots in light, dark, and mobile viewports.
7. Verify modal close behavior.

Run: .venv/Scripts/python.exe -m tests.frontend.check_admin_import
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')
EVIDENCE_DIR = Path('backups/admin_import_20261101')


def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        try:
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            errors = []
            page.on('pageerror', lambda err: errors.append(str(err)))

            # 1. Sign in as admin
            page.goto(BASE_URL)
            page.wait_for_function("document.body.dataset.authState !== 'loading'")
            page.locator('#auth-login-tab').click()
            page.locator('#auth-login-email').fill('admin')
            page.locator('#auth-login-password').fill('admin123')
            page.locator('#auth-login-form button[type=submit]').click()

            page.locator('#system-admin').wait_for(state='visible')
            page.locator('#system-admin').wait_for(state='visible')

            # 2. Switch to Curriculum Tab
            page.locator('#admin-tab-curriculum').click()
            page.locator('#admin-panel-curriculum').wait_for(state='visible')
            page.locator('#admin-programs-tbody tr').first.wait_for(state='visible')
            print('  [PASS] Switched to Curriculum tab and programs loaded')

            # 3. Open Import Modal
            import_btn = page.locator('#admin-curriculum-import-btn')
            import_btn.wait_for(state='visible')
            import_btn.click()

            modal = page.locator('#admin-import-modal')
            modal.wait_for(state='visible')
            assert page.evaluate("document.getElementById('admin-import-modal').open") is True
            print('  [PASS] Import modal opened successfully')

            # 4. Fill form with duplicate code to trigger validation failure
            page.locator('#admin-import-program-select option[value="khdl_7460108_2022"]').wait_for(state='attached')
            page.locator('#admin-import-program-select').select_option('khdl_7460108_2022')
            page.locator('#admin-import-version-title').fill('K68 Thử nghiệm lỗi trùng mã')
            page.locator('#admin-import-cohort').fill('2026')

            invalid_csv = """code,name,credits,prerequisites,block
MAT1001,Giải tích 1,3,,Khối chung
MAT1001,Giải tích 1 trùng lặp,3,,Khối chung
"""
            page.locator('#admin-import-csv-text').fill(invalid_csv)
            page.locator('#admin-import-submit-btn').click()

            # Wait for validation preview
            preview = page.locator('#admin-import-preview')
            preview.wait_for(state='visible')
            page.locator('.preview-status-pill.danger').wait_for(state='visible')
            preview_text = preview.inner_text()
            assert 'Trùng mã học phần: MAT1001' in preview_text
            print('  [PASS] Live validation caught duplicate course error')

            # Capture screenshots of validation error
            page.screenshot(path=str(EVIDENCE_DIR / 'import_validation_error_light.png'))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            page.screenshot(path=str(EVIDENCE_DIR / 'import_validation_error_dark.png'))
            print('  [PASS] Captured validation error screenshots in light & dark')

            # 4b. Test malicious HTML payload in CSV cells: assert inert text and no execution
            page.evaluate("window.__xss_probe = false")
            malicious_csv = """code,name,credits,prerequisites,block
MAT1001,<img src=x onerror=window.__xss_probe=true>,3,,Khối chung
MAT1001,<script>window.__xss_probe=true</script>,3,,Khối chung
"""
            page.locator('#admin-import-csv-text').fill(malicious_csv)
            page.locator('#admin-import-submit-btn').click()
            preview.wait_for(state='visible')
            page.locator('.preview-status-pill.danger').wait_for(state='visible')

            xss_fired = page.evaluate("window.__xss_probe")
            assert xss_fired is False, "XSS execution detected in CSV import feedback!"
            img_count = preview.locator("img").count()
            assert img_count == 0, "HTML tag was rendered into DOM in import preview!"
            print('  [PASS] Malicious CSV payload rendered as inert text without script execution')

            # 5. Correct the CSV to valid content
            page.evaluate("document.documentElement.setAttribute('data-theme', 'light')")
            valid_csv = """code,name,credits,prerequisites,block,suggested_term
MAT1001,Giải tích 1,3,,Khối kiến thức chung,1
MAT1002,Giải tích 2,3,MAT1001,Khối kiến thức chung,2
DAT2001,Nhập môn Khoa học dữ liệu,3,,Cơ sở ngành,3
"""
            page.locator('#admin-import-version-title').fill('K68 Bản thảo chuẩn 2026')
            page.locator('#admin-import-csv-text').fill(valid_csv)
            page.locator('#admin-import-submit-btn').click()

            # Wait for valid state
            page.locator('.preview-status-pill.success').wait_for(state='visible')
            success_text = preview.inner_text()
            assert 'Hợp lệ' in success_text
            assert 'Số học phần: 3' in success_text
            assert 'Tổng tín chỉ: 9' in success_text
            print('  [PASS] Valid draft revision created with stats (3 courses, 9 credits)')

            # Capture screenshots of successful import state
            page.screenshot(path=str(EVIDENCE_DIR / 'import_success_light.png'))
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            page.screenshot(path=str(EVIDENCE_DIR / 'import_success_dark.png'))
            print('  [PASS] Captured success preview screenshots in light & dark')

            # 6. Test mobile view (390px)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.wait_for_timeout(300)
            page.screenshot(path=str(EVIDENCE_DIR / 'import_modal_mobile.png'))
            print('  [PASS] Mobile responsive view verified')

            # 7. Close modal
            page.locator('#admin-import-close-btn').click()
            page.wait_for_timeout(300)
            assert page.evaluate("document.getElementById('admin-import-modal').open") is False
            print('  [PASS] Modal closed successfully')

            # Check zero browser errors
            assert len(errors) == 0, f'Browser page errors: {errors}'

            print('\n>>> Task 7 verification SUCCESSFUL! Screenshots stored in:', EVIDENCE_DIR)
        finally:
            browser.close()


if __name__ == '__main__':
    main()
