"""Verify the production blue admin workspace with isolated API fixtures.

No real credentials, student records, database or provider calls are used.
Run: .venv/Scripts/python.exe -m tests.frontend.check_admin_dashboard_blue
"""

import copy
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.check_admin_dashboard_insights import HEALTH, INSIGHTS, OVERVIEW
from tests.frontend.presentation_fixture import common_route

EVIDENCE = Path('backups/admin_dashboard_blue_20261107')
PROGRAMS = [
    {'program_id': f'synthetic_{index}_2022', 'name': name, 'cohort': '2022',
     'course_count': count, 'total_credits': credits,
     'catalog_status': 'verified' if index == 1 else 'draft_unverified',
     'catalog_revision': f'synthetic-revision-{index}', 'source_file': 'synthetic.pdf',
     'source_pages': [], 'notes': []}
    for index, (name, count, credits) in enumerate([
        ('Khoa học dữ liệu', 65, 127), ('Khoa học máy tính và thông tin', 67, 129),
        ('Toán học', 90, 135), ('Toán tin', 68, 132),
    ])
]


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    account = session_payload()
    account['account'].update(role='admin', auth_method='local', vnu_subject=None,
                              display_name='Synthetic administrator')
    overview = copy.deepcopy(OVERVIEW)
    overview['catalog_status']['details'] = {'statuses': {
        item['program_id']: item['catalog_status'] for item in PROGRAMS
    }}
    overview['document_review_status'] = {
        'value': 44,
        'status': 'available',
        'source': 'postgres:crawled_documents',
        'details': {'total': 44, 'approved': 21, 'pending': 2, 'rejected': 21},
    }
    health = copy.deepcopy(HEALTH)
    for key, count in zip(('academic', 'portal', 'auth', 'consultation', 'admin', 'other'),
                          (30, 20, 35, 40, 20, 5)):
        health['route_groups'][key] = {
            'status': 'available', 'total_requests': count, 'success_rate_pct': 98,
            'error_rate_pct': 2, 'p50_latency_ms': 45, 'p95_latency_ms': 120,
        }
    state = {'health_error': False, 'insights_error': False, 'programs_error': False}
    requests, errors, checks = [], [], []

    def intercept(route):
        path = urlsplit(route.request.url).path
        requests.append(route.request.url)
        if path == '/auth/session':
            route.fulfill(json=account)
        elif path == '/admin/overview':
            route.fulfill(json=overview)
        elif path == '/admin/insights':
            route.fulfill(status=503 if state['insights_error'] else 200,
                          json={'detail': 'unavailable'} if state['insights_error'] else INSIGHTS)
        elif path == '/admin/programs':
            route.fulfill(status=503 if state['programs_error'] else 200,
                          json={'detail': 'unavailable'} if state['programs_error'] else PROGRAMS)
        elif path == '/admin/metrics/health':
            value = {**health, 'window': dict(part.split('=') for part in urlsplit(route.request.url).query.split('&'))['window']}
            route.fulfill(status=503 if state['health_error'] else 200,
                          json={'detail': 'unavailable'} if state['health_error'] else value)
        elif path == '/admin/courses':
            route.fulfill(json=[{'code': 'SYN1001', 'name': 'Synthetic course', 'credits': 3,
                                 'prerequisites': [], 'source_status': 'draft_unverified'}])
        elif path.startswith('/admin/'):
            route.fulfill(json={'items': [], 'total': 0})
        elif path.startswith('/me/'):
            raise AssertionError('Admin must not load student endpoints: ' + path)
        elif common_route(route):
            return
        else:
            route.abort()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        try:
            page = browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
            page.on('pageerror', lambda err: errors.append(str(err)))
            page.route('**/*', intercept)
            page.goto('http://127.0.0.1:8000/')
            expect(page.locator('#system-admin')).to_be_visible()
            expect(page.locator('#ad-membership-card [data-metric="memberships"]')).to_have_text('220')
            expect(page.locator('#ad-program-table')).to_have_count(0)
            expect(page.locator('#ad-program-search')).to_have_count(0)
            expect(page.locator('.ad-column')).to_have_count(6)
            expect(page.locator('.ad-donut-wrap')).to_contain_text('44')
            expect(page.locator('.ad-verification-legend')).to_contain_text('Đã duyệt')
            expect(page.locator('.ad-verification-legend')).to_contain_text('21')
            expect(page.locator('.ad-verification-legend')).to_contain_text('Chờ duyệt')
            expect(page.locator('.ad-verification-legend')).to_contain_text('2')
            expect(page.locator('.ad-verification-legend')).to_contain_text('Từ chối')
            expect(page.locator('#ad-catalog-heading')).to_have_text('Kiểm duyệt tài liệu')
            assert page.locator('#ad-status-cards [data-readiness="operational"]').is_visible()
            assert page.locator('#system-admin').evaluate("e => getComputedStyle(e).getPropertyValue('--ad-blue').trim()") == '#3476dc'
            checks.append('Authenticated production shell uses blue and real API contracts')

            assert page.locator('.ad-program-card').count() == 0
            checks.append('Redundant program table removed from overview dashboard')

            page.locator('.ad-activity-card [data-window="1h"]').click()
            expect(page.locator('.ad-traffic-total .ad-source-pill')).to_have_text('1h')
            assert page.locator('[data-window="1h"][aria-pressed="true"]').count() == 2
            checks.append('Time windows reload the API and synchronize both selectors')

            page.locator('#admin-tab-curriculum').click()
            expect(page.locator('#admin-panel-curriculum')).to_be_visible()
            page.locator('#admin-tab-overview').click()
            expect(page.locator('.ad-column')).to_have_count(6)
            checks.append('Dashboard navigation preserves curriculum management')

            state.update(health_error=True, insights_error=True, programs_error=True)
            page.locator('#admin-overview-refresh').click()
            expect(page.locator('#ad-traffic-chart .ad-empty')).to_be_visible()
            expect(page.locator('[data-metric="memberships"]')).to_have_text('Chưa có dữ liệu')
            assert page.locator('#admin-route-groups-tbody tr').count() == 0
            assert page.locator('#admin-student-insights .ad-student-visual').count() == 0
            checks.append('Failed reads clear old charts, rows and student aggregates')
            state.update(health_error=False, insights_error=False, programs_error=False)
            page.locator('#admin-overview-refresh').click()
            expect(page.locator('.ad-column')).to_have_count(6)

            for width, height in [(1920, 1080), (1440, 1000), (1024, 900), (768, 1024), (390, 844), (360, 800)]:
                page.set_viewport_size({'width': width, 'height': height})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
                if width in (1440, 390):
                    page.screenshot(path=str(EVIDENCE / f'dashboard-{width}.png'), full_page=True)
                if width == 390:
                    assert page.locator('#admin-sidebar').evaluate('e => e.inert')
                    page.locator('#admin-sidebar-toggle').click()
                    assert not page.locator('#admin-sidebar').evaluate('e => e.inert')
                    page.locator('#admin-tab-curriculum').click()
                    assert page.locator('#admin-sidebar').evaluate('e => e.inert')
                    page.locator('#admin-sidebar-toggle').click()
                    page.locator('#admin-tab-overview').click()
            checks.append('Six responsive widths and accessible mobile sidebar')

            page.set_viewport_size({'width': 1440, 'height': 1000})
            page.locator('#system-menu-toggle').click()
            page.locator('[data-theme-choice="dark"]').click()
            page.keyboard.press('Escape')
            page.screenshot(path=str(EVIDENCE / 'dashboard-dark.png'), full_page=True)
            page.locator('#system-menu-toggle').click()
            page.locator('[data-language-choice="en"]').click()
            expect(page.locator('#ad-activity-heading')).to_have_text('System activity')
            expect(page.locator('#ad-catalog-heading')).to_have_text('Document review')
            page.locator('[data-language-choice="vi"]').click()
            expect(page.locator('#ad-catalog-heading')).to_have_text('Kiểm duyệt tài liệu')
            page.keyboard.press('Escape')
            page.locator('#system-menu-toggle').click()
            page.locator('[data-theme-choice="light"]').click()
            page.keyboard.press('Escape')
            checks.append('Dark theme and language controls remain operational')

            page.evaluate("document.dispatchEvent(new CustomEvent('workspace:account-change', {detail: null}))")
            assert page.locator('#ad-traffic-chart').inner_text() == ''
            assert page.locator('#ad-program-table').count() == 0
            assert page.locator('#ad-catalog-chart').inner_text() == ''
            checks.append('Account changes clear all new dashboard data')
            assert not errors, errors
            assert not any('/me/' in url for url in requests)
            checks.append('No JavaScript errors, student requests or real API traffic')
        finally:
            browser.close()
    (EVIDENCE / 'verification.json').write_text(json.dumps({'checks': checks, 'errors': errors}, indent=2), encoding='utf-8')
    print(json.dumps({'passed': len(checks), 'checks': checks}, indent=2))


if __name__ == '__main__':
    main()
