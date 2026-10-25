"""Collection rejection feedback through the current session/reauth UI."""
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import session_payload


def main():
    state = {'authenticated': True, 'job': 'running', 'review': None}
    errors = []
    report = {'connector_version': 'vnu-full-table-20261025', 'completeness': 'unknown',
        'save_status': 'retained', 'unparsed_rows': 0, 'evidence': {
            'source_host_valid': True, 'source_path_valid': True, 'transcript_container_valid': True,
            'filters_absent': False, 'pagination_absent': True, 'hidden_records_absent': True,
            'virtualization_absent': True, 'loading_absent': True, 'network_idle': True,
            'stable_reads': 3, 'data_table_count': 1}}
    source = {'subject': 'synthetic-only', 'profile': {'program': 'Synthetic', 'cohort': '68'},
        'snapshot': {'completeness': 'unknown', 'attempts': [], 'unknown_rows': [], 'source_summary': []}}

    def intercept(route):
        path = urlsplit(route.request.url).path
        if path == '/auth/session':
            route.fulfill(json=session_payload(state['authenticated']))
        elif path == '/me/profile':
            route.fulfill(json={**source, 'latest_collection': state['review']})
        elif path == '/me/portal-sync':
            route.fulfill(json={'state': 'reauth_required'})
        elif path == '/me/portal-reauth':
            assert route.request.post_data_json == {'password': 'invented-password'}
            assert route.request.headers['x-csrf-token'] == 'synthetic-browser-csrf'
            route.fulfill(status=202, json={'id': 'synthetic-job', 'state': 'running'})
        elif path == '/me/portal-sync/synthetic-job':
            value = {'state': state['job']}
            if state['job'] == 'failed':
                state['review'] = report
                value['error'] = 'incomplete_snapshot'
            route.fulfill(json=value)
        elif path == '/me/course-status':
            route.fulfill(json={'status': 'needs_source_review', 'blocking_reasons': ['source_incomplete'],
                'courses': None, 'collection_status': {'completeness': 'unknown'},
                'latest_collection': state['review']})
        elif path == '/auth/logout':
            state['authenticated'] = False
            route.fulfill(json={'logged_out': True})
        elif path.startswith(('/me/', '/auth/')):
            route.fulfill(status=401, json={'detail': 'session_expired'})
        elif path == '/' or path.startswith('/static/'):
            route.continue_()
        else:
            route.abort()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/*', intercept)
        page.goto('http://127.0.0.1:8000/#rules')
        root = page.locator('#course-status-board')
        root.get_by_role('button', name='Cập nhật bảng điểm VNU', exact=True).click()
        page.locator('#portal-reauth').wait_for(state='visible')
        page.locator('#portal-reauth-password').fill('invented-password')
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        assert page.locator('#portal-reauth-password').input_value() == 'invented-password'
        page.locator('#portal-reauth-submit').click()
        page.wait_for_selector('#portal-status.is-loading')
        page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
        assert page.locator('#portal-status.is-loading').count() == 1
        state['job'] = 'failed'
        page.wait_for_function("document.querySelector('#portal-collection-review').textContent.includes('điều khiển lọc')")
        assert page.locator('#portal-reauth-password').input_value() == ''
        page.locator('#tab-btn-rules').click()
        page.wait_for_function("document.querySelector('#course-status-board').textContent.includes('điều khiển lọc')")
        page.locator('[data-language-choice="en"]').click()
        assert 'Detected filter controls' in root.inner_text()
        page.locator('#tab-btn-profile').click()
        page.reload()
        page.wait_for_function("document.querySelector('#portal-collection-review').textContent.includes('previous transcript')")
        evidence = Path('backups/eligibility-integration-ui')
        evidence.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(evidence / 'rejected-sync.png'), full_page=True)
        page.locator('#system-logout').click()
        page.wait_for_function("document.querySelector('#portal-collection-review').hidden")
        assert page.locator('#portal-collection-review').inner_text() == ''
        assert not errors, errors
        browser.close()
    print('Sync feedback: current CSRF/reauth, retained source, progress, reload, VI/EN and logout passed')


if __name__ == '__main__':
    main()
