"""Exercise real browser form POST evidence against intercepted synthetic portal pages."""

from urllib.parse import parse_qs

from playwright.sync_api import TimeoutError, sync_playwright

from app.integrations.daotao.client import LOGIN_URL, DaotaoClient
from app.integrations.daotao.snapshot import PortalFailure, verified_subject

FORM = '''<form id="frmLogin" method="post" action="login.asp">
<input id="txtLoginId" name="txtLoginId"><input id="txtPassword" name="txtPassword">
<input type="submit"></form>'''
MENU = '<a id="PortalModule_374" title="Xem điểm sinh viên">Xem điểm</a>'


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True,
                                    proxy={"server": "http://127.0.0.1:9"})
        try:
            for scenario in ("valid", "invalid", "http_rejected", "preauthenticated",
                             "existing_cookie", "foreign_form", "captcha", "otp",
                             "post_captcha", "hidden_captcha"):
                context = browser.new_context()
                submitted = []

                def route_request(route):
                    request = route.request
                    if request.url != LOGIN_URL:
                        route.abort()
                    elif request.method == "POST":
                        submitted.append(parse_qs(request.post_data))
                        content = MENU if scenario in {"valid", "http_rejected", "hidden_captcha"} else FORM
                        if scenario == "post_captcha":
                            content += '<input name="captcha">'
                        route.fulfill(status=401 if scenario == "http_rejected" else 200,
                                      content_type="text/html; charset=utf-8", body=content)
                    else:
                        content = MENU + FORM if scenario == "preauthenticated" else FORM
                        if scenario == "foreign_form":
                            content = content.replace('action="login.asp"',
                                                      'action="https://other.invalid/login"')
                        if scenario == "captcha":
                            content += '<input name="captcha">'
                        elif scenario == "otp":
                            content += '<input autocomplete="one-time-code">'
                        elif scenario == "hidden_captcha":
                            content += '<input name="captcha" hidden>'
                        route.fulfill(content_type="text/html; charset=utf-8", body=content)

                context.route("**/*", route_request)
                if scenario == "existing_cookie":
                    context.add_cookies([{"name": "synthetic", "value": "only",
                                          "url": LOGIN_URL}])
                client = DaotaoClient(context)
                try:
                    subject = client.login("synthetic001", "synthetic-password", timeout_ms=500)
                    assert scenario in {"valid", "hidden_captcha"}, scenario
                    assert verified_subject("No student label", "synthetic001",
                                            authenticated_subject=subject) == "synthetic001"
                    assert submitted[0]["txtLoginId"] == ["synthetic001"]
                except PortalFailure as exc:
                    assert scenario not in {"valid", "hidden_captcha"}, scenario
                    if scenario in {"captcha", "otp", "post_captcha"}:
                        assert str(exc) == "interaction_required"
                    if scenario in {"captcha", "otp"}:
                        assert not submitted, "Do not submit credentials through a challenge"
                except TimeoutError:
                    assert scenario == "invalid", scenario
                finally:
                    context.close()
        finally:
            browser.close()
    print("Portal auth: accepted fresh POST; rejected bad login/status, old cookies/menu, foreign form")


if __name__ == "__main__":
    main()
