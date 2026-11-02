"""Exercise the production worker with fresh Chrome instances and synthetic VNU pages."""

from unittest.mock import patch

from playwright.sync_api import BrowserContext

from app.integrations.daotao.client import LOGIN_URL, PROFILE_URL
from app.integrations.daotao.worker import collect

FORM = '''<form id="frmLogin" method="post" action="login.asp">
<input id="txtLoginId" name="txtLoginId"><input id="txtPassword" name="txtPassword">
<input type="submit"></form>'''
LANDING = '''<a id="PortalModule_374" title="Xem điểm sinh viên"
onclick="document.getElementById('divList3').hidden=false">Xem điểm</a>
<p>MSSV: synthetic001</p><p>Họ và tên: Synthetic student</p>
<div id="divList3" hidden><table><tr><td title="Mã môn học">Mã môn học</td></tr>
<tr><td>1</td><td>TEST001</td><td>Synthetic course</td><td>3</td><td>8</td><td>B</td><td>3</td></tr>
</table></div>'''


def main():
    state = {"cookie": "", "counter": 0, "expired": False, "conflict": False, "challenge": False}
    posts = []
    original_route = BrowserContext.route

    def intercept(route):
        request = route.request
        assert request.url in {LOGIN_URL, PROFILE_URL}, "No outbound requests are allowed"
        headers = {"Content-Type": "text/html; charset=utf-8"}
        if request.method == "POST":
            posts.append(request.url)
            body = LANDING
        elif request.url == LOGIN_URL:
            body = FORM
        elif state["expired"] or state["cookie"] not in request.headers.get("cookie", ""):
            body = FORM
        else:
            body = LANDING.replace("synthetic001", "synthetic-other") if state["conflict"] else LANDING
            if state["challenge"]:
                body += '<input name="captcha">'
        if body != FORM:
            state["counter"] += 1
            state["cookie"] = f"synthetic_cookie={state['counter']}"
            headers["Set-Cookie"] = state["cookie"] + "; Path=/dkmh/; Secure; HttpOnly; SameSite=Strict"
        route.fulfill(body=body, headers=headers)

    def routed_context(self, url, handler, **kwargs):
        # Replace the production allowlist route with an entirely intercepted source.
        self.set_offline(True)
        return original_route(self, "**/*", intercept)

    with patch.object(BrowserContext, "route", routed_context):
        result = collect({"mode": "login", "username": "synthetic001", "password": "synthetic-password"})
        assert result.get("subject") == "synthetic001" and result["cookies"]
        for _ in range(2):
            old_cookie = result["cookies"]
            result = collect({"mode": "resume", "subject": "synthetic001", "cookies": old_cookie})
            assert result.get("subject") == "synthetic001"
            assert result["cookies"] != old_cookie  # Rotated state survives into the next worker.
            assert result["snapshot"]["attempts"][0]["code"] == "TEST001"
        assert len(posts) == 1, "Resume must never submit a password"
        request = {"mode": "resume", "subject": "synthetic001", "cookies": result["cookies"]}
        state["conflict"] = True
        assert collect(request)["error"] == "identity_unverified"
        state["conflict"] = False
        state["expired"] = True
        expired = collect(request)
        assert expired.get("error") == "vnu_reauth_required", {k: expired.get(k) for k in ("error", "stage", "kind")}
        state["expired"] = False
        state["challenge"] = True
        # Use the last cookie issued by the source, without real values in artifacts.
        request["cookies"][0]["value"] = str(state["counter"])
        assert collect(request)["error"] == "interaction_required"
        assert len(posts) == 1
    print("Portal resume: fresh login once, two fresh-browser resumes, rotation, identity conflict, expiry and challenge passed")


if __name__ == "__main__":
    main()
