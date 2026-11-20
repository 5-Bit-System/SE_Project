"""Persistent chat history repository partitioned by account and major.

Storage format: data/hus_chat_history/{account_id}.json
Configurable via HUS_CHAT_HISTORY_DIR environment variable.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ACCOUNT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")
_LOCK = threading.Lock()


def _get_storage_dir() -> Path:
    env_dir = os.environ.get("HUS_CHAT_HISTORY_DIR")
    if env_dir:
        path = Path(env_dir)
    else:
        path = Path("data/hus_chat_history")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _validate_account_id(account_id: str) -> str:
    if not isinstance(account_id, str) or not ACCOUNT_ID_PATTERN.fullmatch(account_id):
        raise ValueError("invalid_account_id")
    return account_id


def _get_account_file(account_id: str) -> Path:
    validated_id = _validate_account_id(account_id)
    return _get_storage_dir() / f"{validated_id}.json"


def _read_account_data(account_id: str) -> dict[str, Any]:
    target_file = _get_account_file(account_id)
    if not target_file.exists():
        return {"account_id": account_id, "updated_at": None, "majors": {}}
    try:
        content = target_file.read_text(encoding="utf-8")
        if not content.strip():
            return {"account_id": account_id, "updated_at": None, "majors": {}}
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return {"account_id": account_id, "updated_at": None, "majors": {}}
        if not isinstance(parsed.get("majors"), dict):
            parsed["majors"] = {}
        return parsed
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {"account_id": account_id, "updated_at": None, "majors": {}}


def _write_account_data(account_id: str, data: dict[str, Any]) -> None:
    storage_dir = _get_storage_dir()
    target_file = _get_account_file(account_id)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=storage_dir,
            delete=False,
            suffix=".tmp",
            mode="w",
            encoding="utf-8",
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)
            json.dump(data, tmp_file, ensure_ascii=False, indent=2)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_path, target_file)
    except Exception:
        if tmp_path is not None and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def get_history(account_id: str, major: str | None = None) -> list[dict[str, Any]]:
    """Retrieve chat history messages for an account, filtered by major if specified."""
    _validate_account_id(account_id)
    with _LOCK:
        data = _read_account_data(account_id)
        majors_dict = data.get("majors") if isinstance(data.get("majors"), dict) else {}
        if major is not None:
            clean_major = major.strip()
            major_msgs = majors_dict.get(clean_major, [])
            if isinstance(major_msgs, list):
                return [dict(m) for m in major_msgs if isinstance(m, dict)]
            return []

        all_msgs: list[dict[str, Any]] = []
        for msg_list in majors_dict.values():
            if isinstance(msg_list, list):
                all_msgs.extend([dict(m) for m in msg_list if isinstance(m, dict)])
        all_msgs.sort(key=lambda m: str(m.get("timestamp") or ""))
        return all_msgs


def append_message(
    account_id: str,
    major: str,
    message: dict[str, Any],
    max_messages_per_major: int = 100,
) -> list[dict[str, Any]]:
    """Append a chat message to the history for a given account and major.

    Bounds history to max_messages_per_major to prevent unbounded file growth.
    Writes atomically to disk.
    """
    _validate_account_id(account_id)
    if not isinstance(major, str) or not major.strip():
        raise ValueError("invalid_major")
    clean_major = major.strip()

    msg = {
        "role": message.get("role", "user"),
        "reply": str(message.get("reply", "")),
        "citations": list(message.get("citations") or []),
        "generation_mode": message.get("generation_mode"),
        "timestamp": message.get("timestamp") or datetime.now(timezone.utc).isoformat(),
    }

    with _LOCK:
        data = _read_account_data(account_id)
        if "majors" not in data or not isinstance(data["majors"], dict):
            data["majors"] = {}
        if clean_major not in data["majors"] or not isinstance(data["majors"][clean_major], list):
            data["majors"][clean_major] = []

        data["majors"][clean_major].append(msg)
        if max_messages_per_major > 0 and len(data["majors"][clean_major]) > max_messages_per_major:
            data["majors"][clean_major] = data["majors"][clean_major][-max_messages_per_major:]

        data["account_id"] = account_id
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_account_data(account_id, data)
        return list(data["majors"][clean_major])


def clear_history(account_id: str, major: str | None = None) -> bool:
    """Clear chat history for a specific major or the entire account."""
    target_file = _get_account_file(account_id)
    with _LOCK:
        if major is None:
            if target_file.exists():
                try:
                    target_file.unlink()
                except OSError:
                    return False
            return True

        clean_major = major.strip()
        data = _read_account_data(account_id)
        if "majors" in data and isinstance(data["majors"], dict):
            if clean_major in data["majors"]:
                data["majors"][clean_major] = []
                data["updated_at"] = datetime.now(timezone.utc).isoformat()
                _write_account_data(account_id, data)
        return True
