from fastapi.testclient import TestClient

from app.catalog import list_catalogs
from app.main import app
from app.models import Catalog, ChoiceGroup, Course, Program, RecommendationRequest
from app.rules import eligible_courses
from app.services.recommendation_service import recommend


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


def test_recommendation_bundle_consumes_choice_quota_without_unlocking_prerequisites():
    catalog = sample_catalog()
    catalog.courses.extend([
        Course(code="F", name="Lựa chọn thay thế", credits=3, block="elective",
               choice_group_ids=["elective"]),
        Course(code="G", name="Môn sau E", credits=3, block="required", prerequisites=[["E"]]),
    ])

    class AlternativesFirst:
        def rank(self, candidates, goal):
            return ["E", "F", "G", "A"]

    response = recommend(catalog, RecommendationRequest(program_id="demo", max_credits=18),
                         ranker=AlternativesFirst())
    assert [course.code for course in response.recommendations] == ["E", "A"]
    # All alternatives remain eligible individually; selection is a separate constraint.
    assert response.eligible_count == 3


def test_group_can_take_multiple_courses_until_required_credits_are_reached():
    catalog = sample_catalog()
    catalog.program.choice_groups[0].required_credits = 6
    catalog.courses.extend([
        Course(code=code, name=code, credits=3, block="elective", choice_group_ids=["elective"])
        for code in ["F", "G"]
    ])
    response = recommend(catalog, RecommendationRequest(program_id="demo", max_credits=18))
    assert {c.code for c in response.recommendations} == {"A", "E", "F"}
    response = recommend(catalog, RecommendationRequest(program_id="demo", max_credits=18,
                                                        passed_course_codes=["E"]))
    assert {c.code for c in response.recommendations} == {"A", "F"}


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
    assert response.json()["recommendations"]
    allowed = {course["code"] for course in client.get("/courses", params={"program_id": "toan_hoc_7460101_2022"}).json()}
    assert all(course["code"] in allowed for course in response.json()["recommendations"])
    assert response.json()["warnings"]
