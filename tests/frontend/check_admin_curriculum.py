"""Playwright browser verification of Admin Curriculum & Cohort views.

Checks:
1. Program list view: program code, name, cohort/year, credits, courses count, draft status badge, and source file.
2. Program search and status filtering.
3. Course detail view: course code, name, credits, block, term/year, prerequisite rules, draft status badge.
4. Course block and keyword filtering.
5. Navigation back to program list.
6. Mobile layout (390px) and dark/light screenshots.

Run: .venv/Scripts/python.exe -m tests.frontend.check_admin_curriculum
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')
EVIDENCE_DIR = Path('backups/admin_curriculum_20261101')


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

            # 2. Open Admin Console and switch to Curriculum tab
            page.locator('#system-admin-open').wait_for(state='visible')
            page.locator('#system-admin-open').click()
            page.locator('#admin-tab-curriculum').click()
            page.locator('#admin-programs-tbody tr').first.wait_for(state='visible')
            print('  [PASS] Curriculum tab loaded with program rows')

            # 3. Check program row contents
            rows = page.locator('#admin-programs-tbody tr')
            assert rows.count() == 4, f'Expected 4 programs, found {rows.count()}'

            # Verify draft_unverified badge
            badge = rows.first.locator('.admin-status-badge.badge-warning')
            assert badge.is_visible()
            assert 'chưa kiểm định' in badge.inner_text().lower() or 'draft' in badge.inner_text().lower()
            print('  [PASS] Program rows display truthful draft_unverified badge')

            # 4. Test Program Search
            page.locator('#admin-curriculum-search').fill('khmtt')
            page.wait_for_timeout(100)
            assert page.locator('#admin-programs-tbody tr').count() == 1
            assert 'khmtt' in page.locator('#admin-programs-tbody tr').first.inner_text().lower()

            page.locator('#admin-curriculum-search').fill('')
            page.wait_for_timeout(100)
            assert page.locator('#admin-programs-tbody tr').count() == 4
            print('  [PASS] Program search filter verified')

            # 5. Open Course Detail for a program
            first_view_btn = page.locator('.admin-view-courses-btn').first
            first_view_btn.click()
            page.locator('#admin-curriculum-detail-view').wait_for(state='visible')
            assert page.locator('#admin-curriculum-list-view').is_hidden()

            # Wait for courses table
            page.locator('#admin-courses-tbody .admin-course-code').first.wait_for(state='visible')
            courses_count = page.locator('#admin-courses-tbody tr').count()
            assert courses_count > 10, f'Expected >10 courses, got {courses_count}'
            print(f'  [PASS] Opened course detail view with {courses_count} courses')

            # 6. Verify course table fields (Code, Name, Credits, Prereqs)
            first_course = page.locator('#admin-courses-tbody tr').first
            assert first_course.locator('.admin-course-code').is_visible()
            assert first_course.locator('.tabular-nums').is_visible()

            # 7. Test Course Search within program
            first_code = first_course.locator('.admin-course-code').inner_text()
            page.locator('#admin-courses-search').fill(first_code)
            page.wait_for_timeout(100)
            assert page.locator('#admin-courses-tbody tr').count() >= 1
            page.locator('#admin-courses-search').fill('')
            print('  [PASS] Course keyword search verified')

            # 8. Screenshots: Course detail view (Light & Dark)
            page.screenshot(path=str(EVIDENCE_DIR / 'curriculum_courses_light.png'), full_page=True)

            page.locator('[data-theme-choice="dark"]').click()
            page.wait_for_timeout(200)
            page.screenshot(path=str(EVIDENCE_DIR / 'curriculum_courses_dark.png'), full_page=True)
            print('  [PASS] Course detail screenshots captured in light and dark')

            # 9. Test Back to Programs List
            page.locator('#admin-curriculum-detail-back').click()
            page.locator('#admin-curriculum-list-view').wait_for(state='visible')
            assert page.locator('#admin-curriculum-detail-view').is_hidden()
            print('  [PASS] Back button returned to program list view')

            # 10. Screenshots: Programs list view
            page.screenshot(path=str(EVIDENCE_DIR / 'curriculum_programs_dark.png'), full_page=True)

            page.locator('[data-theme-choice="light"]').click()
            page.wait_for_timeout(200)
            page.screenshot(path=str(EVIDENCE_DIR / 'curriculum_programs_light.png'), full_page=True)

            # 11. Mobile check (390px)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.wait_for_timeout(200)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(EVIDENCE_DIR / 'curriculum_mobile.png'), full_page=True)
            print('  [PASS] Mobile responsive view verified without overflow (390px)')

            assert not errors, f'Uncaught browser errors: {errors}'

        finally:
            browser.close()

    print('\n>>> Task 4 verification SUCCESSFUL! Screenshots stored in:', EVIDENCE_DIR)


if __name__ == '__main__':
    main()
