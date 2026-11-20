"""Visual smoke test of the real admin page with deterministic dashboard API fixtures.

Run with a static server serving app/: python -m http.server 8765 --directory app
Screenshots are fixtures, not production statistics.
"""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get('ADMIN_UI_TEST_URL', 'http://127.0.0.1:8765/static/index.html')
EVIDENCE = Path('backups/admin_dashboard_insights_20261105')

OVERVIEW = {
    'accounts_total': {'value': 125, 'status': 'available', 'source': 'postgres:accounts'},
    'programs_count': {'value': 4, 'status': 'available', 'source': 'catalog:active'},
    'courses_count': {'value': 174, 'status': 'available', 'source': 'catalog:active'},
    'catalog_status': {'value': 'draft_unverified', 'status': 'available', 'source': 'catalog:active'},
    'system_readiness': {'value': 'operational', 'status': 'available', 'source': 'system:checks'},
}

INSIGHTS = {
    'students': {'status': 'available', 'data': {
        'students_total': 123, 'gpa4_average': 3.2, 'gpa4_sample_count': 60,
        'credits_average': 80, 'credits_sample_count': 60,
        'progress_average_pct': None, 'progress_sample_count': 0,
        'by_cohort': [{'label': 'K68', 'count': 70}, {'label': 'K67', 'count': 53}],
        'by_program': [{'label': 'Khoa học máy tính và thông tin', 'count': 80},
                       {'label': 'Toán học', 'count': 43}],
    }},
    'courses': {'status': 'available', 'data': {
        'course_memberships': 220, 'elective_count': 50, 'with_prerequisites': 92,
        'by_program': [{'label': 'Khoa học máy tính và thông tin', 'count': 120},
                       {'label': 'Toán học', 'count': 100}],
        'by_suggested_term': [{'label': 'Kỳ dự kiến 1', 'count': 80},
                              {'label': 'Kỳ dự kiến 2', 'count': 70}],
    }},
}
HEALTH = {
    'window': '24h', 'note': 'Số liệu chỉ trong phiên chạy hiện tại.', 'sample_count': 150,
    'overall_health': {'status': 'available', 'total_requests': 150,
                       'success_rate_pct': 98, 'server_error_rate_pct': 1,
                       'p50_latency_ms': 45, 'p95_latency_ms': 120},
    'consultation_health': {'status': 'available', 'total_consultations': 40,
                            'successful_consultations': 38, 'failed_consultations': 2,
                            'recommendation_total': 40, 'recommendation_success_rate_pct': 95,
                            'failure_rate_pct': 5, 'avg_duration_ms': 70,
                            'top_failure_reasons': []},
    'feedback_signals': {'status': 'available', 'total_feedbacks': 20,
                         'positive_rate_pct': 80, 'average_rating': 4.1,
                         'negative_count': 2,
                         'by_category': [{'category': 'recommendation', 'count': 14},
                                         {'category': 'advisor', 'count': 6}]},
    'recommendation_insights': {'status': 'available', 'total_runs': 40,
                                'average_fit_pct': 75,
                                'top_courses': [{'code': 'MAT1001', 'count': 15},
                                                {'code': 'HUS1011', 'count': 9}],
                                'reason_categories': [{'category': 'topic', 'count': 16},
                                                      {'category': 'career', 'count': 8}]},
    'route_groups': {},
}


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        page.goto(BASE)
        page.wait_for_function('window.adminOverview && window.systemAuth')
        page.evaluate('''([overview, insights, health]) => {
            document.body.dataset.authState = 'admin';
            document.querySelector('#system-admin').hidden = false;
            document.querySelector('#admin-notice').style.display = 'none';
            document.querySelector('.skip-link').style.display = 'none';
            window.systemAuth = {
              account: {account_id: 'fixture-admin', role: 'admin'},
              switchAdminTab() {},
              async request(path) {
                (window.__dashboardRequests ||= []).push(path);
                if (path === '/admin/overview') return overview;
                if (path === '/admin/programs') return [];
                if (path === '/admin/insights') return insights;
                if (path.startsWith('/admin/metrics/health')) return health;
                throw Error('Unexpected dashboard request: ' + path);
              }
            };
            document.dispatchEvent(new CustomEvent('workspace:account-change', {detail: window.systemAuth.account}));
        }''', [OVERVIEW, INSIGHTS, HEALTH])
        page.evaluate('window.adminOverview.load()')
        page.locator('#admin-feedback-insights .admin-dashboard-stat').first.wait_for()
        assert page.locator('#admin-overview-grid .admin-kpi-card').count() == 4
        assert '/admin/overview' in page.evaluate('window.__dashboardRequests')
        assert page.locator('#admin-overview-refresh').inner_text().strip() == 'Làm mới'
        for title in ('Tổng quan hệ thống', 'Quản lý sinh viên', 'Quản lý học phần',
                      'Phân tích gợi ý AI', 'Phản hồi sinh viên'):
            assert title in page.locator('#admin-panel-overview').inner_text()
        assert page.locator('#admin-dashboard-students').is_visible()
        assert page.locator('#admin-dashboard-monitoring').is_visible()
        assert page.locator('.admin-dashboard-nav a').count() == 6
        assert page.locator('#admin-highlight-success').inner_text() == '95%'
        assert 'Khớp chủ đề' in page.locator('#admin-recommendation-insights').inner_text()
        assert 'recommendation' in page.locator('#admin-feedback-insights').inner_text()
        width = page.locator('#system-admin').evaluate('(node) => Math.round(node.getBoundingClientRect().width)')
        assert width > 1200, width
        page.locator('#system-admin').screenshot(path=str(EVIDENCE / 'admin_desktop.png'))
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.locator('#system-admin').screenshot(path=str(EVIDENCE / 'admin_mobile.png'))
        page.locator('.admin-dashboard-nav a[href="#admin-dashboard-feedback"]').click()
        assert page.evaluate('location.hash') == '#admin-dashboard-feedback'
        page.evaluate('''() => {
            window.systemAuth.request = async path => {
              if (path === '/admin/insights') return {
                students: {status: 'unavailable'}, courses: {status: 'unavailable'}
              };
              if (path.startsWith('/admin/metrics/health')) return {
                note: 'Phiên mới', overall_health: {status: 'unavailable'},
                consultation_health: {status: 'unavailable'},
                feedback_signals: {status: 'unavailable'},
                recommendation_insights: {status: 'unavailable'}, route_groups: {}
              };
            };
        }''')
        page.evaluate('window.adminOverview.load(true)')
        page.wait_for_function("document.querySelector('#admin-highlight-students').textContent === 'Chưa có dữ liệu'")
        assert 'Chưa có lượt gợi ý' in page.locator('#admin-recommendation-insights').inner_text()
        page.evaluate("document.dispatchEvent(new CustomEvent('workspace:account-change', {detail: null}))")
        assert page.locator('#admin-student-insights').inner_text() == ''
        page.evaluate('''([insights, health]) => {
            document.dispatchEvent(new CustomEvent('workspace:account-change', {detail: window.systemAuth.account}));
            window.systemAuth.request = async path => {
              if (path === '/admin/insights') return insights;
              if (path.startsWith('/admin/metrics/health')) return health;
            };
        }''', [INSIGHTS, HEALTH])
        page.evaluate('window.adminOverview.load(true)')
        page.wait_for_function("document.querySelector('#admin-highlight-students').textContent === '123'")
        assert page.locator('#admin-dashboard-students').is_visible()

        page.context.route('https://mim.hus.vnu.edu.vn/sites/default/files/**',
                           lambda route: route.fulfill(status=200, content_type='text/html',
                                                       body='<title>PDF destination</title>'))
        page.evaluate('''() => {
            window.systemAuth.request = async path => {
              if (path.startsWith('/admin/courses?')) return [];
              throw Error('Unexpected curriculum request: ' + path);
            };
        }''')
        page.set_viewport_size({'width': 1440, 'height': 900})
        page.locator('#admin-panel-curriculum').evaluate('node => node.hidden = false')
        for program_id in ('khdl_7460108_2022', 'khmtt_7480113qtd_2022',
                           'toan_hoc_7460101_2022', 'toan_tin_7460117_2022'):
            page.evaluate('''programId => window.adminCurriculum.openProgramCourses({
                program_id: programId, name: 'Synthetic program', total_credits: 120,
                course_count: 0, catalog_status: 'draft_unverified',
                source_file: 'Official curriculum.pdf'
            })''', program_id)
            link = page.locator('#admin-detail-source-file')
            assert link.inner_text() == 'Official curriculum.pdf'
            href = link.get_attribute('href')
            assert href.startswith('https://mim.hus.vnu.edu.vn/sites/default/files/')
            assert href.endswith('.pdf')
            assert link.get_attribute('target') == '_blank'
            assert 'Trang nguồn' not in page.locator('.admin-curriculum-provenance-box').inner_text()
            with page.expect_popup() as opened:
                link.click()
            popup = opened.value
            popup.wait_for_load_state()
            assert popup.url == href
            popup.close()
        page.locator('#admin-curriculum-detail-view').screenshot(path=str(EVIDENCE / 'admin_pdf_link.png'))
        browser.close()
    print('Admin dashboard browser checks passed; screenshots:', EVIDENCE)


if __name__ == '__main__':
    main()
