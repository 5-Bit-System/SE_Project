"""Real board script, synthetic responses and virtual time; no DB/VNU/provider."""

from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def main():
    script = Path('app/static/course-status.js').read_text()
    errors, pending = [], []
    mode = 'pending'

    def intercept(route):
        path = urlsplit(route.request.url).path
        if path == '/test':
            route.fulfill(content_type='text/html', body='''<!doctype html><html><body>
                <div id="course-status-board"></div><div id="course-planning-panel"></div>
                <script>window.workspaceI18n={language:'vi'};
                window.systemAuth={account:{account_id:'synthetic',session_id:'synthetic-session'}};
                document.documentElement.dataset.view='tab-recommend';
                window.updates=[];document.addEventListener('workspace:planning-state',e=>updates.push(e.detail));
                </script></body></html>''')
        elif path == '/me/semester-plans':
            route.fulfill(json={'plans': []})
        elif path == '/me/course-status':
            if mode == 'pending':
                pending.append(route)
            elif mode == '401':
                route.fulfill(status=401, json={})
            elif mode == 'selection-pending':
                route.fulfill(json={'status': 'partial', 'blocking_reasons': ['program_binding_unverified']})
            else:
                route.fulfill(json={'status': 'partial', 'blocking_reasons': []})
        elif path == '/me/academic-program':
            pending.append(route)
        else:
            route.abort()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/*', intercept)
        page.goto('http://127.0.0.1:8000/test')
        page.clock.install()
        page.add_script_tag(content=script)
        page.evaluate("document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail:{profile:{},snapshot:{}}}))")
        page.wait_for_function('window.workspacePlanning.snapshot().loading')
        page.wait_for_function('updates.some(x=>x.loading)')
        page.wait_for_timeout(50)
        assert pending
        page.clock.fast_forward(20001)
        page.wait_for_function('!window.workspacePlanning.snapshot().loading && window.workspacePlanning.snapshot().failed')
        expect(page.locator('#course-status-board')).to_contain_text('Chưa tải được kết quả')
        expect(page.locator('[data-course-status-focus="refresh"]')).to_be_enabled()
        assert page.evaluate('updates.at(-1).loading') is False

        mode = 'ready'
        page.locator('[data-course-status-focus="refresh"]').click()
        page.wait_for_function('!workspacePlanning.snapshot().loading && !workspacePlanning.snapshot().failed')

        mode = 'selection-pending'
        page.locator('[data-course-status-focus="refresh"]').click()
        page.wait_for_function('workspacePlanning.snapshot().loading')
        page.wait_for_timeout(100)
        assert len(pending) >= 2
        page.clock.fast_forward(20001)
        page.wait_for_function('!workspacePlanning.snapshot().loading && workspacePlanning.snapshot().failed')

        mode = '401'
        page.locator('[data-course-status-focus="refresh"]').click()
        page.wait_for_function('!workspacePlanning.snapshot().loading && workspacePlanning.snapshot().board === null')
        assert page.evaluate('workspacePlanning.snapshot().failed') is True
        assert not errors, errors
        for route in pending:
            try:
                route.abort()
            except Exception:
                pass  # Already aborted by the real request's AbortController.
        browser.close()
    print('Course-status timeout, fallback-selection timeout, retry and 401 cleanup passed')


if __name__ == '__main__':
    main()
