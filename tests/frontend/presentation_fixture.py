"""Shared static-only fixture for UI checks; no HTTP request reaches a server."""

import mimetypes
from pathlib import Path
from urllib.parse import urlsplit

from tests.frontend.auth_fixture import session_payload


def open_plan_tools(page):
    """Open the retained academic/saved-plan tools through their visible control."""
    summary = page.locator('#academic-plan-tools > summary')
    summary.wait_for(state='visible')
    if page.locator('#academic-plan-tools').get_attribute('open') is None:
        summary.click()
        page.wait_for_function("""() => {
            const element = document.querySelector('#academic-plan-tools');
            if (!element.open) return false;
            if (!CSS.supports('interpolate-size: allow-keywords')) return true;
            const content = getComputedStyle(element, '::details-content');
            return content.contentVisibility !== 'hidden' && Number(content.opacity) >= .99;
        }""")


def common_route(route, *, authenticated=True):
    path = urlsplit(route.request.url).path
    if path == '/auth/session':
        route.fulfill(json=session_payload(authenticated))
    elif path == '/me/semester-plans':
        route.fulfill(json={'plans': []})
    elif path == '/' or path.startswith('/static/'):
        static = Path(__file__).resolve().parents[2] / 'app/static'
        file = static / ('index.html' if path == '/' else path.removeprefix('/static/'))
        if file.is_file():
            route.fulfill(body=file.read_bytes(),
                          content_type=mimetypes.guess_type(file)[0] or 'text/plain')
        else:
            route.fulfill(status=404)
    else:
        return False
    return True
