"""Synthetic loading/error UI check; intercepts all requests and never contacts VNU."""

import mimetypes
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright



def main():
    root = Path(__file__).resolve().parents[2] / "app" / "static"
    pending=[]
    with sync_playwright() as p:
     browser=p.chromium.launch(headless=True, channel="chrome")
     try:
      page=browser.new_page()
      def route_request(route):
       path=urlsplit(route.request.url).path
       if path=='/auth/portal':
        pending.append(route)
       elif path.startswith(('/auth/','/me/')):
        route.fulfill(status=401,json={'detail':'session_expired'})
       else:
        file=root/('index.html' if path=='/' else path.removeprefix('/static/'))
        if file.is_file():
         route.fulfill(body=file.read_bytes(),content_type=mimetypes.guess_type(str(file))[0] or 'text/plain')
        else:
         route.fulfill(status=404,body='')
      page.route('**/*',route_request)
      page.goto('http://127.0.0.1:8000/')
      page.evaluate("window.workspaceNavigate('portal-dialog')")
      page.locator('#portal-username').fill('synthetic-only')
      page.locator('#portal-password').fill('synthetic-password')
      page.locator('#portal-submit').click()
      page.wait_for_function("document.querySelector('#portal-submit').classList.contains('is-loading')")
      assert page.locator('#portal-submit').is_disabled()
      assert page.locator('#portal-login').get_attribute('aria-busy')=='true'
      assert page.locator('#portal-status').is_visible()
      assert page.locator('#portal-submit').inner_text()=='Đang lấy dữ liệu…'
      page.wait_for_timeout(100)
      assert pending
      pending.pop().fulfill(status=401,json={'detail':'identity_unverified'})
      page.wait_for_function("!document.querySelector('#portal-submit').disabled")
      assert page.locator('#portal-login').get_attribute('aria-busy')=='false'
      assert 'is-loading' not in (page.locator('#portal-status').get_attribute('class') or '')
      assert 'Chưa xác minh' in page.locator('#portal-status').inner_text()
      print('PASS: pending request shows loading; error clears spinner and unlocks retry')
     finally:
      browser.close()


if __name__ == "__main__":
    main()
