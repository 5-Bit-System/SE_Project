"""Program menu uses the ordinary API without course or generated consent."""

from playwright.sync_api import expect

from tests.hus.test_question_catalog_ui import browser_app as browser_app
from tests.hus.test_question_catalog_ui import click_and_answer
from tests.hus.test_question_catalog_ui import page as page


def test_program_menu_and_group_notes_match_api(page):
    f2 = page.locator('[data-family="f2"]')
    f2.locator('summary').first.click()
    section = f2.locator('.rag-catalog-section').first
    section.locator('summary').click()
    payload, response = click_and_answer(page, section.get_by_role(
        'button', name='Chương trình đào tạo yêu cầu tổng cộng bao nhiêu tín chỉ?', exact=True))
    assert 'course_code' not in payload and payload['allow_generated_reference'] is False
    assert response['hus_answer']['facts']['value'] == {'credits_required': 127}
    expect(page.locator('#rag-generated')).not_to_be_checked()
    _, response = click_and_answer(page, section.get_by_role(
        'button', name='Nhóm II có yêu cầu, tín chỉ liệt kê và ghi chú gì?', exact=True))
    answer = response['hus_answer']
    assert answer['facts']['value']['min_credits_if_selected'] == 5
    assert answer['facts']['value']['offered_credits'] == 13
    link = page.locator('.rag-message-assistant').last.locator('.rag-citations a').first
    expect(link).to_have_attribute('href', answer['citations'][0]['open_url'])
    expect(page.locator('#rag-single-turn')).to_contain_text('chương trình')


def test_program_menu_changes_scope_and_resets_ai(page):
    page.locator('#rag-generated').check()
    page.locator('#rag-major').select_option('mathematics')
    expect(page.locator('#rag-generated')).not_to_be_checked()
    expect(page.locator('#rag-catalog-status')).to_contain_text('câu hỏi')
    page.locator('[data-family="f2"] summary').first.click()
    section = page.locator('[data-family="f2"] .rag-catalog-section').first
    section.locator('summary').click()
    payload, response = click_and_answer(page, section.get_by_role(
        'button', name='Chương trình đào tạo yêu cầu tổng cộng bao nhiêu tín chỉ?', exact=True))
    assert payload['version'] == 'QD3565-2023' and payload['major'] == 'mathematics'
    assert response['hus_answer']['facts']['value'] == {'credits_required': 135}
