"""Synthetic browser plan lifecycle; every request is intercepted, no VNU/DB."""

import copy
import mimetypes
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.check_course_status import course


def main():
    static = Path(__file__).resolve().parents[2] / 'app/static'
    saved, errors = [], []
    board_reads = []
    auth = session_payload()
    data = {'status': 'ready', 'context_revision': 'fake-session', 'plan_basis': 'a' * 64,
            'blocking_reasons': [], 'selections': {}, 'program_id': 'synthetic-program',
            'courses': {'completed': [], 'blocked': [], 'eligible': [
                course('TEST-A', 'Môn giả lập A', 3), course('TEST-B', 'Môn giả lập B', 4)]},
            'progress': {'total': {'earned_credits': 3, 'required_credits': 120, 'remaining_credits': 117}},
            'plan': {'course_codes': ['TEST-A'], 'max_credits': 20, 'suggested_credits': 3}}
    source = {'subject': 'synthetic-only', 'profile': {'program': 'Synthetic', 'cohort': '79'},
              'snapshot': {'completeness': 'complete', 'attempts': []}}

    def intercept(route):
        request = route.request
        path = urlsplit(request.url).path
        if path == '/auth/session':
            route.fulfill(json=auth)
        elif path == '/me/profile':
            route.fulfill(json=source)
        elif path == '/me/course-status':
            board_reads.append(request.url)
            if parse_qs(urlsplit(request.url).query).get('selected_track_id') == ['retired-track']:
                route.fulfill(status=422, json={'detail': 'academic_program_invalid'})
            else:
                route.fulfill(json=data)
        elif path == '/me/semester-plans' and request.method == 'GET':
            route.fulfill(json={'plans': saved})
        elif path.startswith('/me/semester-plans'):
            assert request.headers.get('x-csrf-token') == 'synthetic-browser-csrf'
            if request.method == 'DELETE':
                saved[:] = [row for row in saved if row['id'] != path.rsplit('/', 1)[-1]]
                route.fulfill(json={'deleted': True})
                return
            payload = request.post_data_json
            rows = [copy.deepcopy(row) for row in data['courses']['eligible'] if row['code'] in payload['course_codes']]
            item = {**payload, 'id': path.rsplit('/', 1)[-1] if request.method == 'PUT' else str(len(saved) + 1),
                    'version': payload.get('expected_version', 0) + 1, 'courses': rows,
                    'program_id': 'synthetic-program', 'total_credits': sum(row['credits'] for row in rows),
                    'needs_review': False, 'review_reasons': []}
            saved[:] = [row for row in saved if row['id'] != item['id']]
            saved.append(item)
            route.fulfill(status=201 if request.method == 'POST' else 200, json=item)
        elif path == '/' or path.startswith('/static/'):
            file = static / ('index.html' if path == '/' else path.removeprefix('/static/'))
            if file.is_file():
                route.fulfill(body=file.read_bytes(), content_type=mimetypes.guess_type(file)[0] or 'text/plain')
            else:
                route.fulfill(status=404)
        else:
            route.fulfill(status=401, json={'detail': 'session_expired'})

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel='chrome')
        try:
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            page.route('**/*', intercept)
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto('http://127.0.0.1:8000/#rules')
            page.wait_for_selector('#semester-plan-form')
            page.locator('#semester-plan-title').fill('HK1 — Phương án A')
            page.locator('[data-plan-code="TEST-B"]').check()
            page.reload()
            page.wait_for_selector('#semester-plan-form')
            page.wait_for_function("document.querySelector('[data-plan-code=\"TEST-B\"]')?.checked")
            assert page.locator('#semester-plan-title').input_value() == 'HK1 — Phương án A'
            reads = len(board_reads)
            page.evaluate("window.workspaceNavigate('tab-dashboard')")
            page.evaluate("window.workspaceNavigate('tab-rules')")
            page.evaluate("value => document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: value}))", source)
            page.wait_for_timeout(150)
            assert len(board_reads) == reads
            assert page.locator('[data-plan-code="TEST-B"]').is_checked()
            assert page.locator('#semester-plan-title').input_value() == 'HK1 — Phương án A'
            stored = page.evaluate("JSON.parse(sessionStorage.getItem('study-workspace-semester-draft-v1'))")
            assert stored['codes'] == ['TEST-A', 'TEST-B']
            assert not {'snapshot', 'cookies', 'password', 'csrf', 'grades'} & stored.keys()
            page.locator('#semester-plan-form button[type=submit]').click()
            page.wait_for_function("document.querySelector('#semester-plans').textContent.includes('Đã lưu kế hoạch')")
            assert saved[0]['total_credits'] == 7
            page.reload()
            page.wait_for_selector('#semester-plan-picker option[value="1"]', state='attached')
            page.locator('#semester-plan-picker').select_option('1')
            page.wait_for_function("document.querySelector('[data-plan-code=\"TEST-B\"]')?.checked")
            page.locator('#semester-plan-picker').select_option('')
            page.locator('#semester-plan-title').fill('HK1 — Phương án B')
            page.locator('#semester-plan-form button[type=submit]').click()
            page.wait_for_function("document.querySelectorAll('#semester-plan-picker option').length === 3")
            saved[0]['needs_review'] = True
            saved[0]['selected_track_id'] = 'retired-track'
            page.reload()
            page.wait_for_selector('#semester-plan-picker option[value="1"]', state='attached')
            page.locator('#semester-plan-picker').select_option('1')
            page.wait_for_function("document.querySelector('#semester-plans').textContent.includes('Bảng điểm, chương trình hoặc quy chế đã thay đổi')")
            page.wait_for_selector('[data-plan-code="TEST-B"]')
            assert 'Hướng/nhánh cũ không còn phù hợp' in page.locator('#semester-plans').inner_text()
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.locator('#semester-plan-form').is_visible()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path='/tmp/semester-plans-mobile.png', full_page=True)
            page.locator('[data-language-choice=en]').click()
            assert page.locator('#semester-plans').get_by_text('Saved semester plans', exact=True).is_visible()
            page.on('dialog', lambda dialog: dialog.accept())
            page.locator('#semester-plans').get_by_role('button', name='Delete alternative', exact=True).click()
            page.wait_for_function("document.querySelectorAll('#semester-plan-picker option').length === 2")
            page.locator('#semester-plan-title').fill('Do not carry into a new login')
            auth['account']['session_id'] = '00000000-0000-4000-8000-000000000099'
            page.evaluate('async () => { await window.systemAuth.refresh(); }')
            page.wait_for_function("document.querySelector('#semester-plan-title')?.value === ''")
            assert 'Do not carry' not in (page.evaluate("sessionStorage.getItem('study-workspace-semester-draft-v1')") or '')
            page.evaluate("document.dispatchEvent(new Event('workspace:session-expired'))")
            assert page.locator('#semester-plan-form').count() == 0
            assert page.evaluate("sessionStorage.getItem('study-workspace-semester-draft-v1')") is None
            assert not errors, errors
        finally:
            browser.close()
    print('PASS: create, reload, multiple plans, stale warning, mobile, EN, delete and logout cleanup')


if __name__ == '__main__':
    main()
