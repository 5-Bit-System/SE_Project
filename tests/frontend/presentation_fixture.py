"""Shared static-only fixture for UI checks; no HTTP request reaches a server."""

import mimetypes
from pathlib import Path
from urllib.parse import urlsplit

from tests.frontend.auth_fixture import session_payload


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
