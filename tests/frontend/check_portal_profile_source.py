"""Read landing-page profile before the transcript replaces it; no live requests."""

from playwright.sync_api import sync_playwright

from app.integrations.daotao.client import LOGIN_URL, PROFILE_URL, DaotaoClient
from app.integrations.daotao.snapshot import source_profile, verified_subject

FORM = '''<form id="frmLogin" method="post" action="login.asp">
<input id="txtLoginId" name="txtLoginId"><input id="txtPassword" name="txtPassword">
<input type="submit"></form>'''
LANDING = '''<a id="PortalModule_374" title="Xem điểm sinh viên" onclick="
document.getElementById('facts').remove();document.getElementById('divList3').hidden=false;
">Xem điểm</a>
<div id="facts"><p>MSSV: synthetic001</p><table>
<tr><td>Họ và tên:</td><td>Sinh viên giả lập</td></tr>
<tr><td>Ngành học:</td><td>Ngành nguồn thử</td></tr>
<tr><td>Khóa học:</td><td>QH-2099</td></tr></table></div>
<div id="divList3" hidden><table><tr><td title="Mã môn học">Mã môn học</td></tr>
<tr><td>1</td><td>TEST001</td><td>Môn thử</td><td>3</td><td>8</td><td>B</td><td>3</td></tr>
</table></div>'''


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        try:
            for redirect in (False, True):
                context = browser.new_context()
                requests = []

                def intercept(route):
                    request = route.request
                    requests.append((request.method, request.url))
                    if request.url == LOGIN_URL:
                        if request.method == "POST" and redirect:
                            route.fulfill(status=302, headers={"Location": PROFILE_URL})
                            return
                        body = LANDING if request.method == "POST" else FORM
                    elif request.url == PROFILE_URL:
                        body = LANDING
                    else:
                        raise AssertionError("Unexpected request")
                    route.fulfill(content_type="text/html; charset=utf-8", body=body)

                context.route("**/*", intercept)
                client = DaotaoClient(context)
                subject = client.login("synthetic001", "synthetic-password")
                texts = client.read_profile_texts()
                assert requests.count(("GET", PROFILE_URL)) == 1
                assert source_profile(texts) == {
                    "name": "Sinh viên giả lập", "program": "Ngành nguồn thử", "cohort": "QH-2099"}
                client.open_transcript()
                after = client.page.locator("body").inner_text()
                assert "Sinh viên giả lập" not in after
                assert source_profile(texts)["name"] == "Sinh viên giả lập"
                assert verified_subject("\n".join([*texts, after]), "synthetic001",
                                        authenticated_subject=subject) == "synthetic001"
                assert client.read_transcript()[1][1] == "TEST001"
                context.close()
            check_profile_module(browser)
        finally:
            browser.close()
    print("Portal profile: fixed authenticated landing URL, early capture, transcript preserved")


def check_profile_module(browser):
    """Source screenshot layout, with invented values and delayed frame loading."""
    shell = '''<a id="PortalModule_374" title="Xem điểm sinh viên" onclick="
        document.querySelector('iframe').remove();
        document.getElementById('divList3').hidden=false;">Xem điểm</a>
        <a id="PortalModule_synthetic" title="Hồ sơ sinh viên" onclick="
        setTimeout(() => {const f=document.createElement('iframe');
        f.src='synthetic-profile.asp';document.body.append(f)}, 100)">Hồ sơ sinh viên</a>
        <a id="PortalModule_enrollment" title="Cập nhật hồ sơ sinh viên" onclick="
        document.querySelector('iframe').remove();
        setTimeout(() => {const f=document.createElement('iframe');
        f.src='synthetic-enrollment.asp';document.body.append(f)}, 100)">Cập nhật hồ sơ sinh viên</a>
        <div id="divList3" hidden><table><tr><td title="Mã môn học">Mã môn học</td></tr>
        <tr><td>1</td><td>TEST001</td><td>Môn thử</td><td>3</td><td>8</td><td>B</td><td>3</td>
        </tr></table></div>'''
    profile = '''<fieldset><legend>THÔNG TIN CÁ NHÂN</legend><table>
        <tr><td>Mã sinh viên:</td><td>synthetic001</td><td>Số hồ sơ:</td><td>unrelated</td></tr>
        <tr><td>Họ và tên:</td><td>Sinh viên giả lập</td><td>Giới tính:</td><td>unrelated</td></tr>
        <tr><td>Ngành học:</td><td><input readonly value="Ngành nguồn thử"></td>
            <td>Khóa học:</td><td><select><option value="test">QH-2099</option></select></td></tr>
        <tr hidden><td>Họ và tên:</td><td>Hidden obsolete name</td></tr>
        <tr><td>Họ và tên bố:</td><td>Unrelated family name</td></tr></table></fieldset>'''
    for fields_present in (True, False):
        context = browser.new_context()
        requests = []

        def intercept(route):
            requests.append(route.request.url)
            if route.request.url == PROFILE_URL:
                body = shell
            elif route.request.url.endswith('/synthetic-profile.asp'):
                body = profile if fields_present else profile.replace(
                    'Ngành học:', 'Unknown program label:').replace('Khóa học:', 'Unknown cohort label:')
            elif route.request.url.endswith('/synthetic-enrollment.asp'):
                body = '''<form onsubmit="throw Error('Must never submit')"><fieldset>
                    <legend>Thông tin nhập học</legend><table>
                    <tr><td>Khóa</td><td><select disabled><option>QH.2099.TEST</option></select></td></tr>
                    <tr><td>Lớp quản lý</td><td><select disabled>
                    <option value="other">80 Ngành không được chọn</option>
                    <option value="selected" selected>79 Ngành thử liên ngành</option>
                    </select></td></tr></table></fieldset><button>Lưu</button></form>'''
            else:
                raise AssertionError("Unexpected request")
            route.fulfill(content_type="text/html; charset=utf-8", body=body)

        context.route("**/*", intercept)
        client = DaotaoClient(context)
        texts = client.read_profile_texts(timeout_ms=3000)
        details = source_profile(texts)
        assert details == {"name": "Sinh viên giả lập",
                           "program": "Ngành thử liên ngành", "cohort": "79"}
        assert len(requests) == 3
        assert verified_subject("\n".join(texts), "synthetic001") == "synthetic001"
        client.open_transcript()
        assert not client.page.locator('iframe').count()
        assert source_profile(texts) == details
        assert client.read_transcript()[1][1] == "TEST001"
        context.close()


if __name__ == "__main__":
    main()
