"""A new release must not reuse a browser's cached application scripts."""

import re

from fastapi.testclient import TestClient

from app import main


def test_changed_script_gets_new_url_even_with_previous_html_validators(tmp_path, monkeypatch):
    (tmp_path / "index.html").write_text(
        '<script src="/static/course-status.js" defer></script>', encoding="utf-8")
    script = tmp_path / "course-status.js"
    script.write_text("old();", encoding="utf-8")
    monkeypatch.setattr(main, "STATIC_ROOT", tmp_path)
    with TestClient(main.app) as client:
        before = client.get("/")
        script.write_text("new();", encoding="utf-8")
        after = client.get("/", headers={"If-None-Match": before.headers.get("etag", '"old"')})
    assert before.headers["cache-control"] == after.headers["cache-control"] == "no-store"
    assert after.status_code == 200
    assert re.search(r'/static/course-status.js\?v=[a-f0-9]+', after.text)
    assert before.text != after.text


def test_static_assets_revalidate_and_personal_responses_remain_uncacheable():
    with TestClient(main.app, base_url="http://127.0.0.1:8000") as client:
        response = client.get("/static/course-status.js")
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-cache"
        private = client.get("/me/academic-program")
        assert private.status_code == 401
        assert private.headers["cache-control"] == "no-store"
