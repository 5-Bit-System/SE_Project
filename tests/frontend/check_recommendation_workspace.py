"""Recommendation UI against intercepted, invented data; no VNU, model or DB calls."""

import copy
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect, sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.check_course_status import course
from tests.frontend.presentation_fixture import common_route


def main():
    evidence = Path('backups/recommendation_refinement_20261104/browser')
    evidence.mkdir(parents=True, exist_ok=True)
    auth = session_payload()
    group = {'id': 'ai-choice', 'name': 'Synthetic choice', 'required_credits': 3,
             'earned_credits': 0, 'remaining_credits': 3}
    rows = [course('B200', 'Môn bắt buộc minh họa', 3, requirement_type='required'),
            course('C300', 'Học máy minh họa', 3, requirement_type='elective', groups=[group]),
            course('D301', 'Môn tự chọn minh họa', 3, requirement_type='elective', groups=[group]),
            course('E400', '<img src=x onerror=alert(1)>', 4),
            course('F500', 'Môn nối tiếp không được lưu', 3, planning_eligible=False,
                   eligibility_basis='available_prerequisites'),
            course('G600', 'Môn nối tiếp học cùng kỳ', 3, requirement_type='required',
                   planning_eligible=True, eligibility_basis='available_prerequisites',
                   prerequisite_clauses=[['B200']])]
    metadata = {row['code']: {**row, 'prerequisites': [['A100']],
                'prerequisite_status': 'verified', 'source_status': 'verified'} for row in rows}
    metadata['G600']['prerequisites'] = [['B200']]
    metadata['A100'] = {**course('A100', 'Môn nền tảng đã hoàn thành', 3), 'prerequisites': []}
    source = {'subject': 'synthetic-only', 'profile': {'program': 'Chương trình minh họa', 'cohort': '68'},
              'snapshot': {'digest': 'synthetic-snapshot', 'completeness': 'complete', 'attempts': []}}
    plans, requests, errors, pending, rec_payloads = [], [], [], [], []
    mode = 'ready'
    save_mode = 'saved'
    enhance_mode = 'llm'
    required_track = required_path = True

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
            ready = ((not required_track or bool(query.get('selected_track_id')))
                     and (not required_path or bool(query.get('selected_graduation_path_id'))))
            route.fulfill(json={
                'status': 'ready' if ready else 'partial', 'can_plan': ready,
                'program_id': 'synthetic-program', 'program_name': 'Chương trình minh họa',
                'catalog_status': 'verified', 'context_revision': revision(query), 'plan_basis': 'a' * 64,
                'blocking_reasons': [] if ready else ['track_selection_required', 'graduation_selection_required'],
                'selections': {'track_required': required_track, 'path_required': required_path,
                    'tracks': [{'id': 'track-ai', 'name': 'Trí tuệ nhân tạo'}, {'id': 'track-software', 'name': 'Phần mềm'}],
                    'paths': [{'id': 'thesis', 'name': 'Khóa luận tốt nghiệp', 'allowed_track_ids': ['track-ai', 'track-software']},
                              {'id': 'courses', 'name': 'Học phần thay thế', 'allowed_track_ids': ['track-ai', 'track-software']}] if required_path else []},
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
            assert 'preference' not in payload
            assert payload['form_input']['values']['workload'] == 'moderate'
            assert payload['ranking_weights']['workload'] > 0
            assert 'passed_course_codes' not in payload and 'owner' not in payload
            assert isinstance(payload['include_narrative'], bool)
            rec_payloads.append(payload)
            if mode == 'clarification':
                route.fulfill(json={'context_revision': payload['expected_revision'], 'recommendations': [],
                    'intent': {'status': 'needs_clarification',
                               'questions': ['interest_topics: câu nhập bổ sung lựa chọn khác biểu mẫu; hãy xác nhận lại.']}})
                return
            if mode == 'pending':
                pending.append(route)
                return
            if mode == 'failed' or (mode == 'partial' and payload['ranking_weights']['topic'] > .4):
                route.fulfill(status=503, json={'detail': 'temporary_failure'})
                return
            if payload['include_narrative'] and enhance_mode == 'error':
                route.fulfill(status=503, json={'detail': 'narrative_temporarily_unavailable'})
                return
            weights = payload['ranking_weights']
            # In graduation variant, G600 (dependent on B200) deliberately precedes B200 to test order-independence.
            selected = ['G600', 'B200', 'E400'] if weights['course_type'] > .4 else ['C300', 'D301', 'F500'] if weights['topic'] > .4 else ['B200', 'C300', 'E400']
            strategy_label = 'Ưu tiên tốt nghiệp' if weights['course_type'] > .4 else 'Sát định hướng' if weights['topic'] > .4 else 'Cân bằng'
            if payload['include_narrative'] and enhance_mode == 'llm':
                plan_explanation = {
                    'headline': f'Phương án {strategy_label.lower()} với B200 và C300 <img src=x onerror=alert(1)>',
                    'bundle_rationale': 'Tổ hợp ưu tiên môn bắt buộc B200 cùng hướng Học máy để giữ cân bằng tiến độ.',
                    'highlights': [
                        'Ưu tiên hoàn thành B200 trước các học phần tiếp theo.',
                        'Giữ tổng tín chỉ ở mức hợp lý cho kỳ tới.',
                    ],
                    'caveats': ['Trạng thái mở lớp kỳ tới chưa được xác minh; hãy đối chiếu thời khóa biểu chính thức khi đăng ký.'],
                    'explanation_source': 'llm_grounded',
                }
            else:
                plan_explanation = {
                    'headline': f'Đề xuất {len(selected)} môn (10 TC) — {strategy_label}',
                    'bundle_rationale': f'Tổ hợp gồm {len(selected)} học phần với tổng 10 TC (mục tiêu 20 TC, biên ±2 TC) theo chiến lược {strategy_label}. Nội dung gắn với chủ đề: Học máy.',
                    'highlights': [
                        'Học lại điểm F: B200 được ưu tiên đưa vào kế hoạch kỳ này.',
                        'Cân đối tải học kỳ ở mức 10/20 TC (còn thiếu 117 TC theo CTĐT).',
                    ],
                    'caveats': ['Trạng thái mở lớp kỳ tới chưa được xác minh; hãy đối chiếu thời khóa biểu chính thức khi đăng ký.'],
                    'explanation_source': 'deterministic_fallback',
                }
            route.fulfill(json={'context_revision': payload['expected_revision'], 'catalog_status': 'verified',
                'recommendations': [{**next(row for row in rows if row['code'] == code),
                    'fit_probability': 0.42,
                    'eligibility_reason': (
                        ['Đủ điều kiện học cùng kỳ với học phần tiên quyết B200.']
                        if code == 'G600'
                        else ['Chưa hoàn thành môn này và đã thỏa các prerequisite trong catalog.']
                    ),
                    'transcript_signals': (
                        ['Học phần bắt buộc còn thiếu trong chương trình đào tạo.',
                         'Học song hành cùng học phần tiên quyết B200 trong học kỳ này.']
                        if code == 'G600'
                        else ['Học phần bắt buộc còn thiếu trong chương trình đào tạo.']
                    ),
                    'fit_reason': 'Phù hợp chủ đề bạn quan tâm: Học máy.',
                    'reason': (
                        'Đủ điều kiện: Đủ điều kiện học cùng kỳ với học phần tiên quyết B200. Phù hợp: Phù hợp chủ đề bạn quan tâm: Học máy. Tiến độ bảng điểm: Học song hành cùng học phần tiên quyết B200 trong học kỳ này.'
                        if code == 'G600'
                        else 'Đủ điều kiện: Chưa hoàn thành môn này và đã thỏa các prerequisite trong catalog. Phù hợp: Phù hợp chủ đề bạn quan tâm: Học máy. Tiến độ bảng điểm: Học phần bắt buộc còn thiếu trong chương trình đào tạo.'
                    )} for code in selected],
                'warnings': ['Lịch mở lớp chưa xác nhận.'],
                'plan_explanation': plan_explanation})
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
            if 'G600' in payload['course_codes'] and 'B200' not in payload['course_codes']:
                route.fulfill(status=409, json={'detail': 'semester_plan_course_unavailable'})
                return
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
        page.clock.set_fixed_time(datetime(2026, 11, 4, 1, tzinfo=timezone.utc))
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.route('**/*', intercept)
        page.goto('http://127.0.0.1:8000/#recommend')
        expect(page.locator('[data-rec-direction="track-ai"]')).to_be_visible()
        page.screenshot(path=str(evidence / 'landing-light-1440.png'), full_page=True)
        expect(page.locator('#rec-goal')).to_have_count(0)
        page.locator('[data-rec-direction="custom"]').click()
        expect(page.locator('#rec-custom-direction')).to_be_focused()
        expect(page.locator('#rec-goal')).to_have_count(0)
        page.locator('#rec-custom-direction').fill('An toàn thông tin')
        page.get_by_role('button', name='Dùng định hướng này', exact=True).click()
        expect(page.locator('#rec-custom-direction')).to_be_visible()  # Required curriculum track is still missing.
        page.locator('#rec-custom-track').select_option('track-ai')
        page.locator('#rec-custom-direction').fill('   ')
        page.get_by_role('button', name='Dùng định hướng này', exact=True).click()
        expect(page.locator('#rec-custom-direction')).to_be_visible()
        page.locator('#rec-custom-direction').fill('An toàn thông tin')
        page.get_by_role('button', name='Dùng định hướng này', exact=True).click()
        assert page.locator('.rec-flying-chip').count() == 1
        expect(page.locator('.rec-answer').first).to_contain_text('An toàn thông tin')
        expect(page.locator('#rec-goal')).to_have_count(0)
        expect(page.locator('#rec-credit-budget')).to_have_value('20')
        expect(page.locator('#rec-credit-budget')).to_have_attribute('min', '18')
        expect(page.locator('#rec-credit-budget')).to_have_attribute('max', '20')
        page.locator('#rec-credit-budget').fill('0')
        page.get_by_role('button', name='Đúng nhịp của mình', exact=True).click()
        expect(page.locator('#rec-credit-budget')).to_be_visible()
        page.locator('[data-rec-load="light"]').click()
        expect(page.locator('#rec-credit-budget')).to_have_value('17')
        expect(page.locator('#rec-credit-budget')).to_have_attribute('min', '14')
        expect(page.locator('#rec-credit-budget')).to_have_attribute('max', '17')
        slider = page.locator('.rec-budget input[type=range]')
        slider.focus()
        page.keyboard.press('Home')
        expect(page.locator('#rec-credit-budget')).to_have_value('14')
        page.locator('#rec-credit-budget').fill('13')
        page.get_by_role('button', name='Đúng nhịp của mình', exact=True).click()
        expect(page.locator('#rec-credit-budget')).to_be_visible()
        page.locator('[data-rec-load="heavy"]').click()
        expect(page.locator('#rec-credit-budget')).to_have_value('21')
        expect(page.locator('#rec-credit-budget')).to_have_attribute('min', '21')
        expect(page.locator('#rec-credit-budget')).to_have_attribute('max', '30')
        slider.focus()
        page.keyboard.press('End')
        expect(page.locator('#rec-credit-budget')).to_have_value('30')
        page.locator('[data-rec-load="moderate"]').click()
        expect(page.locator('#rec-credit-budget')).to_have_value('20')
        slider.focus()
        page.keyboard.press('Home')
        expect(page.locator('#rec-credit-budget')).to_have_value('18')
        slider.focus()
        page.keyboard.press('End')
        expect(page.locator('#rec-credit-budget')).to_have_value('20')
        page.screenshot(path=str(evidence / 'credit-ranges.png'))
        page.get_by_role('button', name='Đúng nhịp của mình', exact=True).click()
        expect(page.locator('#rec-goal')).to_have_count(0)
        assert page.locator('#rec-target-semester option').evaluate_all('nodes => nodes.map(node => node.value)') == ['1', '2']
        assert page.locator('#rec-target-year option').evaluate_all('nodes => nodes.map(node => node.value)') == ['2026', '2027', '2028']
        expect(page.locator('.rec-question')).to_contain_text('K68 vào học năm 2023')
        page.screenshot(path=str(evidence / 'cohort-window.png'))
        page.get_by_role('button', name='Ghi nhận mục tiêu', exact=True).click()
        expect(page.locator('#rec-goal')).to_have_count(0)
        page.locator('[data-rec-path="thesis"]').click()
        expect(page.locator('#rec-goal')).to_be_visible()
        assert plans == []
        expect(page.locator('#rec-include-narrative')).not_to_be_checked()
        page.locator('#rec-goal').fill('Mình muốn ưu tiên học máy.')
        page.locator('.rec-send').click()
        expect(page.locator('.rec-free-goal')).to_contain_text('ưu tiên học máy')
        page.locator('#rec-generate').click()
        expect(page.locator('#rec-save')).to_be_enabled(timeout=15000)
        assert page.locator('.rec-course').first.evaluate("element => element.getAnimations().some(animation => animation.playState === 'running')")
        assert len([item for item in requests if item == ('/me/recommendations', 'POST')]) == 3
        assert len(rec_payloads) == 3 and all(item['include_narrative'] is False for item in rec_payloads)
        expect(page.locator('.rec-course')).to_have_count(3)
        assert page.locator('.rec-course img').count() == 0
        assert '10 / 20 tín chỉ' in page.locator('.rec-plan-caption').inner_text()
        expect(page.locator('.rec-plan-explanation')).to_be_visible()
        expect(page.locator('.rec-plan-explanation')).to_have_attribute('data-explanation-source', 'deterministic_fallback')
        expect(page.locator('.rec-plan-source-badge')).to_contain_text('Tổng hợp từ dữ liệu chương trình')
        expect(page.locator('.rec-plan-headline')).to_contain_text('Đề xuất 3 môn (10 TC) — Cân bằng')
        expect(page.locator('#rec-enhance-explanation')).to_be_visible()
        enhance_mode = 'error'
        page.locator('#rec-enhance-explanation').click()
        expect(page.locator('.rec-plan-enhance-notice')).to_contain_text('Không kết nối được dịch vụ AI lúc này')
        expect(page.locator('.rec-course')).to_have_count(3)
        expect(page.locator('.rec-plan-explanation')).to_have_attribute('data-explanation-source', 'deterministic_fallback')
        enhance_mode = 'llm'
        page.locator('#rec-enhance-explanation').click()
        expect(page.locator('.rec-plan-explanation')).to_have_attribute('data-explanation-source', 'llm_grounded')
        expect(page.locator('.rec-plan-explanation.is-llm')).to_be_visible()
        expect(page.locator('.rec-plan-source-badge')).to_contain_text('Tổng hợp AI · bám sát dữ liệu')
        expect(page.locator('.rec-plan-headline')).to_contain_text('Phương án cân bằng với B200 và C300')
        expect(page.locator('#rec-enhance-explanation')).to_have_count(0)
        expect(page.locator('.rec-plan-enhance-notice')).to_have_count(0)
        assert page.locator('.rec-plan-explanation img').count() == 0
        expect(page.locator('.rec-algorithm-guide')).to_be_visible()
        page.locator('.rec-algorithm-guide > summary').click()
        expect(page.locator('.rec-algorithm-steps li')).to_have_count(4)
        expect(page.locator('.rec-algorithm-guide')).to_contain_text('T ± 2 TC')
        page.screenshot(path=str(evidence / 'results-light-1440.png'), full_page=True)
        page.locator('.rec-course').first.get_by_role('button', name='Vì sao môn này?', exact=True).click()
        expect(page.locator('.rec-dialog')).to_be_visible()
        dialog_text = page.locator('.rec-dialog').inner_text()
        assert 'A100: Môn nền tảng đã hoàn thành' in dialog_text
        assert dialog_text.count('Phù hợp chủ đề bạn quan tâm: Học máy.') == 1
        assert dialog_text.count('Học phần bắt buộc còn thiếu trong chương trình đào tạo.') == 1
        page.keyboard.press('Escape')
        expect(page.locator('.rec-dialog')).not_to_be_visible()
        page.locator('[data-rec-variant="direction"]').click()
        expect(page.locator('.rec-course')).to_have_count(1)
        assert 'C300' in page.locator('.rec-course').inner_text()
        expect(page.locator('.rec-plan-explanation')).to_have_attribute('data-explanation-source', 'deterministic_fallback')
        expect(page.locator('#rec-enhance-explanation')).to_be_visible()
        page.locator('#rec-compare').click()
        expect(page.locator('.rec-compare-dialog table')).to_be_visible()
        assert 'E400' in page.locator('.rec-compare-dialog table').inner_text()
        page.keyboard.press('Escape')
        page.locator('[data-rec-variant="balanced"]').click()
        expect(page.locator('.rec-plan-explanation')).to_have_attribute('data-explanation-source', 'llm_grounded')
        # Co-enrolled bundle (G600 + B200 + E400) where dependent G600 precedes B200:
        page.locator('[data-rec-variant="graduation"]').click()
        expect(page.locator('.rec-course')).to_have_count(3)
        assert page.locator('[data-rec-course]').nth(0).get_attribute('data-rec-course') == 'G600'
        page.locator('[data-rec-course="G600"]').get_by_role('button', name='Vì sao môn này?', exact=True).click()
        expect(page.locator('.rec-dialog')).to_contain_text('Đủ điều kiện học cùng kỳ với học phần tiên quyết B200.')
        expect(page.locator('.rec-dialog')).to_contain_text('B200: Môn bắt buộc minh họa (học cùng kỳ)')
        page.keyboard.press('Escape')
        page.get_by_role('button', name='Chỉnh sửa phương án', exact=True).click()
        expect(page.locator('#academic-plan-tools')).to_have_attribute('open', '')
        expect(page.locator('#semester-plans [data-plan-course="G600"]')).to_be_visible()
        assert 'Cần kiểm tra' not in page.locator('#semester-plans [data-plan-course="G600"]').inner_text()
        page.locator('#semester-plans [data-plan-course="B200"] button').click()
        expect(page.locator('#semester-plans [data-plan-course="G600"]')).to_contain_text('Cần kiểm tra')
        page.locator('#semester-plan-form button[type=submit]').click()
        expect(page.locator('#semester-plans')).to_contain_text('Có môn không còn đủ điều kiện')
        page.locator('[data-rec-variant="graduation"]').click()
        save_mode = 'saved'
        page.locator('#rec-save').click()
        page.get_by_role('button', name='Xác nhận lưu', exact=True).click()
        expect(page.locator('.rec-save-success')).to_contain_text('Đã lưu phương án')
        assert set(plans[-1]['course_codes']) == {'G600', 'B200', 'E400'}
        page.keyboard.press('Escape')
        plans.clear()
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
        expect(page.get_by_role('heading', name='Next-term suggestions', exact=True)).to_be_visible()
        expect(page.locator('.rec-algorithm-guide')).to_contain_text('How course recommendations work')
        expect(page.locator('.rec-plan-source-badge')).to_contain_text('AI summary · data-grounded (VI)')
        expect(page.locator('.rec-plan-headline')).to_contain_text('Phương án cân bằng với B200 và C300')
        expect(page.locator('.rec-plan-caveats')).to_contain_text('Next-term course offerings are not verified; check the official timetable when registering.')
        expect(page.locator('.rec-course-reason').first).to_contain_text('Matches your focus topics: Machine Learning.')
        page.locator('.rec-course').first.get_by_role('button', name='Why this course?', exact=True).click()
        expect(page.locator('.rec-dialog')).to_contain_text('Goal alignment:')
        expect(page.locator('.rec-dialog')).to_contain_text('Remaining required course in your curriculum.')
        page.keyboard.press('Escape')
        page.locator('[data-rec-variant="graduation"]').click()
        page.locator('[data-rec-course="G600"]').get_by_role('button', name='Why this course?', exact=True).click()
        expect(page.locator('.rec-dialog')).to_contain_text('Eligible to co-enroll in the same term with prerequisite(s) B200.')
        expect(page.locator('.rec-dialog')).to_contain_text('Co-enrolled in the same term alongside prerequisite(s) B200.')
        expect(page.locator('.rec-dialog')).to_contain_text('(co-enrolled)')
        page.keyboard.press('Escape')
        page.emulate_media(reduced_motion='reduce')
        page.locator('[data-rec-variant="direction"]').click()
        expect(page.locator('.rec-plan-source-badge')).to_contain_text('Curriculum & transcript summary')
        expect(page.locator('.rec-plan-headline')).to_contain_text('Suggested 3 courses (10 cr) — Interest focus')
        expect(page.locator('.rec-plan-rationale')).to_contain_text('Bundle of 3 courses totaling 10 cr (target 20 cr, ±2 cr band) under the Interest focus strategy.')
        expect(page.locator('.rec-plan-highlights')).to_contain_text('F-grade retake: B200 prioritized in this term plan.')
        assert page.locator('.rec-flying-chip').count() == 0
        page.locator('[data-language-choice=vi]').click()
        page.set_viewport_size({'width': 1440, 'height': 1000})
        page.locator('[data-rec-variant="balanced"]').click()
        rec_payloads.clear()
        page.locator('#rec-include-narrative').check()
        page.locator('#rec-generate').click()
        expect(page.locator('.rec-plan-explanation.is-llm')).to_be_visible(timeout=15000)
        assert len(rec_payloads) == 3
        assert sum(1 for item in rec_payloads if item['include_narrative']) == 1
        page.locator('#rec-include-narrative').uncheck()
        # A cohort refresh in the same session must invalidate the old graduation goal.
        page.evaluate("""() => {
          const value = window.workspacePlanning.snapshot(); value.profile.cohort = '69';
          document.dispatchEvent(new CustomEvent('workspace:planning-state', {detail: value}));
        }""")
        expect(page.locator('#rec-goal')).to_have_count(0)
        expect(page.locator('#rec-target-year option')).to_have_count(4)
        assert page.locator('#rec-target-year option').last.get_attribute('value') == '2029'
        page.evaluate("""() => {
          const value = window.workspacePlanning.snapshot(); value.profile.cohort = '68';
          document.dispatchEvent(new CustomEvent('workspace:planning-state', {detail: value}));
        }""")
        page.get_by_role('button', name='Ghi nhận mục tiêu', exact=True).click()
        expect(page.locator('#rec-goal')).to_be_visible()
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
        mode = 'clarification'
        page.locator('#rec-generate').click()
        expect(page.locator('#rec-plan-content .rec-error')).to_contain_text('Chủ đề quan tâm: câu nhập bổ sung lựa chọn khác biểu mẫu; hãy xác nhận lại.')
        expect(page.locator('#rec-plan-content .rec-error')).to_contain_text('Gợi ý:')
        expect(page.locator('#rec-roadmap')).to_contain_text('Cần xem thông báo bên dưới')
        assert page.evaluate("Boolean(document.getElementById('rec-results').compareDocumentPosition(document.querySelector('.rec-algorithm-guide')) & Node.DOCUMENT_POSITION_FOLLOWING)")
        assert page.locator('.rec-course').count() == 0
        assert not page.locator('#rec-save').count() or not page.locator('#rec-save').is_enabled()
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
        # Ordinary curricula have exactly the three requested intake stages.
        mode = 'ready'
        required_track = required_path = False
        page.reload()
        expect(page.locator('[data-rec-direction="custom"]')).to_be_visible()
        expect(page.locator('[data-rec-direction]')).to_have_count(4)
        expect(page.locator('#rec-goal')).to_have_count(0)
        page.locator('[data-rec-direction="custom"]').click()
        expect(page.locator('#rec-custom-track')).to_have_count(0)
        page.locator('#rec-custom-direction').fill('Thiết kế sản phẩm số')
        page.get_by_role('button', name='Dùng định hướng này', exact=True).click()
        expect(page.locator('#rec-goal')).to_have_count(0)
        page.get_by_role('button', name='Đúng nhịp của mình', exact=True).click()
        expect(page.locator('#rec-goal')).to_have_count(0)
        page.get_by_role('button', name='Ghi nhận mục tiêu', exact=True).click()
        expect(page.locator('#rec-goal')).to_be_visible()
        expect(page.locator('.rec-step-dot')).to_have_count(3)
        page.screenshot(path=str(evidence / 'final-chat-three-stages.png'), full_page=True)
        page.locator('#rec-roadmap [data-rec-answer="direction"]').click()
        page.locator('#rec-custom-direction').fill('A' * 120)
        page.get_by_role('button', name='Dùng định hướng này', exact=True).click()
        page.set_viewport_size({'width': 390, 'height': 1000})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.locator('.rec-mobile-roadmap').click()
        expect(page.locator('.rec-roadmap-sheet')).to_be_visible()
        assert page.locator('.rec-roadmap-sheet').evaluate('element => element.scrollWidth <= element.clientWidth')
        page.keyboard.press('Escape')
        source['profile']['cohort'] = ''
        page.reload()
        page.locator('[data-rec-direction="ai"]').click()
        page.get_by_role('button', name='Đúng nhịp của mình', exact=True).click()
        expect(page.get_by_role('button', name='Ghi nhận mục tiêu', exact=True)).to_be_disabled()
        expect(page.locator('.rec-question')).to_contain_text('Chưa đọc được khóa tuyển sinh')
        expect(page.locator('#rec-goal')).to_have_count(0)
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
