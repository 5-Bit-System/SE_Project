"""Real Chrome, synthetic portal documents only; no credentials or VNU access."""

from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import sync_playwright

from app.integrations.daotao.client import PROFILE_URL, DaotaoClient
from app.integrations.daotao.snapshot import snapshot

TABLE = '''<div id="divList3"><table><tr><td title="Mã môn học">Mã môn học</td></tr>
<tr><td>HỌC KỲ 1 - 2099-2100</td></tr>
<tr><td>1</td><td>TEST001</td><td>Invented course</td><td>3</td><td>7.5</td><td>B</td><td>3</td></tr>
<tr><td>Tổng tín chỉ: 3</td></tr></table></div>'''


def main():
    cases = [
        (TABLE, "complete"),
        ('<select><option>Tất cả</option></select>' + TABLE, "unknown"),
        ('<select disabled><option>Read-only source metadata</option></select><input readonly value="Source label">' + TABLE, "complete"),
        ('<label><input type="checkbox">Unknown control</label>' + TABLE, "unknown"),
        ('<label><input type="checkbox" checked>Unknown control</label>' + TABLE, "unknown"),
        ('<a rel="next" href="next.asp">Next</a>' + TABLE, "unknown"),
        ('<div aria-busy="true">Loading</div>' + TABLE, "unknown"),
        (TABLE.replace('<tr><td>1</td>', '<tr hidden><td>1</td>'), "unknown"),
        (TABLE + TABLE, "unknown"),
    ]
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True,
                                    proxy={"server": "http://127.0.0.1:9"})
        try:
            for html, expected in cases:
                context = browser.new_context()
                context.route("**/*", lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=html))
                client = DaotaoClient(context)
                client.page.goto(PROFILE_URL)
                rows, evidence = client.read_transcript_capture(timeout_ms=4000)
                assert snapshot(rows, evidence)["completeness"] == expected
                assert evidence["stable_reads"] == 3
                assert evidence["network_idle"] is True
                context.close()
            # showApp can load the existing menu route inside a deeper module frame.
            for handler_target, module_path, active_filter, expected in [
                    ('ListPoint/listpoint.asp', '/dkmh/Student/Modules/ListPoint/listpoint.asp', False, 'complete'),
                    ('ListPoint/listpoint.asp', '/ListPoint/synthetic-module.aspx', False, 'complete'),
                    ('ListPoint/listpoint.asp', '/ListPoint/synthetic-module.aspx', True, 'unknown'),
                    ('Other/listpoint.asp', '/ListPoint/synthetic-module.aspx', False, 'unknown')]:
                context = browser.new_context()
                shell = '''<a id="PortalModule_374" title="Xem điểm sinh viên"
                    onclick="showApp(this.id, 'TARGET')">Xem điểm</a>
                    <script>function showApp(id, target) { const frame=document.createElement('iframe');
                    frame.src='MODULE'; document.body.append(frame); }</script>'''.replace('TARGET', handler_target).replace('MODULE', module_path)
                module = '<select disabled><option>Source metadata</option></select>' + TABLE
                if active_filter:
                    module = '<select><option>Semester filter</option></select>' + module

                def intercept(route):
                    body = shell if route.request.url == PROFILE_URL else module
                    route.fulfill(content_type="text/html; charset=utf-8", body=body)

                context.route("**/*", intercept)
                client = DaotaoClient(context)
                client.page.goto(PROFILE_URL)
                client.open_transcript()
                rows, evidence = client.read_transcript_capture(timeout_ms=4000)
                assert snapshot(rows, evidence)["completeness"] == expected
                context.close()
            for event in ('onclick', 'onchange'):
                context = browser.new_context()
                full_view = '''<label><input id="include-all" style="position:absolute;left:-10000px" type="checkbox" EVENT="submit_d()">Xem cả các môn rớt</label>
                    <script>function submit_d() { if(document.querySelector('#include-all').checked) {
                    document.querySelector('#divList3 table').insertAdjacentHTML('beforeend',
                    '<tr><td>2</td><td>TESTFAIL</td><td>Invented failed course</td><td>3</td><td>2</td><td>F</td><td>0</td></tr>');
                    } }</script>'''.replace('EVENT', event) + TABLE
                context.route("**/*", lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=full_view))
                client = DaotaoClient(context)
                client.page.goto(PROFILE_URL)
                rows, evidence = client.read_transcript_capture(timeout_ms=4000)
                result = snapshot(rows, evidence)
                assert result['completeness'] == 'complete', (event, evidence, client.page.locator('#include-all').is_checked())
                assert [row['code'] for row in result['attempts']] == ['TEST001', 'TESTFAIL']
                assert client.page.locator('#include-all').is_checked()
                second_rows, second_evidence = client.read_transcript_capture(timeout_ms=4000)
                assert len(snapshot(second_rows, second_evidence)['attempts']) == 2
                context.close()
            for echoes_selection in (True, False):
                context = browser.new_context()
                requests = []

                def native_form(route):
                    requests.append(route.request.url)
                    expanded = parse_qs(urlsplit(route.request.url).query).get('all') == ['1']
                    checkbox = '<form method="get"><label><input id="include-all" name="all" value="1" type="checkbox" onchange="submit_d()" CHECKED>Xem cả môn rớt</label></form><script>function submit_d(){document.forms[0].submit()}</script>'
                    body = checkbox.replace('CHECKED', 'checked' if expanded and echoes_selection else '') + TABLE
                    if expanded:
                        body = body.replace('</table>', '<tr><td>2</td><td>TESTFAIL</td><td>Invented failed course</td><td>3</td><td>2</td><td>F</td><td>0</td></tr></table>')
                    route.fulfill(content_type='text/html; charset=utf-8', body=body)

                context.route('**/*', native_form)
                client = DaotaoClient(context)
                client.page.goto(PROFILE_URL)
                rows, evidence = client.read_transcript_capture(timeout_ms=4000)
                assert snapshot(rows, evidence)['completeness'] == ('complete' if echoes_selection else 'unknown')
                assert len(snapshot(rows, evidence)['attempts']) == 2
                assert len(requests) == 2
                context.close()
        finally:
            browser.close()
    print("Portal collection: full table, menu-owned nested module, read-only metadata, active filters/paging/hidden/multiple tables passed")


if __name__ == "__main__":
    main()
