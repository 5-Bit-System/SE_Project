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
    product_res = product.post("/hus/chat", json=payload)
    assert product_res.status_code == 200 and product_res.json()["mode"] == "basic_chat"
    assert product_res.headers.get("cache-control") == "no-store"
    result = demo.post("/hus/chat", json=payload)
    assert result.status_code == 200 and result.json()["mode"] == "basic_chat"
    assert demo.post("/me/recommendations", json={}).status_code == 404


def test_main_app_exposes_all_hus_rag_endpoints_with_cache_control_no_store():
    client = TestClient(main_app, base_url="http://127.0.0.1:8000")

    # 1. GET /hus/config
    cfg = client.get("/hus/config")
    assert cfg.status_code == 200
    assert cfg.headers.get("cache-control") == "no-store"
    data = cfg.json()
    assert "majors" in data and len(data["majors"]) == 4

    # 2. POST /hus/chat
    chat_res = client.post("/hus/chat", json={"question": "Xin chào", "major": "data_science"})
    assert chat_res.status_code == 200
    assert chat_res.headers.get("cache-control") == "no-store"
    assert chat_res.json()["mode"] == "basic_chat"

    # 3. POST /hus/retrieve
    ret_res = client.post("/hus/retrieve", json={"question": "MAT3533 tín chỉ", "major": "data_science"})
    assert ret_res.status_code == 200
    assert ret_res.headers.get("cache-control") == "no-store"
    ret_data = ret_res.json()
    assert "top_k_chunks" in ret_data

    # 4. GET /hus/questions
    q_res = client.get("/hus/questions", params={"major": "data_science", "version": "QD3569-2023"})
    assert q_res.status_code == 200
    assert q_res.headers.get("cache-control") == "no-store"
    assert "groups" in q_res.json()

    # 4b. GET /hus/questions with invalid version returns 404
    q_404 = client.get("/hus/questions", params={"major": "data_science", "version": "non-existent"})
    assert q_404.status_code == 404

    # 5. GET /hus/sources/{source_id}
    src_404 = client.get("/hus/sources/invalid_source_id")
    assert src_404.status_code == 404
