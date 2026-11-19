"""Browser checks of answer versus clarification/missing-source feedback."""

from playwright.sync_api import expect

from tests.hus.test_question_catalog_ui import browser_app as browser_app
from tests.hus.test_question_catalog_ui import page as page
from tools.run_hus_rag_demo import check_displayed_reply


def send(page, question):
    page.locator('#rag-question').fill(question)
    with page.expect_response(lambda r: r.url.endswith('/hus/chat')) as event:
        page.locator('#rag-send').click()
    response = event.value.json()
    check_displayed_reply(page, response)
    return response


def test_unknown_is_visible_and_still_has_a_source(page):
    answer = send(page, 'Tiên quyết MAT2400?')['hus_answer']
    assert answer['facts']['value'] == [None]
    assert answer['facts']['prerequisite_status'] == 'unknown'
    expect(page.locator('#rag-status')).to_contain_text('chưa rõ')
    message = page.locator('.rag-message-assistant').last
    expect(message).to_contain_text('không có tiên quyết')
    link = message.locator('.rag-citations a').first
    expect(link).to_be_visible()
    source = page.request.get(link.get_attribute('href'))
    assert source.ok and source.headers['content-type'] == 'application/pdf'


def test_multifield_and_followup_show_clarification_without_citations(page):
    send(page, 'Số tín chỉ MAT3533?')
    for question in ['MAT3533 có tên gì, bao nhiêu tín chỉ và tiên quyết gì?', 'Môn đó có bao nhiêu tín chỉ?']:
        answer = send(page, question)['hus_answer']
        assert answer['status'] == 'needs_clarification'
        expect(page.locator('#rag-status')).to_contain_text('làm rõ')
        if answer['diagnostic']['code'] == 'unsupported_operation':
            expect(page.locator('#rag-status')).to_contain_text('Yêu cầu này chưa được triển khai')
        expect(page.locator('.rag-message-assistant').last.locator('.rag-citations a')).to_have_count(0)
    expect(page.locator('#rag-question')).to_have_attribute('aria-describedby', 'rag-single-turn')


def test_no_information_and_basic_reply_have_correct_status(page):
    answer = send(page, 'Số tín chỉ MAT9999?')['hus_answer']
    assert answer['status'] == 'no_information'
    expect(page.locator('.rag-message-assistant').last.locator('.rag-citations')).to_have_count(0)
    expect(page.locator('#rag-status')).to_contain_text('Chưa có thông tin')
    expect(page.locator('#rag-status')).to_contain_text('Dữ liệu hiện có chưa cung cấp thông tin cần hỏi')
    assert send(page, 'Xin chào')['mode'] == 'basic_chat'
    expect(page.locator('#rag-status')).to_contain_text('hội thoại')


def test_credits_show_the_fact_and_one_source_without_review_boilerplate(page):
    page.locator('#rag-major').select_option('computer_science')
    answer = send(page, 'MAT3562E có bao nhiêu tín chỉ?')['hus_answer']
    assert answer['facts']['value'] == 3
    message = page.locator('.rag-message-assistant').last
    expect(message.locator('.rag-message-text')).to_contain_text('Số tín chỉ: 3')
    expect(message).not_to_contain_text('verified theo sign-off')
    expect(message.locator('.rag-citations a')).to_have_count(1)
    expect(message.locator('.rag-citations')).to_contain_text('Trang 12')
