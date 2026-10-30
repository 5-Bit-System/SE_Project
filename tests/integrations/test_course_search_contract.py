"""Consumer/provider contracts specified before production implementation (VT-101)."""

import pytest
from fastapi.testclient import TestClient

from app.errors import CatalogError, StorageDataError, StorageUnavailable
from app.main import app
from app.models import Course
from tests.support.search_data import (
    CODE_ORDER,
    CREDIT_ORDER,
    INPUT_CODES,
    NAME_ORDER,
    search_catalog,
)


@pytest.fixture
def search_client(monkeypatch):
    catalog = search_catalog()

    def load(program_id):
        if program_id in {"bt3", "bt3_synthetic"}:
            return catalog
        if program_id == "foreign":
            return catalog.model_copy(update={"program": catalog.program.model_copy(
                update={"program_id": "foreign"}), "courses": [
                    Course(code="F01", name="Foreign", credits=3, block="major")]})
        raise CatalogError("Unknown synthetic program")

    monkeypatch.setattr("app.api.routes.load_catalog", load)
    # No lifespan: fixture controls loading; no portal worker or real DB is started.
    client = TestClient(app, raise_server_exceptions=False)
    yield client, catalog
    client.close()


def fetch(search_client, **params):
    client, _ = search_client
    return client.get("/courses/search", params={"program_id": "bt3", **params})


def codes(data):
    return [item["code"] for item in data["items"]]


def test_legacy_consumer_array_fields_types_order_and_extras(search_client):
    client, catalog = search_client
    response = client.get("/courses", params={"program_id": "bt3"})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    rows = response.json()
    assert isinstance(rows, list)
    assert [row["code"] for row in rows] == INPUT_CODES
    # Expected wire shape derives from the existing Course response model, not new search code.
    assert rows == [course.model_dump(mode="json") for course in catalog.courses]
    for row in rows:
        assert isinstance(row["code"], str) and isinstance(row["name"], str)
        assert type(row["credits"]) is int and isinstance(row["block"], str)
        assert row["name_en"] is None or isinstance(row["name_en"], str)
        assert isinstance(row["prerequisites"], list)
        assert row["test_provenance"] == {"kind": "invented"}
        assert row["hours"] == {"lecture": 0, "practice": None}


def test_new_provider_envelope_defaults_and_course_metadata(search_client):
    response = fetch(search_client)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")
    data = response.json()
    assert set(data) == {"program_id", "items", "total", "page", "page_size"}
    assert data["program_id"] == "bt3_synthetic"
    assert (data["total"], data["page"], data["page_size"]) == (8, 1, 20)
    assert all(type(data[field]) is int for field in ("total", "page", "page_size"))
    assert codes(data) == CODE_ORDER
    assert data["items"][0]["name_en"] is None
    assert data["items"][0]["source_status"] == "draft_unverified"
    assert data["items"][0]["prerequisite_status"] == "draft_unverified"
    assert data["items"][0]["test_provenance"] == {"kind": "invented"}


@pytest.mark.parametrize(("params", "expected"), [
    ({"q": " DATA ", "block": "major", "requirement_type": "elective"}, ["C02", "C04"]),
    ({"q": "c03"}, ["C03"]),
    ({"q": "foundations"}, ["C03"]),
    ({"q": "éTHIQUE"}, ["C06"]),
    ({"q": "ethique"}, []),
    ({"q": "%"}, ["C08"]),
    ({"q": "   "}, CODE_ORDER),
    ({"block": "general", "requirement_type": "required"}, ["C01", "C05"]),
    ({"block": ""}, []),
    ({"block": "does-not-exist"}, []),
    ({"q": "DATA", "block": "general"}, []),
    ({"requirement_type": "graduation"}, ["C07"]),
    ({"requirement_type": "required_excluded"}, ["C06"]),
])
def test_literal_search_and_combined_filters(search_client, params, expected):
    response = fetch(search_client, **params)
    assert response.status_code == 200, response.text
    assert codes(response.json()) == expected
    assert response.json()["total"] == len(expected)


def test_pagination_total_no_duplicate_or_missing_results(search_client):
    pages = [fetch(search_client, page=page, page_size=3).json() for page in (1, 2, 3)]
    assert [len(page["items"]) for page in pages] == [3, 3, 2]
    assert [page["total"] for page in pages] == [8, 8, 8]
    assert [page["page"] for page in pages] == [1, 2, 3]
    assert [code for page in pages for code in codes(page)] == CODE_ORDER
    filtered = fetch(search_client, q="data", page=2, page_size=2).json()
    assert codes(filtered) == ["C04"] and filtered["total"] == 3


