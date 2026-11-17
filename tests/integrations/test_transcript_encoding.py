"""Synthetic encoding regressions; no provider, account database or student data."""

import copy
import json

import pytest

from app.integrations.daotao import store
from app.integrations.daotao.parser import normalize_rows
from app.integrations.daotao.snapshot import snapshot, source_profile
from app.integrations.daotao.text import repair_source_text

NAMES = [
    "Khai phá dữ liệu",
    "Chủ nghĩa xã hội khoa học",
    "Thị giác máy tính",
    "Nguyên lý các ngôn ngữ lập trình",
    "Thiết kế và đánh giá thuật toán",
    "Ngôn ngữ lập trình thế hệ hai",
    "Phương pháp nghiên cứu khoa học",
]
PERSON_NAMES = ["Nguyễn Lễ", "Đỗ Mỹ Linh", "Trần Công Việt"]


def misdecode(text, encoding):
    if encoding == "latin1":
        return text.encode("utf-8").decode(encoding)
    # HTML's Windows-1252 decoding preserves its five undefined C1 bytes.
    chars = []
    for byte in text.encode("utf-8"):
        try:
            chars.append(bytes([byte]).decode("cp1252"))
        except UnicodeDecodeError:
            chars.append(chr(byte))
    return "".join(chars)


@pytest.mark.parametrize("name", [*NAMES, *PERSON_NAMES])
@pytest.mark.parametrize("encoding", ["latin1", "cp1252"])
def test_repair_reversible_course_names(name, encoding):
    broken = misdecode(name, encoding)
    assert repair_source_text(broken) == name
    assert repair_source_text(repair_source_text(broken)) == name


@pytest.mark.parametrize("name", [*NAMES, *PERSON_NAMES, "ASCII Course 101 (A/B)", "", "Là ễ Đ Ω"])
def test_valid_names_are_unchanged(name):
    assert repair_source_text(name) == name


def test_mixed_unicode_and_cp1252_with_undefined_control_bytes():
    # U+009D is undefined in CP1252; defined C1 bytes become punctuation.
    broken = "Đại cương: " + misdecode("Phương pháp thời thế hệ", "cp1252")
    assert "\u009d" in broken
    assert "\u2021" in broken
    assert repair_source_text(broken) == "Đại cương: Phương pháp thời thế hệ"


@pytest.mark.parametrize("broken", [
    "Khai phÃ",                  # Missing continuation byte.
    "Khai phÃ d liệu",           # Missing bytes cannot be inferred from a name.
    "vÃ ",                       # Old whitespace normalization lost U+00A0 in và.
    "Khai phÃ¡ d\ufffd liệu",    # A replacement character has destroyed evidence.
    "\u00c0\u00af",            # Overlong UTF-8.
    "\u00ed\u00a0\u0080",      # UTF-8 surrogate.
    "\u00c2\u0085",            # Do not introduce a control character.
])
def test_unrecoverable_or_invalid_sequences_are_not_guessed(broken):
    assert repair_source_text(broken) == broken


def test_repeated_encoding_is_bounded_and_idempotent():
    broken = NAMES[0]
    for _ in range(3):
        broken = misdecode(broken, "cp1252")
    assert repair_source_text(broken) == NAMES[0]
    too_deep = misdecode(broken, "cp1252")
    assert repair_source_text(too_deep) == too_deep
    assert repair_source_text(repair_source_text(too_deep)) == too_deep


def test_collection_repairs_names_before_nbsp_and_nel_whitespace_is_lost():
    broken = misdecode("Là ễ", "latin1")
    assert "\u00a0" in broken and "\u0085" in broken
    rows = [[" 1 ", "CÃ³", broken, "3", "8,5", "B+", "3.5"]]
    before = copy.deepcopy(rows)
    assert normalize_rows(rows) == [["1", "CÃ³", "Là ễ", "3", "8,5", "B+", "3.5"]]
    assert rows == before


def test_collection_only_repairs_course_name_column_of_known_course_rows():
    broken = misdecode("Khai phá dữ liệu", "cp1252")
    rows = [
        ["1", "CÃ³", broken, "3", "Ã¡", "B+", "3.5"],
        ["Header", "C001", broken, "3", "8,5", "B+", "3.5"],
        ["2", broken],
        ["3", "", broken, "3", "8,5", "B+", "3.5"],
        [broken],
    ]
    expected = copy.deepcopy(rows)
    expected[0][2] = NAMES[0]
    assert normalize_rows(rows) == expected


