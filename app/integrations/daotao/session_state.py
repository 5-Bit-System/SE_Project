"""Bounded VNU cookie contract. Only server-owned process memory may retain it."""

import json
import math

from app.integrations.daotao.snapshot import PortalFailure

HOST = "daotao.vnu.edu.vn"
MAX_STATE_BYTES = 64 * 1024
MAX_INPUT_BYTES = 72 * 1024
COOKIE_FIELDS = {"name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite"}


def validated_cookies(cookies):
    """Copy an allowlisted cookie jar, or fail without exposing its contents."""
    if not isinstance(cookies, list) or len(cookies) > 64:
        raise PortalFailure("portal_state_invalid")
    result = []
    for cookie in cookies:
        if not isinstance(cookie, dict) or set(cookie) - COOKIE_FIELDS:
            raise PortalFailure("portal_state_invalid")
        if (not isinstance(cookie.get("name"), str) or not 0 < len(cookie["name"]) <= 256
                or not isinstance(cookie.get("value"), str) or len(cookie["value"]) > 4096
                or not isinstance(cookie.get("domain"), str) or cookie["domain"] not in {HOST, "." + HOST}
                or not isinstance(cookie.get("path"), str) or not cookie["path"].startswith("/")):
            raise PortalFailure("portal_state_invalid")
        expiry = cookie.get("expires", -1)
        if (isinstance(expiry, bool) or not isinstance(expiry, (int, float))
                or not math.isfinite(expiry) or (expiry < 0 and expiry != -1)):
            raise PortalFailure("portal_state_invalid")
        if any(key in cookie and not isinstance(cookie[key], bool) for key in ("secure", "httpOnly")):
            raise PortalFailure("portal_state_invalid")
        if "sameSite" in cookie and (not isinstance(cookie["sameSite"], str)
                                     or cookie["sameSite"] not in {"Strict", "Lax", "None"}):
            raise PortalFailure("portal_state_invalid")
        result.append(dict(cookie))
    if len(json.dumps(result, ensure_ascii=True).encode("utf-8")) > MAX_STATE_BYTES:
        raise PortalFailure("portal_state_invalid")
    return result