@pytest.mark.parametrize(("sort", "expected"), [("code", CODE_ORDER),
                                                ("credits", CREDIT_ORDER), ("name", NAME_ORDER)])
def test_stable_sort_ties_and_repository_order(search_client, sort, expected):
    _, catalog = search_client
    before = catalog.model_dump(mode="json")
    first = fetch(search_client, sort=sort, page_size=100).json()
    assert codes(first) == expected
    assert catalog.model_dump(mode="json") == before
    catalog.courses.reverse()
    for page, offset in ((1, 0), (2, 3), (3, 6)):
        assert codes(fetch(search_client, sort=sort, page=page, page_size=3).json()) == expected[offset:offset + 3]


@pytest.mark.parametrize("params", [{"page": 4, "page_size": 3}, {"page": 10**12},
                                    {"q": "no-such-course"}])
def test_empty_result_is_valid_success(search_client, params):
    response = fetch(search_client, **params)
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == (0 if "q" in params else 8)


@pytest.mark.parametrize(("params", "field"), [
    ({"page": 0}, "page"), ({"page": -1}, "page"), ({"page": "abc"}, "page"),
    ({"page_size": 0}, "page_size"), ({"page_size": 101}, "page_size"),
    ({"sort": "random"}, "sort"), ({"requirement_type": "invalid"}, "requirement_type"),
    ({"q": "x" * 121}, "q"),
])
def test_query_validation_error_contract(search_client, params, field):
    response = fetch(search_client, **params)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert ["query", field] in [error["loc"] for error in detail]


@pytest.mark.parametrize("path", ["/courses", "/courses/search"])
def test_required_program_and_unknown_program_contract(search_client, path):
    client, _ = search_client
    missing = client.get(path)
    assert missing.status_code == 422
    assert missing.json()["detail"][0]["loc"] == ["query", "program_id"]
    unknown = client.get(path, params={"program_id": "unknown"})
    assert unknown.status_code == 404
    assert unknown.json() == {"detail": "Unknown synthetic program"}


@pytest.mark.parametrize("size", [1, 100])
def test_pagination_boundaries(search_client, size):
    data = fetch(search_client, page_size=size).json()
    assert data["page_size"] == size and data["total"] == 8
    assert codes(data) == (["C01"] if size == 1 else CODE_ORDER)


def test_program_isolation_and_single_snapshot_load(search_client, monkeypatch):
    client, _ = search_client
    result = client.get("/courses/search", params={"program_id": "foreign"})
    assert result.status_code == 200
    assert result.json()["program_id"] == "foreign"
    assert codes(result.json()) == ["F01"]
    calls = []

    def load(program_id):
        calls.append(program_id)
        return search_catalog()

    monkeypatch.setattr("app.api.routes.load_catalog", load)
    assert fetch(search_client).status_code == 200
    assert calls == ["bt3"]


@pytest.mark.parametrize("path", ["/courses", "/courses/search"])
@pytest.mark.parametrize(("error", "status", "detail"), [
    (StorageUnavailable("Synthetic storage unavailable"), 503, "Synthetic storage unavailable"),
    (StorageDataError("private-internal-synthetic"), 500,
     "Dữ liệu máy chủ chưa hợp lệ; kiểm tra migration/seed"),
    (ValueError("Synthetic domain error"), 422, "Synthetic domain error"),
])
def test_failure_contract_never_returns_default_success(search_client, monkeypatch, path, error, status, detail):
    client, _ = search_client

    def broken(program_id):
        raise error

    monkeypatch.setattr("app.api.routes.load_catalog", broken)
    response = client.get(path, params={"program_id": "bt3"})
    assert response.status_code == status, "Dependency failure must not become empty success"
    assert response.json() == {"detail": detail}
    assert "private-internal-synthetic" not in response.text


def test_unexpected_exception_is_500_not_empty_success(search_client, monkeypatch):
    def broken(program_id):
        raise RuntimeError("private-internal-synthetic")

    monkeypatch.setattr("app.api.routes.load_catalog", broken)
    response = fetch(search_client)
    assert response.status_code == 500
    assert "private-internal-synthetic" not in response.text
    assert response.text != "[]"
