from functools import partial
import json
import shutil

from fastapi.testclient import TestClient
import pytest

import app.main as main
from app.catalog import DATA_ROOT, list_catalogs, load_catalog
from app.models import CourseResponse, ProgramResponse


@pytest.fixture
def client():
    with TestClient(main.app) as client:
        yield client


@pytest.fixture
def catalog_root(tmp_path, monkeypatch):
    root = tmp_path / "curricula"
    shutil.copytree(DATA_ROOT, root)
    monkeypatch.setattr(main, "list_catalogs", partial(list_catalogs, root=root))
    monkeypatch.setattr(main, "load_catalog", partial(load_catalog, root=root))
    return root


def test_program_response_contract_and_metadata(client):
    response = client.get("/programs")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    expected = list_catalogs()
    assert response.json() == [
        {**catalog.program.model_dump(), "course_count": len(catalog.courses)}
        for catalog in expected
    ]
    assert [ProgramResponse.model_validate(item).course_count for item in response.json()] == [65, 67, 90, 68]
    assert all("source_issues" in item and "track_selection" in item for item in response.json())


@pytest.mark.parametrize("program_id", sorted(path.name for path in DATA_ROOT.iterdir() if path.is_dir()))
def test_course_response_matches_only_selected_catalog(client, program_id):
    response = client.get("/courses", params={"program_id": program_id})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    catalog = load_catalog(program_id)
    assert response.json() == [course.model_dump() for course in catalog.courses]
    assert all(CourseResponse.model_validate(item) for item in response.json())
    assert len({course["code"] for course in response.json()}) == len(catalog.courses)


def test_shared_code_keeps_program_specific_metadata(client):
    def course(program_id):
        return next(item for item in client.get("/courses", params={"program_id": program_id}).json() if item["code"] == "MAT2505")

    math = course("toan_hoc_7460101_2022")
    cs = course("khmtt_7480113qtd_2022")
    assert math["block"] == "group" and math["choice_group_ids"] == ["programming"]
    assert cs["block"] == "discipline" and cs["choice_group_ids"] == []


def test_conflicts_and_provenance_are_preserved_in_response(client):
    courses = client.get("/courses", params={"program_id": "toan_hoc_7460101_2022"}).json()
    course = next(item for item in courses if item["code"] == "MAT3325")
    assert course["prerequisite_status"] == "source_conflict"
    assert course["source_rows"] == [56, 72]
    assert len(course["prerequisite_variants"]) == 2


@pytest.mark.parametrize("params", [{}, {"program_id": ""}])
def test_required_program_query_returns_validation_detail(client, params):
    response = client.get("/courses", params=params)
    assert response.status_code == 422
    assert isinstance(response.json()["detail"], list)
    assert response.json()["detail"][0]["loc"] == ["query", "program_id"]


@pytest.mark.parametrize("program_id", ["unknown", "../toan_hoc_7460101_2022", r"..\toan_hoc_7460101_2022", str(DATA_ROOT / "toan_hoc_7460101_2022")])
def test_unknown_program_and_paths_return_404(client, program_id):
    response = client.get("/courses", params={"program_id": program_id})
    assert response.status_code == 404
    assert response.json() == {"detail": f"Không tìm thấy chương trình: {program_id}"}


@pytest.mark.parametrize("endpoint", ["/programs", "/courses"])
@pytest.mark.parametrize("failure", ["missing", "json", "schema", "root"])
def test_catalog_failures_return_503_without_internal_paths(client, catalog_root, endpoint, failure):
    program_id = "toan_hoc_7460101_2022"
    path = catalog_root / program_id / "courses.json"
    if failure == "missing":
        path.unlink()
    elif failure == "json":
        path.write_text("{", encoding="utf-8")
    elif failure == "schema":
        path.write_text(json.dumps({"wrong": "shape"}), encoding="utf-8")
    else:
        shutil.rmtree(catalog_root)
    response = client.get(endpoint, params={"program_id": program_id})
    assert response.status_code == 503
    assert response.json() == {"detail": main.CATALOG_UNAVAILABLE}
    assert str(catalog_root) not in response.text


def test_empty_catalog_root_returns_empty_program_list(client, catalog_root):
    for directory in catalog_root.iterdir():
        shutil.rmtree(directory)
    response = client.get("/programs")
    assert response.status_code == 200
    assert response.json() == []


def test_empty_course_list_is_valid_response(client, catalog_root):
    program_id = "toan_hoc_7460101_2022"
    (catalog_root / program_id / "courses.json").write_text("[]", encoding="utf-8")
    response = client.get("/courses", params={"program_id": program_id})
    assert response.status_code == 200
    assert response.json() == []
    program = next(item for item in client.get("/programs").json() if item["program_id"] == program_id)
    assert program["course_count"] == 0


def test_openapi_declares_catalog_response_models_and_errors(client):
    schema = client.get("/openapi.json").json()
    for path, model, errors in [
        ("/programs", "ProgramResponse", {"503"}),
        ("/courses", "CourseResponse", {"404", "422", "503"}),
    ]:
        operation = schema["paths"][path]["get"]
        assert operation["tags"] == ["Catalog"]
        response = operation["responses"]["200"]["content"]["application/json"]["schema"]
        assert response["type"] == "array"
        assert response["items"]["$ref"] == f"#/components/schemas/{model}"
        assert errors <= operation["responses"].keys()
    parameter, = schema["paths"]["/courses"]["get"]["parameters"]
    assert parameter["required"] is True
    assert parameter["schema"]["minLength"] == 1
