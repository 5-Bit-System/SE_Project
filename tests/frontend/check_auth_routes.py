"""Browser regression for role-specific workspace and admin hash routes."""

import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

STATIC = Path(__file__).resolve().parents[2] / "app" / "static"
EVIDENCE = Path("backups/admin_hash_routes_20261105")


class StaticHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path == "/":
            return str(STATIC / "index.html")
        if path.startswith("/static/"):
            return str(STATIC / path.removeprefix("/static/"))
        return str(STATIC / "missing")

    def log_message(self, *_):
        pass


def stub_session(page, role):
    def reply(route):
        path = route.request.url.split(":", 2)[-1].split("/", 1)[-1]
        if path.startswith("auth/session"):
            result = {"authenticated": True, "csrf_token": "synthetic", "account": {
                "account_id": f"synthetic-{role}", "session_id": f"session-{role}",
                "role": role, "email": "admin@example.test" if role == "admin" else None,
                "vnu_subject": "synthetic-student" if role == "student" else None,
                "display_name": "Synthetic", "must_change_password": False,
                "expires_in": 1800}}
        elif path.startswith("admin/users?"):
            result = {"items": [], "total": 0}
        else:
            result = {}
        route.fulfill(status=200, content_type="application/json", body=json.dumps(result))

    page.route("**/auth/session", reply)
    page.route("**/admin/**", reply)


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(StaticHandler))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            root = f"http://127.0.0.1:{server.server_port}/"

            admin = browser.new_page()
            stub_session(admin, "admin")
            admin.goto(root + "#dashboard")
            admin.wait_for_function("document.body.dataset.authState === 'admin'")
            assert admin.evaluate("location.hash") == "#admin/overview"
            admin.locator("#admin-tab-users").click()
            assert admin.evaluate("location.hash") == "#admin/users"
            admin.reload()
            admin.wait_for_function("document.body.dataset.authState === 'admin'")
            assert admin.locator("#admin-tab-users").get_attribute("aria-selected") == "true"
            admin.locator("#admin-tab-curriculum").click()
            assert admin.evaluate("location.hash") == "#admin/curriculum"
            admin.go_back()
            assert admin.evaluate("location.hash") == "#admin/users"
            assert admin.locator("#admin-tab-users").get_attribute("aria-selected") == "true"
            admin.go_forward()
            assert admin.locator("#admin-tab-curriculum").get_attribute("aria-selected") == "true"
            admin.goto(root + "#admin/audit")
            admin.wait_for_function("document.body.dataset.authState === 'admin'")
            assert admin.evaluate("location.hash") == "#admin/audit"
            assert admin.locator("#admin-tab-audit").get_attribute("aria-selected") == "true"
            for tab in ("overview", "crawler", "announcements", "users", "curriculum", "audit"):
                admin.locator(f"#admin-tab-{tab}").click()
                assert admin.evaluate("location.hash") == f"#admin/{tab}"
                assert admin.locator(f"#admin-tab-{tab}").get_attribute("aria-selected") == "true"
            admin.locator("#admin-tab-overview").click()
            admin.locator('.admin-dashboard-nav a[href="#admin-dashboard-feedback"]').click()
            assert admin.evaluate("location.hash") == "#admin-dashboard-feedback"
            assert admin.locator("#admin-tab-overview").get_attribute("aria-selected") == "true"
            admin.reload()
            admin.wait_for_function("document.body.dataset.authState === 'admin'")
            assert admin.evaluate("location.hash") == "#admin/overview"
            admin.screenshot(path=str(EVIDENCE / "admin-overview-feedback.png"))

            student = browser.new_page()
            stub_session(student, "student")
            student.goto(root + "#admin/users")
            student.wait_for_function("document.body.dataset.authState === 'workspace'")
            assert student.evaluate("location.hash") == "#dashboard"
            assert student.locator("#system-admin").is_hidden()
            student.goto(root + "#admin-dashboard-feedback")
            student.wait_for_function("document.body.dataset.authState === 'workspace'")
            assert student.evaluate("location.hash") == "#dashboard"
            student.locator('[data-tab="portal-dialog"]').click()
            assert student.evaluate("location.hash") == "#profile"
            student.screenshot(path=str(EVIDENCE / "student-profile.png"))
            browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
