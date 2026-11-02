"""Main's protected product and local standalone RAG stay separate after merging."""

from fastapi.testclient import TestClient

from app.hus.demo import app as demo_app
from app.main import app as main_app


def test_main_advisor_endpoints_still_require_an_account():
    client = TestClient(main_app, base_url="http://127.0.0.1:8000")
    client.headers["Origin"] = "http://127.0.0.1:8000"
    for path in ("/advisor/chat", "/me/advisor/chat"):
        assert client.post(path, json={}).status_code == 401


def test_main_advisor_origin_boundary_is_preserved():
    client = TestClient(main_app, base_url="http://127.0.0.1:8000")
    response = client.post("/advisor/chat", json={}, headers={"Origin": "https://other.example.test"})
    assert response.status_code == 403


def test_demo_is_not_a_public_main_auth_bypass_or_recommendation_app():
    payload = {"question": "Xin chào", "major": "data_science"}
    product = TestClient(main_app, base_url="http://127.0.0.1:8000")
    demo = TestClient(demo_app)
    assert product.post("/hus/chat", json=payload).status_code == 404
    result = demo.post("/hus/chat", json=payload)
    assert result.status_code == 200 and result.json()["mode"] == "basic_chat"
    assert demo.post("/me/recommendations", json={}).status_code == 404
