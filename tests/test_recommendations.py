from fastapi.testclient import TestClient

from app.catalog import list_catalogs
from app.main import app
from app.models import Catalog, ChoiceGroup, Course, Program, RecommendationRequest
from app.rules import eligible_courses
from app.service import recommend


def sample_catalog() -> Catalog:
    return Catalog(
        program=Program(
            program_id="demo",
            name="Dữ liệu tổng hợp dùng riêng cho test",
            total_credits=12,
            catalog_status="draft_unverified",
            source_file="synthetic",
            source_pages="none",
            choice_groups=[ChoiceGroup(id="elective", name="Tự chọn", required_credits=3)],
        ),
        courses=[
            Course(code="A", name="Nhập môn", credits=3, block="required"),
            Course(code="B", name="Dữ liệu", credits=3, block="required", prerequisites=[["A"]]),
            Course(code="C", name="AI", credits=3, block="required", prerequisites=[["A", "B"]]),
            Course(code="D", name="Nâng cao", credits=3, block="required", prerequisites=[["A"], ["B"]]),
            Course(code="E", name="Tự chọn", credits=3, block="elective", choice_group_ids=["elective"]),
        ],
    )


def test_all_four_catalogs_are_separate_and_draft():
    catalogs = list_catalogs()
    assert len(catalogs) == 4
    assert len({item.program.program_id for item in catalogs}) == 4
    assert all(item.program.catalog_status == "draft_unverified" for item in catalogs)


def test_prerequisite_and_or_and_group_quota():
    catalog = sample_catalog()
    assert {course.code for course in eligible_courses(catalog, {"A"}, 18)} == {"B", "C", "E"}
    assert {course.code for course in eligible_courses(catalog, {"A", "B", "E"}, 18)} == {"C", "D"}


def test_untrusted_ranker_cannot_add_foreign_or_duplicate_courses():
    class BadRanker:
        def rank(self, candidates, goal):
            return ["FOREIGN", "B", "B", "E", "A"]

    response = recommend(
        sample_catalog(),
        RecommendationRequest(program_id="demo", passed_course_codes=["A"], max_credits=6),
        ranker=BadRanker(),
    )
    codes = [item.code for item in response.recommendations]
    assert codes == ["B", "E"]
    assert sum(item.credits for item in response.recommendations) <= 6


def test_ranker_failure_uses_safe_fallback():
    class BrokenRanker:
        def rank(self, candidates, goal):
            raise TimeoutError()

    response = recommend(sample_catalog(), RecommendationRequest(program_id="demo"), ranker=BrokenRanker())
    assert response.recommendations
    assert any("dự phòng" in warning for warning in response.warnings)


def test_wrong_program_and_unknown_passed_course_are_rejected():
    catalog = sample_catalog()
    for request in [
        RecommendationRequest(program_id="other"),
        RecommendationRequest(program_id="demo", passed_course_codes=["X"]),
    ]:
        try:
            recommend(catalog, request)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid request was accepted")


def test_http_contract():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    assert len(client.get("/programs").json()) == 4
    assert client.get("/courses", params={"program_id": "unknown"}).status_code == 404
    response = client.post("/recommendations", json={"program_id": "toan_hoc_7460101_2022"})
    assert response.status_code == 200
    assert response.json()["recommendations"] == []
    assert response.json()["warnings"]
