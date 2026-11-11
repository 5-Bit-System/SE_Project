"""Tests for HUS chat history repository, schemas, and REST endpoints."""

from __future__ import annotations

import concurrent.futures
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.hus import chat_history_repository
from app.hus.demo import app
from app.schemas.hus import (
    HUSChatHistoryAppend,
    HUSChatHistoryResponse,
    HUSChatMessage,
)


@pytest.fixture(autouse=True)
def isolated_history_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("HUS_CHAT_HISTORY_DIR", str(tmp_path))
    yield tmp_path


def test_empty_account_returns_empty_list():
    account_id = "test_user_empty"
    assert chat_history_repository.get_history(account_id, major="data_science") == []
    assert chat_history_repository.get_history(account_id, major=None) == []


def test_corrupted_json_returns_empty_list(tmp_path):
    account_id = "test_user_corrupt"
    bad_file = tmp_path / f"{account_id}.json"
    bad_file.write_text("{this is not valid json!}", encoding="utf-8")

    assert chat_history_repository.get_history(account_id, major="data_science") == []
    assert chat_history_repository.get_history(account_id, major=None) == []


def test_append_message_separated_by_major():
    account_id = "test_user_majors"

    msg1 = {"role": "user", "reply": "khdl question", "citations": []}
    msg2 = {"role": "assistant", "reply": "khdl answer", "generation_mode": "grounded_llm"}
    chat_history_repository.append_message(account_id, "data_science", msg1)
    chat_history_repository.append_message(account_id, "data_science", msg2)

    msg3 = {"role": "user", "reply": "khmt question", "citations": []}
    chat_history_repository.append_message(account_id, "computer_science", msg3)

    ds_history = chat_history_repository.get_history(account_id, major="data_science")
    cs_history = chat_history_repository.get_history(account_id, major="computer_science")
    all_history = chat_history_repository.get_history(account_id, major=None)

    assert len(ds_history) == 2
    assert ds_history[0]["reply"] == "khdl question"
    assert ds_history[1]["reply"] == "khdl answer"
    assert ds_history[1]["generation_mode"] == "grounded_llm"

    assert len(cs_history) == 1
    assert cs_history[0]["reply"] == "khmt question"

    assert len(all_history) == 3


def test_max_messages_truncation():
    account_id = "test_user_truncate"
    for i in range(15):
        chat_history_repository.append_message(
            account_id,
            "data_science",
            {"role": "user", "reply": f"message {i}"},
            max_messages_per_major=5,
        )

    history = chat_history_repository.get_history(account_id, "data_science")
    assert len(history) == 5
    assert history[0]["reply"] == "message 10"
    assert history[-1]["reply"] == "message 14"


@pytest.mark.parametrize(
    "invalid_id",
    [
        "../../etc/passwd",
        "../account",
        "user/name",
        "user\\name",
        "user name",
        "user$name",
        "",
        None,
    ],
)
def test_path_traversal_and_invalid_account_id_rejected(invalid_id: Any):
    with pytest.raises(ValueError, match="invalid_account_id"):
        chat_history_repository.get_history(invalid_id, major="data_science")

    with pytest.raises(ValueError, match="invalid_account_id"):
        chat_history_repository.append_message(
            invalid_id, "data_science", {"role": "user", "reply": "hi"}
        )

    with pytest.raises(ValueError, match="invalid_account_id"):
        chat_history_repository.clear_history(invalid_id, major="data_science")


def test_atomic_write_concurrency():
    account_id = "test_user_concurrent"

    def worker(worker_id: int):
        for i in range(10):
            chat_history_repository.append_message(
                account_id,
                "data_science",
                {"role": "user", "reply": f"worker {worker_id} msg {i}"},
                max_messages_per_major=100,
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, w) for w in range(5)]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    history = chat_history_repository.get_history(account_id, "data_science")
    assert len(history) == 50


def test_clear_history_specific_major_and_all():
    account_id = "test_user_clear"

    chat_history_repository.append_message(
        account_id, "data_science", {"role": "user", "reply": "ds msg"}
    )
    chat_history_repository.append_message(
        account_id, "computer_science", {"role": "user", "reply": "cs msg"}
    )

    # Clear specific major
    assert chat_history_repository.clear_history(account_id, major="data_science") is True
    assert chat_history_repository.get_history(account_id, "data_science") == []
    assert len(chat_history_repository.get_history(account_id, "computer_science")) == 1

    # Clear all majors (removes file)
    assert chat_history_repository.clear_history(account_id, major=None) is True
    assert chat_history_repository.get_history(account_id, "computer_science") == []
    assert chat_history_repository.get_history(account_id, None) == []


def test_schema_serialization():
    msg = HUSChatMessage(
        role="assistant",
        reply="Câu trả lời mẫu",
        citations=[{"label": "QĐ 3569"}],
        generation_mode="grounded_llm",
    )
    assert msg.role == "assistant"
    assert msg.citations == [{"label": "QĐ 3569"}]

    append_payload = HUSChatHistoryAppend(
        major="data_science",
        role="user",
        reply="Học phí bao nhiêu?",
    )
    assert append_payload.major == "data_science"
    assert append_payload.citations == []

    response = HUSChatHistoryResponse(
        account_id="acc-123",
        major="data_science",
        messages=[msg],
    )
    assert response.account_id == "acc-123"
    assert len(response.messages) == 1


# --- API Endpoint tests ---