def stored_profile(name):
    rows = [["HỌC KỲ 1 - 2099-2100"], ["1", "SYN001", name, "3", "8,5", "B+", "3.5"]]
    return {"subject": "synthetic", "profile": {"name": "Synthetic source"},
            "snapshot": snapshot(rows), "fetched_at": "2099-01-01T00:00:00+00:00"}


@pytest.mark.parametrize("name", PERSON_NAMES)
@pytest.mark.parametrize("encoding", ["latin1", "cp1252"])
def test_source_profile_repairs_person_name_before_control_or_whitespace_loss(name, encoding):
    broken = misdecode(name, encoding)
    assert source_profile([f"Họ và tên\t{broken}\r\nNgành học: Ngành thử nghiệm\nKhóa học: 79"]) == {
        "name": name, "program": "Ngành thử nghiệm", "cohort": "79"}


@pytest.mark.parametrize("name", [*PERSON_NAMES, "Là ễ Đ Ω", "Khai phÃ", None, ""])
def test_profile_person_name_projection_preserves_raw_profile(client, monkeypatch, name):
    saved = stored_profile(NAMES[0])
    raw = misdecode(name, "cp1252") if name in PERSON_NAMES else name
    saved["profile"].update(name=raw, program="Ngành nguyên bản", cohort="79")
    before = copy.deepcopy(saved)
    monkeypatch.setattr(store, "profile", lambda owner: saved)
    client.fake_accounts.issue(client, "synthetic-person", linked=True)
    for _ in range(2):
        response = client.get("/me/profile")
        assert response.status_code == 200
        result = response.json()
        assert result["display_profile"] == ({"name": name} if isinstance(name, str) else {})
        assert result["profile"] == before["profile"]
        assert result["snapshot"] == before["snapshot"]
        assert saved == before


def test_profile_projects_names_without_mutating_saved_payload_or_digest(client, monkeypatch):
    saved = stored_profile(misdecode(NAMES[0], "cp1252"))
    before = json.dumps(saved, ensure_ascii=False, sort_keys=True)
    monkeypatch.setattr(store, "profile", lambda owner: saved)
    client.fake_accounts.issue(client, "synthetic-a", linked=True)

    for _ in range(2):
        response = client.get("/me/profile")
        assert response.status_code == 200
        result = response.json()
        assert result["display_names"] == {"1": NAMES[0]}
        assert result["snapshot"] == saved["snapshot"]
        assert result["snapshot"]["attempts"][0]["name"] != NAMES[0]
        assert result["fetched_at"] == saved["fetched_at"]
        assert json.dumps(saved, ensure_ascii=False, sort_keys=True) == before


def test_profile_display_projection_obeys_authentication_and_owner_scope(client, monkeypatch):
    saved = {owner: stored_profile(misdecode(name, "latin1"))
             for owner, name in zip(("synthetic-a", "synthetic-b"), NAMES[:2], strict=True)}
    for owner, name in zip(saved, PERSON_NAMES[:2], strict=True):
        saved[owner]["profile"]["name"] = misdecode(name, "cp1252")
    seen = []

    def read(owner):
        seen.append(owner)
        return saved[owner]

    monkeypatch.setattr(store, "profile", read)
    assert client.get("/me/profile").status_code == 401
    assert seen == []
    client.fake_accounts.issue(client, "unlinked")
    assert client.get("/me/profile").json()["display_names"] == {}
    assert client.get("/me/profile").json()["display_profile"] == {}
    assert seen == []
    for owner, name, person in zip(("synthetic-a", "synthetic-b"), NAMES[:2], PERSON_NAMES[:2], strict=True):
        client.fake_accounts.issue(client, owner, linked=True)
        result = client.get("/me/profile").json()
        assert result["display_names"] == {"1": name}
        assert result["display_profile"] == {"name": person}
    assert seen == ["synthetic-a", "synthetic-b"]


def test_profile_does_not_project_private_names_after_revocation_during_read(client, monkeypatch):
    client.fake_accounts.issue(client, "synthetic-a", linked=True)

    def read(owner):
        client.fake_accounts.revoke(client.cookies.get("study_app_session"))
        return stored_profile(misdecode(NAMES[0], "latin1"))

    monkeypatch.setattr(store, "profile", read)
    response = client.get("/me/profile")
    assert response.status_code == 401
    assert "display_names" not in response.text
    assert NAMES[0] not in response.text
