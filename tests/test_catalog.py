import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.catalog import CatalogError, CatalogNotFoundError, list_catalogs, load_catalog


@pytest.fixture
def catalog_root(tmp_path):
    directory = tmp_path / "demo"
    directory.mkdir()
    program = {
        "program_id": "demo",
        "name": "Ngành thử nghiệm",
        "total_credits": 3,
        "catalog_status": "draft_unverified",
        "source_file": "synthetic",
        "source_pages": "1",
        "choice_groups": [{"id": "elective", "name": "Tự chọn", "required_credits": 3}],
    }
    courses = [{"code": "A", "name": "Nhập môn", "credits": 3, "block": "required"}]
    (directory / "curriculum.json").write_text(json.dumps(program), encoding="utf-8")
    (directory / "courses.json").write_text(json.dumps(courses), encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("filename", ["curriculum.json", "courses.json"])
@pytest.mark.parametrize("loader", [lambda root: load_catalog("demo", root), list_catalogs])
def test_missing_file_is_catalog_error(catalog_root, filename, loader):
    path = catalog_root / "demo" / filename
    path.unlink()
    with pytest.raises(CatalogError, match=filename) as error:
        loader(catalog_root)
    assert isinstance(error.value.__cause__, FileNotFoundError)


@pytest.mark.parametrize("filename", ["curriculum.json", "courses.json"])
def test_malformed_json_reports_file_and_position(catalog_root, filename):
    (catalog_root / "demo" / filename).write_text('{\n"broken": }', encoding="utf-8")
    with pytest.raises(CatalogError, match=filename) as error:
        load_catalog("demo", catalog_root)
    assert "dòng 2" in str(error.value)
    assert "cột 11" in str(error.value)
    assert isinstance(error.value.__cause__, json.JSONDecodeError)


@pytest.mark.parametrize("filename", ["curriculum.json", "courses.json"])
def test_invalid_utf8_is_catalog_error(catalog_root, filename):
    (catalog_root / "demo" / filename).write_bytes(b"\xff")
    with pytest.raises(CatalogError, match=f"UTF-8.*{filename}") as error:
        load_catalog("demo", catalog_root)
    assert isinstance(error.value.__cause__, UnicodeDecodeError)


@pytest.mark.parametrize("filename", ["curriculum.json", "courses.json"])
def test_unreadable_file_is_catalog_error(catalog_root, filename, monkeypatch):
    target = catalog_root / "demo" / filename
    original = Path.read_text

    def read_text(path, *args, **kwargs):
        if path == target:
            raise PermissionError("access denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)
    with pytest.raises(CatalogError, match=filename) as error:
        load_catalog("demo", catalog_root)
    assert isinstance(error.value.__cause__, PermissionError)


@pytest.mark.parametrize(
    "filename,payload",
    [
        ("curriculum.json", None),
        ("curriculum.json", []),
        ("curriculum.json", {}),
        ("courses.json", None),
        ("courses.json", {}),
        ("courses.json", "invalid"),
        ("courses.json", 3),
        ("courses.json", [None]),
        ("courses.json", [{}]),
        ("courses.json", [{"code": "A", "name": "A", "credits": 0, "block": "required"}]),
    ],
)
def test_invalid_schema_is_catalog_error(catalog_root, filename, payload):
    (catalog_root / "demo" / filename).write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CatalogError, match=f"Dữ liệu không hợp lệ.*{filename}"):
        load_catalog("demo", catalog_root)


def test_invalid_program_field_reports_field(catalog_root):
    path = catalog_root / "demo" / "curriculum.json"
    program = json.loads(path.read_text(encoding="utf-8"))
    program["total_credits"] = -1
    path.write_text(json.dumps(program), encoding="utf-8")
    with pytest.raises(CatalogError, match="total_credits"):
        load_catalog("demo", catalog_root)


@pytest.mark.parametrize("invalid_root", ["missing", "file"])
@pytest.mark.parametrize("loader", [lambda root: load_catalog("demo", root), list_catalogs])
def test_invalid_root_is_catalog_error(tmp_path, invalid_root, loader):
    root = tmp_path / invalid_root
    if invalid_root == "file":
        root.write_text("not a directory", encoding="utf-8")
    with pytest.raises(CatalogError, match="thư mục catalog") as error:
        loader(root)
    assert isinstance(error.value.__cause__, OSError)


@pytest.mark.parametrize("program_id", ["unknown", "..", "../demo", "demo/..", r"..\demo"])
def test_free_form_paths_are_rejected(catalog_root, program_id):
    with pytest.raises(CatalogError, match="Không tìm thấy chương trình"):
        load_catalog(program_id, catalog_root)


def test_absolute_path_is_rejected(catalog_root):
    with pytest.raises(CatalogError, match="Không tìm thấy chương trình"):
        load_catalog(str(catalog_root / "demo"), catalog_root)


def test_list_only_loads_directories_in_sorted_order(catalog_root):
    (catalog_root / "notes.txt").write_text("not a program", encoding="utf-8")
    directory = catalog_root / "alpha"
    directory.mkdir()
    for filename in ["curriculum.json", "courses.json"]:
        data = json.loads((catalog_root / "demo" / filename).read_text(encoding="utf-8"))
        if filename == "curriculum.json":
            data["program_id"] = "alpha"
        (directory / filename).write_text(json.dumps(data), encoding="utf-8")
    assert [catalog.program.program_id for catalog in list_catalogs(catalog_root)] == ["alpha", "demo"]


def test_directory_link_outside_root_is_rejected(catalog_root, tmp_path):
    root = tmp_path / "catalogs"
    root.mkdir()
    try:
        (root / "demo").symlink_to(catalog_root / "demo", target_is_directory=True)
    except OSError:
        pytest.skip("Creating directory symlinks is not supported in this environment")
    with pytest.raises(CatalogError, match="Không tìm thấy chương trình"):
        load_catalog("demo", root)
    assert list_catalogs(root) == []


@pytest.mark.parametrize("issue", ["program_id", "duplicate_code", "unknown_group"])
def test_existing_integrity_checks_are_preserved(catalog_root, issue):
    program_path = catalog_root / "demo" / "curriculum.json"
    courses_path = catalog_root / "demo" / "courses.json"
    program = json.loads(program_path.read_text(encoding="utf-8"))
    courses = json.loads(courses_path.read_text(encoding="utf-8"))
    if issue == "program_id":
        program["program_id"] = "other"
        expected = "program_id không khớp"
    elif issue == "duplicate_code":
        courses.append(courses[0].copy())
        expected = "Mã môn trùng"
    else:
        courses[0]["choice_group_ids"] = ["missing"]
        expected = "Nhóm tự chọn không tồn tại"
    program_path.write_text(json.dumps(program), encoding="utf-8")
    courses_path.write_text(json.dumps(courses), encoding="utf-8")
    with pytest.raises(CatalogError, match=expected):
        load_catalog("demo", catalog_root)


def test_valid_catalog_preserves_unicode_metadata_and_does_not_write(catalog_root):
    directory = catalog_root / "demo"
    program_path = directory / "curriculum.json"
    courses_path = directory / "courses.json"
    program = json.loads(program_path.read_text(encoding="utf-8"))
    courses = json.loads(courses_path.read_text(encoding="utf-8"))
    program["source_issues"] = [{"id": "needs_review", "message": "Cần đối chiếu PDF"}]
    courses[0].update({
        "source_rows": [1, 3],
        "hours": None,
        "prerequisite_status": "source_conflict",
        "prerequisite_variants": [[], [["EXTERNAL"]]],
        "external_prerequisite_codes": ["EXTERNAL"],
    })
    program_path.write_text(json.dumps(program, ensure_ascii=False), encoding="utf-8")
    courses_path.write_text(json.dumps(courses, ensure_ascii=False), encoding="utf-8")
    before = {path: path.read_bytes() for path in directory.iterdir()}
    catalog = load_catalog("demo", catalog_root)
    assert catalog.program.name == "Ngành thử nghiệm"
    assert catalog.program.source_issues == program["source_issues"]
    assert catalog.courses[0].name == "Nhập môn"
    assert catalog.courses[0].source_rows == [1, 3]
    assert catalog.courses[0].hours is None
    assert catalog.courses[0].prerequisite_variants == [[], [["EXTERNAL"]]]
    assert catalog.courses[0].external_prerequisite_codes == ["EXTERNAL"]
    assert catalog.program.catalog_status == "draft_unverified"
    assert {path: path.read_bytes() for path in directory.iterdir()} == before


def test_course_validation_error_identifies_item_and_field(catalog_root):
    path = catalog_root / "demo" / "courses.json"
    courses = json.loads(path.read_text(encoding="utf-8"))
    courses.append({"code": "B", "name": "Sai tín chỉ", "credits": -1, "block": "required"})
    path.write_text(json.dumps(courses), encoding="utf-8")
    with pytest.raises(CatalogError, match="courses.json") as error:
        load_catalog("demo", catalog_root)
    assert isinstance(error.value.__cause__, ValidationError)
    assert error.value.__cause__.errors()[0]["loc"] == (1, "credits")


def test_unknown_program_uses_distinct_error_type(catalog_root):
    with pytest.raises(CatalogNotFoundError):
        load_catalog("missing", catalog_root)


@pytest.mark.parametrize("loader", [lambda root: load_catalog("demo", root), list_catalogs])
def test_unreadable_root_keeps_filesystem_cause(catalog_root, monkeypatch, loader):
    original = Path.iterdir

    def iterdir(path):
        if path == catalog_root:
            raise PermissionError("access denied")
        return original(path)

    monkeypatch.setattr(Path, "iterdir", iterdir)
    with pytest.raises(CatalogError, match="thư mục catalog") as error:
        loader(catalog_root)
    assert isinstance(error.value.__cause__, PermissionError)


def test_empty_root_lists_no_catalogs_and_plain_file_is_not_a_program(tmp_path):
    assert list_catalogs(tmp_path) == []
    (tmp_path / "demo").write_text("not a directory", encoding="utf-8")
    assert list_catalogs(tmp_path) == []
    with pytest.raises(CatalogNotFoundError):
        load_catalog("demo", tmp_path)


def test_same_code_in_two_programs_is_loaded_independently(catalog_root):
    other = catalog_root / "other"
    other.mkdir()
    program = json.loads((catalog_root / "demo" / "curriculum.json").read_text(encoding="utf-8"))
    program["program_id"] = "other"
    (other / "curriculum.json").write_text(json.dumps(program), encoding="utf-8")
    (other / "courses.json").write_text(json.dumps([
        {"code": "A", "name": "Môn của ngành khác", "credits": 4, "block": "elective"},
    ]), encoding="utf-8")
    catalogs = list_catalogs(catalog_root)
    assert [catalog.program.program_id for catalog in catalogs] == ["demo", "other"]
    assert [(catalog.courses[0].code, catalog.courses[0].credits) for catalog in catalogs] == [("A", 3), ("A", 4)]
    assert catalogs[0].courses[0].name != catalogs[1].courses[0].name


def test_directory_resolving_outside_root_is_rejected_without_symlink_privileges(catalog_root, monkeypatch):
    directory = catalog_root / "demo"
    original = Path.resolve

    def resolve(path, *args, **kwargs):
        if path == directory:
            return catalog_root.parent / "outside" / "demo"
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    assert list_catalogs(catalog_root) == []
    with pytest.raises(CatalogNotFoundError):
        load_catalog("demo", catalog_root)
