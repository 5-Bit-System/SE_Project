"""Late admin responses must not overwrite filters or survive logout."""
import copy
import json
import os

from playwright.sync_api import expect, sync_playwright

BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:8000')


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        try:
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            page.goto(BASE_URL)
            page.locator('#auth-login-tab').click()
            page.locator('#auth-login-email').fill('admin')
            page.locator('#auth-login-password').fill('admin123')
            page.locator('#auth-login-form button[type=submit]').click()
            expect(page.locator('#system-admin-open')).to_be_visible()
            page.locator('#system-admin-open').click()
            template = page.request.get(BASE_URL + '/admin/crawler/documents?limit=1').json()['documents'][0]
            pending = []
            page.route('**/admin/crawler/documents?*', lambda route: pending.append(route))
            page.locator('#admin-tab-crawler').click()
            page.wait_for_timeout(150)
            assert len(pending) == 1
            page.locator('#admin-docs-search').fill('latest')
            page.wait_for_timeout(150)
            assert len(pending) == 2
            def payload(title):
                doc = copy.deepcopy(template)
                doc['title'] = title
                return json.dumps({'documents': [doc], 'total': 1, 'limit': 20, 'offset': 0})
            pending[1].fulfill(status=200, content_type='application/json', body=payload('LATEST_RESULT'))
            expect(page.locator('#admin-crawler-docs-tbody')).to_contain_text('LATEST_RESULT')
            pending[0].fulfill(status=200, content_type='application/json', body=payload('STALE_RESULT'))
            page.wait_for_timeout(200)
            expect(page.locator('#admin-crawler-docs-tbody')).not_to_contain_text('STALE_RESULT')
            held = []
            page.route('**/admin/overview', lambda route: held.append(route))
            page.locator('#admin-tab-overview').click()
            page.locator('#admin-overview-refresh').click()
            page.wait_for_timeout(150)
            assert held
            page.locator('#system-logout').click()
            expect(page.locator('#system-admin')).to_be_hidden()
            held[0].fulfill(status=200, content_type='application/json', body=json.dumps({
                key: {'value': 999999, 'status': 'available', 'source': 'PRIVATE_LATE_RESULT'}
                for key in ['accounts_total','programs_count','courses_count','catalog_status','system_readiness']}))
            page.wait_for_timeout(200)
            expect(page.locator('#admin-overview-grid')).to_be_empty()
            assert 'PRIVATE_LATE_RESULT' not in page.locator('#system-admin').inner_text()
            print('Admin races: newest filter wins; logout clears private UI and drops late responses')
        finally:
            browser.close()


if __name__ == '__main__':
    main()