def test_api_get_history_without_auth():
    with TestClient(app) as client:
        res = client.get("/hus/chat/history", params={"major": "data_science"})
        assert res.status_code == 200
        data = res.json()
        assert data["account_id"] is None
        assert data["major"] == "data_science"
        assert data["messages"] == []


def test_api_post_history_guest_ignored():
    with TestClient(app) as client:
        payload = {
            "major": "data_science",
            "role": "user",
            "reply": "xin chào",
            "citations": [],
        }
        res = client.post("/hus/chat/history", json=payload)
        assert res.status_code == 200
        assert res.json() == {"status": "guest_ignored"}


def test_api_delete_history_no_account():
    with TestClient(app) as client:
        res = client.delete("/hus/chat/history", params={"major": "data_science"})
        assert res.status_code == 200
        assert res.json() == {"status": "no_account"}


def test_api_chat_history_lifecycle_with_dev_header():
    headers = {"X-Account-ID": "acc-dev-123"}
    with TestClient(app) as client:
        # 1. Initially empty
        res = client.get(
            "/hus/chat/history", params={"major": "data_science"}, headers=headers
        )
        assert res.status_code == 200
        assert res.json()["messages"] == []
        assert res.json()["account_id"] == "acc-dev-123"

        # 2. Append user message
        res_post1 = client.post(
            "/hus/chat/history",
            headers=headers,
            json={
                "major": "data_science",
                "role": "user",
                "reply": "học môn gì trước?",
                "citations": [],
            },
        )
        assert res_post1.status_code == 200
        assert res_post1.json() == {"status": "saved", "count": 1}

        # 3. Append assistant message
        res_post2 = client.post(
            "/hus/chat/history",
            headers=headers,
            json={
                "major": "data_science",
                "role": "assistant",
                "reply": "Nên học MAT2400 trước.",
                "citations": [{"citation_id": "c1", "label": "QĐ 3569"}],
                "generation_mode": "grounded_llm",
            },
        )
        assert res_post2.status_code == 200
        assert res_post2.json() == {"status": "saved", "count": 2}

        # 4. Get history and verify contents
        res_get = client.get(
            "/hus/chat/history", params={"major": "data_science"}, headers=headers
        )
        assert res_get.status_code == 200
        data = res_get.json()
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["reply"] == "học môn gì trước?"
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][1]["reply"] == "Nên học MAT2400 trước."
        assert data["messages"][1]["generation_mode"] == "grounded_llm"
        assert len(data["messages"][1]["citations"]) == 1

        # 5. Clear specific major
        res_del = client.delete(
            "/hus/chat/history", params={"major": "data_science"}, headers=headers
        )
        assert res_del.status_code == 200
        assert res_del.json() == {"status": "cleared"}

        # 6. Verify now empty
        res_get_after = client.get(
            "/hus/chat/history", params={"major": "data_science"}, headers=headers
        )
        assert res_get_after.status_code == 200
        assert res_get_after.json()["messages"] == []


def test_api_chat_history_with_mocked_cookie_auth():
    mock_principal = {"account_id": "auth-user-999", "role": "student"}
    mock_auth_dep = MagicMock()
    mock_auth_dep.optional_account = AsyncMock(return_value=mock_principal)
    with patch.dict("sys.modules", {"app.auth.dependencies": mock_auth_dep}):
        with TestClient(app) as client:
            client.cookies.set("study_app_session", "valid-token")
            # 1. Post message with session cookie
            res = client.post(
                "/hus/chat/history",
                json={
                    "major": "data_science",
                    "role": "user",
                    "reply": "Câu hỏi từ tài khoản đã đăng nhập",
                },
            )
            assert res.status_code == 200
            assert res.json() == {"status": "saved", "count": 1}

            # 2. Get history
            res_get = client.get(
                "/hus/chat/history",
                params={"major": "data_science"},
            )
            assert res_get.status_code == 200
            data = res_get.json()
            assert data["account_id"] == "auth-user-999"
            assert len(data["messages"]) == 1
            assert data["messages"][0]["reply"] == "Câu hỏi từ tài khoản đã đăng nhập"

            # 3. Clear history
            res_del = client.delete(
                "/hus/chat/history",
            )
            assert res_del.status_code == 200
            assert res_del.json() == {"status": "cleared"}

            res_get2 = client.get(
                "/hus/chat/history",
                params={"major": "data_science"},
            )
            assert res_get2.json()["messages"] == []


def test_corrupted_majors_null_returns_empty_list(tmp_path):
    account_id = "test_user_null_majors"
    bad_file = tmp_path / f"{account_id}.json"
    bad_file.write_text('{"account_id": "test_user_null_majors", "majors": null}', encoding="utf-8")

    assert chat_history_repository.get_history(account_id, major="data_science") == []
    assert chat_history_repository.get_history(account_id, major=None) == []


def test_api_invalid_account_id_header_returns_400():
    headers = {"X-Account-ID": "../../etc/passwd"}
    with TestClient(app) as client:
        res = client.get(
            "/hus/chat/history", params={"major": "data_science"}, headers=headers
        )
        assert res.status_code == 400
        assert res.json()["detail"] == "invalid_account_id"

        res_post = client.post(
            "/hus/chat/history",
            headers=headers,
            json={"major": "data_science", "role": "user", "reply": "hi"},
        )
        assert res_post.status_code == 400
        assert res_post.json()["detail"] == "invalid_account_id"

        res_del = client.delete(
            "/hus/chat/history", params={"major": "data_science"}, headers=headers
        )
        assert res_del.status_code == 400
        assert res_del.json()["detail"] == "invalid_account_id"
