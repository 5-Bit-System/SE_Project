"""Recommendation UI against intercepted, invented data; no VNU, model or DB calls."""

import copy
import json
import shutil
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect, sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.check_course_status import course
from tests.frontend.presentation_fixture import common_route


def main():
    evidence = Path('backups/recommendation_workspace_20261101')
    evidence.mkdir(parents=True, exist_ok=True)
    auth = session_payload()
    group = {'id': 'ai-choice', 'name': 'Synthetic choice', 'required_credits': 3,
             'earned_credits': 0, 'remaining_credits': 3}
    rows = [course('B200', 'Môn bắt buộc minh họa', 3, requirement_type='required'),
            course('C300', 'Học máy minh họa', 3, requirement_type='elective', groups=[group]),
            course('D301', 'Môn tự chọn minh họa', 3, requirement_type='elective', groups=[group]),
            course('E400', '<img src=x onerror=alert(1)>', 4),
            course('F500', 'Môn nối tiếp không được lưu', 3, planning_eligible=False,
                   eligibility_basis='available_prerequisites')]
    metadata = {row['code']: {**row, 'prerequisites': [['A100']],
                'prerequisite_status': 'verified', 'source_status': 'verified'} for row in rows}
    metadata['A100'] = {**course('A100', 'Môn nền tảng đã hoàn thành', 3), 'prerequisites': []}
    source = {'subject': 'synthetic-only', 'profile': {'program': 'Chương trình minh họa', 'cohort': '68'},
              'snapshot': {'digest': 'synthetic-snapshot', 'completeness': 'complete', 'attempts': []}}
    plans, requests, errors, pending = [], [], [], []
    mode = 'ready'
    save_mode = 'saved'

    def revision(query):
        return 'synthetic-' + query.get('selected_track_id', ['none'])[0] + '-' + query.get('selected_graduation_path_id', ['none'])[0]

    def intercept(route):
        nonlocal mode
        request = route.request
        parsed = urlsplit(request.url)
        path, query = parsed.path, parse_qs(parsed.query)
        requests.append((path, request.method))
        if path == '/auth/session':
            route.fulfill(json=auth)
        elif path == '/me/profile':
            route.fulfill(json=source)
        elif path == '/me/course-status':
            ready = bool(query.get('selected_track_id') and query.get('selected_graduation_path_id'))
            route.fulfill(json={
                'status': 'ready' if ready else 'partial', 'can_plan': ready,
                'program_id': 'synthetic-program', 'program_name': 'Chương trình minh họa',
                'catalog_status': 'verified', 'context_revision': revision(query), 'plan_basis': 'a' * 64,
                'blocking_reasons': [] if ready else ['track_selection_required', 'graduation_selection_required'],
                'selections': {'track_required': True, 'path_required': True,
                    'tracks': [{'id': 'track-ai', 'name': 'Trí tuệ nhân tạo'}, {'id': 'track-software', 'name': 'Phần mềm'}],
                    'paths': [{'id': 'thesis', 'name': 'Khóa luận tốt nghiệp', 'allowed_track_ids': ['track-ai', 'track-software']},
                              {'id': 'courses', 'name': 'Học phần thay thế', 'allowed_track_ids': ['track-ai', 'track-software']}]},
                'courses': {'completed': [metadata['A100']], 'eligible': copy.deepcopy(rows), 'blocked': []},
                'progress': {'total': {'earned_credits': 3, 'required_credits': 120, 'remaining_credits': 117}},
                'plan': {'course_codes': ['B200', 'C300'] if ready else [],
                         'max_credits': int(query.get('max_credits', ['20'])[0]), 'suggested_credits': 6 if ready else 0},
            })
        elif path == '/courses':
            route.fulfill(json=list(metadata.values()))
        elif path == '/me/academic-context':
            route.fulfill(json={'status': 'needs_policy_review' if mode == 'unready' else 'ready',
                'revision': revision(query), 'completed_course_codes': ['A100']})
        elif path == '/me/recommendations':
            payload = request.post_data_json
            assert request.headers['x-csrf-token'] == 'synthetic-browser-csrf'
            assert payload['max_credits'] == 20
            assert payload['selected_track_id'] == 'track-ai'
            assert payload['selected_graduation_path_id'] == 'thesis'
            assert payload['preference']['course_type'] == 'required'
            assert payload['preference']['workload'] == 'moderate'
            assert payload['ranking_weights']['workload'] > 0
            assert 'passed_course_codes' not in payload and 'owner' not in payload
            if mode == 'pending':
                pending.append(route)
                return
            if mode == 'failed' or (mode == 'partial' and payload['ranking_weights']['topic'] > .6):
                route.fulfill(status=503, json={'detail': 'temporary_failure'})
                return
            weights = payload['ranking_weights']
            selected = ['B200', 'E400'] if weights['course_type'] > .6 else ['C300', 'D301', 'F500'] if weights['topic'] > .6 else ['B200', 'C300', 'E400']
            route.fulfill(json={'context_revision': payload['expected_revision'], 'catalog_status': 'verified',
                'recommendations': [{**next(row for row in rows if row['code'] == code),
                    'reason': 'Giải thích từ phản hồi API giả lập.', 'fit_reason': 'Phù hợp mục tiêu minh họa.'} for code in selected],
                'warnings': ['Lịch mở lớp chưa xác nhận.']})
        elif path == '/me/semester-plans' and request.method == 'GET':
            route.fulfill(json={'plans': plans})
        elif path == '/me/semester-plans' and request.method == 'POST':
            assert request.headers['x-csrf-token'] == 'synthetic-browser-csrf'
            if save_mode == 'failed':
                route.fulfill(status=409, json={'detail': 'context_changed'})
                return
            payload = request.post_data_json
            assert payload['expected_basis'] == 'a' * 64
            assert 'F500' not in payload['course_codes']
            saved_rows = [row for row in rows if row['code'] in payload['course_codes']]
            result = {**payload, 'id': str(len(plans) + 1), 'version': 1, 'courses': saved_rows,
                'program_id': 'synthetic-program', 'total_credits': sum(row['credits'] for row in saved_rows),
                'needs_review': False, 'review_reasons': []}
            plans.append(result)
            if save_mode == 'uncertain':
                route.abort('failed')  # The server committed, but the response was lost.
                return
            route.fulfill(status=201, json=result)
        elif not common_route(route):
            route.abort()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome', headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='no-preference',
            record_video_dir=str(evidence / 'recording'), record_video_size={'width': 1440, 'height': 1000})
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/*', intercept)
        page.goto('http://127.0.0.1:8000/#recommend')
        expect(page.locator('[data-rec-direction="track-ai"]')).to_be_visible()
        page.screenshot(path=str(evidence / 'landing-light-1440.png'), full_page=True)
        page.locator('[data-rec-direction="track-ai"]').click()
        assert page.locator('.rec-flying-chip').count() == 1
        expect(page.locator('#rec-credit-budget')).to_have_value('20')
        page.locator('#rec-credit-budget').fill('0')
        page.get_by_role('button', name='Đúng nhịp của mình', exact=True).click()
        expect(page.locator('#rec-credit-budget')).to_be_visible()
        page.locator('#rec-credit-budget').fill('20')
        page.get_by_role('button', name='Đúng nhịp của mình', exact=True).click()
        page.get_by_role('button', name='Ghi nhận mục tiêu', exact=True).click()
        page.locator('[data-rec-path="thesis"]').click()
        assert plans == []
        page.locator('#rec-goal').fill('Mình muốn ưu tiên học máy.')
        page.locator('.rec-send').click()
        expect(page.locator('.rec-free-goal')).to_contain_text('ưu tiên học máy')
        page.locator('#rec-generate').click()
        expect(page.locator('#rec-save')).to_be_enabled(timeout=15000)
        assert page.locator('.rec-course').first.evaluate("element => element.getAnimations().some(animation => animation.playState === 'running')")
        assert len([item for item in requests if item == ('/me/recommendations', 'POST')]) == 3
        expect(page.locator('.rec-course')).to_have_count(3)
        assert page.locator('.rec-course img').count() == 0
        assert '10 / 20 tín chỉ' in page.locator('.rec-plan-caption').inner_text()
        page.screenshot(path=str(evidence / 'results-light-1440.png'), full_page=True)
        page.locator('.rec-course').first.get_by_role('button', name='Vì sao môn này?', exact=True).click()
        expect(page.locator('.rec-dialog')).to_be_visible()
        assert 'A100: Môn nền tảng đã hoàn thành' in page.locator('.rec-dialog').inner_text()
        page.keyboard.press('Escape')
        expect(page.locator('.rec-dialog')).not_to_be_visible()
        page.locator('[data-rec-variant="direction"]').click()
        expect(page.locator('.rec-course')).to_have_count(1)
        assert 'C300' in page.locator('.rec-course').inner_text()
        page.locator('#rec-compare').click()
        expect(page.locator('.rec-compare-dialog table')).to_be_visible()
        assert 'E400' in page.locator('.rec-compare-dialog table').inner_text()
        page.keyboard.press('Escape')
        page.locator('[data-rec-variant="balanced"]').click()
        save_mode = 'failed'
        page.locator('#rec-save').click()
        page.get_by_role('button', name='Xác nhận lưu', exact=True).click()
        expect(page.locator('#rec-save-status')).to_contain_text('đã thay đổi')
        assert not plans and page.locator('.rec-save-success').count() == 0
        page.keyboard.press('Escape')
        save_mode = 'saved'
        page.locator('#rec-save').click()
        page.get_by_role('button', name='Xác nhận lưu', exact=True).click()
        expect(page.locator('.rec-save-success')).to_contain_text('Đã lưu phương án')
        assert len(plans) == 1
        page.screenshot(path=str(evidence / 'saved.png'))
        page.keyboard.press('Escape')
        save_mode = 'uncertain'
        page.locator('[data-rec-variant="direction"]').click()
        page.locator('#rec-save').click()
        page.get_by_role('button', name='Xác nhận lưu', exact=True).click()
        expect(page.locator('#rec-save-status')).to_contain_text('Chưa xác nhận được kết quả lưu')
        assert len(plans) == 2 and page.locator('.rec-save-success').count() == 0
        assert page.get_by_role('button', name='Xác nhận lưu', exact=True).is_disabled()
        page.keyboard.press('Escape')
        expect(page.locator('#rec-save')).to_have_text('Kiểm tra kết quả lưu')
        post_count = requests.count(('/me/semester-plans', 'POST'))
        page.locator('#rec-save').click()
        assert page.locator('#academic-plan-tools').evaluate('element => element.open')
        assert requests.count(('/me/semester-plans', 'POST')) == post_count
        page.locator('#academic-plan-tools > summary').click()
        page.locator('[data-rec-variant="balanced"]').click()
        save_mode = 'saved'
        for width in (1440, 1024, 390):
            page.set_viewport_size({'width': width, 'height': 1000})
            for theme in ('light', 'dark'):
                page.locator(f'[data-theme-choice="{theme}"]').click()
                page.wait_for_timeout(300)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, theme)
                page.screenshot(path=str(evidence / f'results-{theme}-{width}.png'), full_page=True)
        page.locator('.rec-mobile-roadmap').click()
        expect(page.locator('.rec-roadmap-sheet')).to_be_visible()
        page.keyboard.press('Escape')
        page.locator('[data-language-choice=en]').click()
        expect(page.get_by_role('heading', name='Your next semester, your way.')).to_be_visible()
        page.emulate_media(reduced_motion='reduce')
        page.locator('[data-rec-variant="direction"]').click()
        assert page.locator('.rec-flying-chip').count() == 0
        page.locator('[data-language-choice=vi]').click()
        page.set_viewport_size({'width': 1440, 'height': 1000})
        mode = 'unready'
        page.locator('#rec-generate').click()
        expect(page.locator('.rec-error')).to_contain_text('chưa đủ xác minh')
        assert page.locator('.rec-course').count() == 0
        mode = 'partial'
        page.locator('#rec-generate').click()
        expect(page.locator('[data-rec-variant="balanced"]')).to_be_visible()
        page.locator('[data-rec-variant="balanced"]').click()
        expect(page.locator('#rec-save')).to_be_enabled()
        page.locator('[data-rec-variant="direction"]').click()
        expect(page.locator('#rec-plan-content .rec-error')).to_be_visible()
        assert page.locator('.rec-course').count() == 0
        assert page.locator('#rec-compare').is_enabled()
        mode = 'failed'
        page.locator('#rec-generate').click()
        expect(page.locator('#rec-plan-content .rec-error')).to_be_visible()
        assert page.locator('.rec-course').count() == 0
        page.emulate_media(reduced_motion='no-preference')
        mode = 'pending'
        page.locator('#rec-generate').click()
        page.wait_for_function("document.querySelector('.rec-loading') !== null")
        assert pending
        before_motion = page.locator('.rec-loading-papers i').first.evaluate('element => getComputedStyle(element).transform')
        page.wait_for_timeout(180)
        after_motion = page.locator('.rec-loading-papers i').first.evaluate('element => getComputedStyle(element).transform')
        assert before_motion != after_motion
        page.locator('#tab-btn-dashboard').click()
        assert page.locator('.rec-loading-papers i').first.evaluate("element => getComputedStyle(element).animationPlayState === 'paused'")
        page.locator('#tab-btn-recommend').click()
        page.evaluate("document.dispatchEvent(new Event('workspace:session-expired'))")
        for route in pending:
            try:
                route.fulfill(json={'context_revision': 'old', 'recommendations': [{'code': 'PRIVATE-OLD'}]})
            except Exception:
                pass  # Browser cancellation may already have closed this route.
        page.wait_for_timeout(150)
        assert page.locator('.rec-course').count() == 0
        assert 'PRIVATE-OLD' not in page.locator('#recommendation-workspace').inner_text()
        assert page.locator('.rec-dialog').count() == 1
        assert not errors, errors
        assert not {path for path, _ in requests} & {'/recommendations', '/advisor/chat', '/me/recommendations/what-if'}
        (evidence / 'verification.json').write_text(json.dumps({'passed': True, 'api_intercepted': True,
            'viewports': [1440, 1024, 390], 'themes': ['light', 'dark'], 'no_real_personal_data': True}, indent=2), encoding='utf-8')
        video = page.video
        context.close()
        shutil.copyfile(video.path(), evidence / 'recommendation-preview.webm')
        browser.close()
    print('Recommendation workspace: wizard, three API fixtures, quotas, details, compare, save/error/lost response, VI/EN, mobile/themes/reduced and logout race passed')


if __name__ == '__main__':
    main()
