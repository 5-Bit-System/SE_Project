"""Test chat history persistence across F5 page reload and New Chat button."""

import json
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import expect, sync_playwright

from tests.frontend.auth_fixture import session_payload
from tests.frontend.presentation_fixture import common_route


def test_lookup_history_persists_across_f5_reload():
    # In-memory mock store for server chat history to test full lifecycle
    server_history = {}

    sample = {
        "subject": "synthetic-only",
        "fetched_at": "2026-10-23T00:00:00+00:00",
        "profile": {"program": "Khoa học dữ liệu", "cohort": "68"},
        "snapshot": {"source_summary": [["Tổng tín chỉ: 6"]], "unknown_rows": [], "attempts": []},
    }

    def intercept(route):
        url = route.request.url
        path = urlsplit(url).path
        if path == '/auth/session':
            route.fulfill(json=session_payload())
        elif path.startswith('/me/'):
            route.fulfill(json=sample)
        elif path == '/hus/chat/history':
            qs = parse_qs(urlsplit(url).query)
            major = qs.get('major', ['data_science'])[0]
            if route.request.method == 'DELETE':
                server_history[major] = []
                route.fulfill(json={'status': 'cleared'})
            elif route.request.method == 'POST':
                data = json.loads(route.request.post_data)
                server_history.setdefault(major, []).append(data)
                route.fulfill(json={'status': 'saved', 'count': len(server_history[major])})
            else:
                route.fulfill(json={
                    'account_id': 'synthetic-student',
                    'major': major,
                    'messages': server_history.get(major, []),
                })
        elif path == '/hus/chat':
            route.fulfill(json={
                'mode': 'hus_rag',
                'reply': '### Thông tin học phần\n- **Mã học phần:** MAT2400 [1]\n- **Tên:** Giải tích 1',
                'generation_mode': 'grounded_llm',
                'hus_answer': {
                    'status': 'answered',
                    'citations': [{'citation_id': 1, 'label': 'QĐ 3569', 'evidence_kind': 'pdf', 'availability': 'available', 'open_url': '/hus/sources/b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2?page=10#page=10', 'document_sha256': 'b4b0289701a6c1e2b7d288ea880970a2a9f49d680dc6c3986d9b840d93083ab2', 'pdf_page': 10}],
                },
            })
        else:
            assert common_route(route), url

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.route("**/*", intercept)

        # 1. Open workspace with hash #lookup
        page.goto("http://127.0.0.1:8000/#lookup", wait_until="networkidle")

        # 2. Wait for lookup tab and major selector to be ready
        expect(page.locator("#lookup-major")).to_be_visible()
        expect(page.locator("#lookup-question")).to_be_visible()

        # Initial message count is 1 (the welcome assistant message)
        expect(page.locator(".rag-message")).to_have_count(1)
        expect(page.locator(".rag-message-assistant").first).to_contain_text("Xin chào!")

        # 3. Ask question
        page.locator("#lookup-question").fill("giải tích 1 học gì?")
        with page.expect_response(lambda r: "/hus/chat" in r.url):
            page.locator("#lookup-send").click()

        # Messages should now have: 1 welcome, 1 user question, 1 assistant answer = 3 messages
        expect(page.locator(".rag-message")).to_have_count(3)
        expect(page.locator(".rag-message-user")).to_contain_text("giải tích 1 học gì?")
        expect(page.locator(".rag-message-assistant").last).to_contain_text("Thông tin học phần")

        # 4. Trigger F5 Reload
        page.reload(wait_until="networkidle")

        # Navigate / verify #tab-lookup active
        page.locator("#tab-btn-lookup").click()
        expect(page.locator("#tab-lookup")).to_be_visible()

        # 5. VERIFY PERSISTENCE ACROSS F5:
        # User message and assistant answer are STILL in #lookup-messages!
        expect(page.locator(".rag-message-user")).to_contain_text("giải tích 1 học gì?")
        expect(page.locator(".rag-message-assistant").last).to_contain_text("Thông tin học phần")
        expect(page.locator(".rag-course-card")).to_be_visible()

        # 6. Click "+ Đoạn chat mới" button
        expect(page.locator("#lookup-new-chat")).to_be_visible()
        page.locator("#lookup-new-chat").click()

        # Conversation is reset: only 1 welcome message remains
        expect(page.locator(".rag-message")).to_have_count(1)
        expect(page.locator(".rag-message-user")).to_have_count(0)
        expect(page.locator(".rag-message-assistant").first).to_contain_text("Xin chào!")

        browser.close()


def test_lookup_history_isolated_between_accounts():
    """Verify that User B does not see User A's chat history."""
    server_histories = {}
    current_account = ["student-user-A"]

    def intercept(route):
        url = route.request.url
        path = urlsplit(url).path
        if path == '/auth/session':
            route.fulfill(json={
                'authenticated': True,
                'account': {
                    'account_id': current_account[0],
                    'vnu_subject': current_account[0],
                    'role': 'student',
                    'display_name': f'Student {current_account[0]}',
                },
                'csrf_token': 'fake-csrf-token',
            })
        elif path.startswith('/me/'):
            route.fulfill(json={
                "subject": current_account[0],
                "fetched_at": "2026-10-23T00:00:00+00:00",
                "profile": {"program": "Khoa học dữ liệu", "cohort": "68"},
                "snapshot": {"source_summary": [], "unknown_rows": [], "attempts": []},
            })
        elif path == '/hus/chat/history':
            qs = parse_qs(urlsplit(url).query)
            major = qs.get('major', ['data_science'])[0]
            acc_id = current_account[0]
            user_store = server_histories.setdefault(acc_id, {})
            if route.request.method == 'DELETE':
                user_store[major] = []
                route.fulfill(json={'status': 'cleared'})
            elif route.request.method == 'POST':
                data = json.loads(route.request.post_data)
                user_store.setdefault(major, []).append(data)
                route.fulfill(json={'status': 'saved', 'count': len(user_store[major])})
            else:
                route.fulfill(json={
                    'account_id': acc_id,
                    'major': major,
                    'messages': user_store.get(major, []),
                })
        elif path == '/hus/chat':
            route.fulfill(json={
                'mode': 'basic_chat',
                'reply': f'Trả lời cho {current_account[0]}',
                'hus_answer': None,
            })
        else:
            assert common_route(route), url

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.route("**/*", intercept)

        # 1. Login as User A and chat
        current_account[0] = "student-user-A"
        page.goto("http://127.0.0.1:8000/#lookup", wait_until="networkidle")

        page.locator("#lookup-question").fill("Câu hỏi bí mật của User A")
        with page.expect_response(lambda r: "/hus/chat" in r.url):
            page.locator("#lookup-send").click()

        expect(page.locator(".rag-message-user")).to_contain_text("Câu hỏi bí mật của User A")

        # 2. Switch session to User B and reload
        current_account[0] = "student-user-B"
        page.reload(wait_until="networkidle")
        page.locator("#tab-btn-lookup").click()

        # User B should NOT see User A's question!
        expect(page.locator(".rag-message-user")).to_have_count(0)
        expect(page.locator("#lookup-messages")).not_to_contain_text("Câu hỏi bí mật của User A")
        expect(page.locator(".rag-message-assistant").first).to_contain_text("Xin chào!")

        # 3. Switch back to User A
        current_account[0] = "student-user-A"
        page.reload(wait_until="networkidle")
        page.locator("#tab-btn-lookup").click()

        # User A's question is STILL there!
        expect(page.locator(".rag-message-user")).to_contain_text("Câu hỏi bí mật của User A")

        browser.close()
