"""Exercise the real admin HTML and account detail interaction with synthetic API data."""

import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

STATIC = Path(__file__).resolve().parents[2] / "app" / "static"
EVIDENCE = Path("backups/admin_account_detail_20261105")
ACCOUNT_ID = "00000000-0000-4000-8000-000000000123"


class StaticHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path == "/":
            return str(STATIC / "index.html")
        if path.startswith("/static/"):
            return str(STATIC / path.removeprefix("/static/"))
        return str(STATIC / "missing")

    def log_message(self, *_):
        pass


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(StaticHandler))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            state = {"detail_error": False}

            def reply(route):
                path = route.request.url.split(":", 2)[-1].split("/", 1)[-1]
                if path.startswith("auth/session"):
                    payload = {"authenticated": True, "csrf_token": "synthetic", "account": {
                        "account_id": "00000000-0000-4000-8000-000000000001",
                        "session_id": "00000000-0000-4000-8000-000000000002",
                        "email": "admin@example.test", "display_name": "Admin", "role": "admin",
                        "must_change_password": False, "expires_in": 1800}}
                elif path.startswith("admin/users/"):
                    if state["detail_error"]:
                        route.fulfill(status=503, content_type="application/json",
                                      body=json.dumps({"detail": "storage_unavailable"}))
                        return
                    payload = {"account": {"id": ACCOUNT_ID, "vnu_subject": "synthetic-student",
                        "email": "student@example.test", "display_name": "Synthetic Student", "role": "student",
                        "profile_name": "Student from VNU", "profile_program": "Computer science",
                        "profile_cohort": "K68", "last_login_at": "2026-11-05T01:00:00Z",
                        "last_logout_at": "2026-11-05T03:00:00Z",
                        "is_active": True, "created_at": "2026-11-05T00:00:00Z"},
                        "events": [{"kind": "login_vnu", "created_at": "2026-11-05T01:00:00Z"},
                                   {"kind": "advisor", "created_at": "2026-11-05T02:00:00Z"},
                                   {"kind": "logout", "created_at": "2026-11-05T03:00:00Z"}]}
                elif path.startswith("admin/users?"):
                    payload = {"items": [{"id": ACCOUNT_ID, "vnu_subject": "synthetic-student",
                        "email": None, "display_name": "Synthetic Student", "role": "student",
                        "is_active": True, "email_verified_at": None}], "total": 1}
                else:
                    payload = {}
                route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

            page.route("**/auth/**", reply)
            page.route("**/admin/**", reply)
            page.goto(f"http://127.0.0.1:{server.server_port}/")
            page.locator("#admin-tab-users").click()
            account_link = page.get_by_role("button", name="Xem thông tin và lịch sử của synthetic-student")
            account_link.click()
            dialog = page.locator("#admin-user-detail-modal")
            assert dialog.is_visible()
            assert "Student from VNU" in dialog.inner_text()
            assert "Computer science" in dialog.inner_text()
            assert "K68" in dialog.inner_text()
            assert "student@example.test" in dialog.inner_text()
            assert "Đăng nhập gần nhất" in dialog.inner_text()
            assert "Đăng xuất gần nhất" in dialog.inner_text()
            assert "Đăng nhập VNU" in dialog.inner_text()
            assert "Đăng xuất" in dialog.inner_text()
            assert "Hỏi đáp" in dialog.inner_text()
            page.screenshot(path=str(EVIDENCE / "desktop.png"))
            page.set_viewport_size({"width": 390, "height": 844})
            box = dialog.bounding_box()
            assert box and box["x"] >= 0 and box["x"] + box["width"] <= 390
            page.screenshot(path=str(EVIDENCE / "mobile.png"))
            dialog.evaluate("element => element.scrollTop = element.scrollHeight")
            assert page.locator("#admin-user-history-note").is_visible()
            page.screenshot(path=str(EVIDENCE / "mobile-history.png"))
            page.keyboard.press("Escape")
            assert not dialog.is_visible()
            assert account_link.evaluate("element => element === document.activeElement")
            account_link.click()
            assert dialog.is_visible()
            page.evaluate("window.systemAuth.switchAdminTab('audit')")
            assert not dialog.is_visible()
            assert page.locator('#admin-user-detail-profile').inner_text() == ''
            page.evaluate("window.systemAuth.switchAdminTab('users')")
            state["detail_error"] = True
            account_link.click()
            assert "Không tải được thông tin tài khoản" in dialog.inner_text()
            page.evaluate("window.systemAuth.expire()")
            assert not dialog.is_visible()
            assert "Synthetic Student" not in dialog.inner_text()
            browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
