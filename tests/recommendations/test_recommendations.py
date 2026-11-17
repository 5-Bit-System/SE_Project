
from app.catalog import list_catalogs
from app.models import Catalog, ChoiceGroup, Course, Program, RecommendationRequest
from app.rules import eligible_courses
from app.services.recommendation_service import recommend


def sample_catalog() -> Catalog:
    return Catalog(
        program=Program(
            program_id="demo",
            name="Dữ liệu tổng hợp dùng riêng cho test",
            total_credits=12,
            catalog_status="verified",
            source_file="synthetic",
            source_pages="none",
            choice_groups=[ChoiceGroup(id="elective", name="Tự chọn", required_credits=3)],
        ),
        courses=[
            Course(code="A", name="Nhập môn", credits=3, block="required", prerequisite_status="verified", source_status="verified"),
            Course(code="B", name="Dữ liệu", credits=3, block="required", prerequisites=[["A"]], prerequisite_status="verified", source_status="verified"),
            Course(code="C", name="AI", credits=3, block="required", prerequisites=[["A", "B"]], prerequisite_status="verified", source_status="verified"),
            Course(code="D", name="Nâng cao", credits=3, block="required", prerequisites=[["A"], ["B"]], prerequisite_status="verified", source_status="verified"),
            Course(code="E", name="Tự chọn", credits=3, block="elective", choice_group_ids=["elective"], prerequisite_status="verified", source_status="verified"),
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


def test_http_contract_does_not_recommend_from_unverified_catalog(verified_client):
    client = verified_client
    assert client.get("/health").json() == {"status": "ok"}
    assert len(client.get("/programs").json()) == 4
    assert client.get("/courses", params={"program_id": "unknown"}).status_code == 404
    response = client.post("/recommendations", json={"program_id": "toan_hoc_7460101_2022"})
    assert response.status_code == 200
    assert response.json()["catalog_status"] == "draft_unverified"
    assert response.json()["eligible_count"] == 0
    assert response.json()["recommendations"] == []
    assert any("Catalog chưa được xác minh" in warning for warning in response.json()["warnings"])


def test_probabilistic_soft_similarity_and_softmax():
    from app.models import RankingWeights, StructuredPreference
    from app.recommendation.scoring import pref_fit_score, softmax_probabilities

    base = Course(
        code="M1",
        name="Học máy",
        credits=3,
        block="major",
        topics=["machine_learning", "data_science"],
        career_paths=["ai_engineer"],
        orientation="theory",
        difficulty="moderate",
        workload="moderate",
        prerequisite_status="verified",
        source_status="verified",
    )
    near = base.model_copy(update={"code": "M2", "difficulty": "advanced", "workload": "heavy", "orientation": "research"})
    far = base.model_copy(update={"code": "M3", "topics": ["cybersecurity"], "difficulty": "easy", "workload": "light", "orientation": "practice"})
    pref = StructuredPreference(
        interest_topics=["machine_learning"],
        orientation="theory",
        difficulty="moderate",
        workload="moderate",
    )
    weights = RankingWeights()
    s_exact = pref_fit_score(base, pref, weights)
    s_near = pref_fit_score(near, pref, weights)
    s_far = pref_fit_score(far, pref, weights)
    assert s_exact > s_near > s_far > 0
    probs = softmax_probabilities([s_exact, s_near, s_far])
    assert abs(sum(probs) - 1.0) < 0.01
    assert probs[0] > probs[1] > probs[2]


def test_credit_band_plus_minus_two_and_hard_cap_distinction():
    cat = Catalog(
        program=Program(
            program_id="band",
            name="Band demo",
            total_credits=30,
            catalog_status="verified",
            source_file="synthetic",
            source_pages="none",
        ),
        courses=[
            Course(
                code=f"C{i}",
                name=f"Môn {i}",
                credits=3,
                block="major",
                topics=["machine_learning"],
                prerequisite_status="verified",
                source_status="verified",
            )
            for i in range(1, 7)
        ],
    )
    # Target 14 TC với toàn môn 3 TC: tối ưu T±2 chọn 5 môn = 15 TC (+1 TC) thay vì 12 TC (-2 TC)
    res_band = recommend(
        cat,
        RecommendationRequest(program_id="band", max_credits=14, limit=10, goal="học máy"),
    )
    assert res_band.selected_credits == 15
    assert sum(r.credits for r in res_band.recommendations) == 15
    assert res_band.target_credits == 14
    assert res_band.credit_tolerance == 2

    # Ràng buộc cứng từ câu chat ("Tối đa 12 tín chỉ") không được vượt 12
    res_hard = recommend(
        cat,
        RecommendationRequest(program_id="band", max_credits=20, limit=10, goal="Tối đa 12 tín chỉ học máy"),
    )
    assert sum(r.credits for r in res_hard.recommendations) <= 12
    assert res_hard.credit_tolerance == 0


def test_khmtt_failed_f_course_is_retake_eligible_and_prioritized():
    import json

    from app.config import PROJECT_ROOT
    from database.hus_db.catalog_builder import build_catalogs

    bundle = json.loads((PROJECT_ROOT / "database/data/hus_source.json").read_text(encoding="utf-8"))
    khmtt = next(c for c in build_catalogs(bundle) if c.program.program_id == "khmtt_7480113qtd_2022")
    passed = [
        "HUS1011", "MAT2505", "MAT2501", "MAT2502", "MAT2400",
        "MAT2323", "MAT3500", "MAT3514", "MAT3507", "MAT1202", "MAT1206E",
    ]
    # Sinh viên bị điểm F môn MAT3533 (Học máy) -> kỳ tới được xếp học lại và chặn NLP/CV
    res = recommend(
        khmtt,
        RecommendationRequest(
            program_id=khmtt.program.program_id,
            passed_course_codes=passed,
            failed_course_codes=["MAT3533"],
            max_credits=15,
            limit=8,
            goal="trí tuệ nhân tạo và học máy",
        ),
    )
    codes = [r.code for r in res.recommendations]
    assert "MAT3533" in codes
    assert "MAT3561E" not in codes and "MAT3562E" not in codes
    retake_item = next(r for r in res.recommendations if r.code == "MAT3533")
    assert retake_item.is_retake is True
    assert any("điểm F" in sig for sig in retake_item.transcript_signals)
    assert 13 <= res.selected_credits <= 17


def test_human_readable_fit_reason_and_group_names():
    from app.models import RankingWeights, StructuredPreference
    from app.recommendation.scoring import (
        compute_transcript_context,
        fit_reason,
        transcript_need_score,
    )
    from app.services.operational_metrics import _fit_category

    course_topic = Course(
        code="MAT3533",
        name="Học máy",
        credits=3,
        block="major",
        topics=["machine_learning"],
        career_paths=["ai_engineer"],
        orientation="research",
        difficulty="moderate",
        workload="light",
        choice_group_ids=["g_major_electives"],
        requirement_type="elective",
        prerequisite_status="verified",
        source_status="verified",
    )
    cat = Catalog(
        program=Program(
            program_id="demo_hr",
            name="Demo",
            total_credits=30,
            catalog_status="verified",
            source_file="synthetic",
            source_pages="none",
            choice_groups=[ChoiceGroup(id="g_major_electives", name="Tự chọn chuyên ngành", required_credits=6)],
        ),
        courses=[course_topic],
    )

    topic_reason = fit_reason(course_topic, StructuredPreference(interest_topics=["machine_learning"]), 0.8)
    assert "Học máy" in topic_reason and "machine_learning" not in topic_reason
    assert _fit_category(topic_reason) == "topic"

    career_reason = fit_reason(course_topic, StructuredPreference(career_paths=["ai_engineer"]), 0.8)
    assert "Kỹ sư Trí tuệ nhân tạo" in career_reason and "ai_engineer" not in career_reason
    assert _fit_category(career_reason) == "career"

    style_reason = fit_reason(
        course_topic,
        StructuredPreference(orientation="theory", difficulty="moderate", workload="light"),
        0.7,
    )
    assert "orientation=" not in style_reason and "mức độ trung bình" in style_reason
    assert _fit_category(style_reason) == "metadata"

    type_reason = fit_reason(course_topic, StructuredPreference(course_type="elective"), 0.5)
    assert "tự chọn" in type_reason and "elective" not in type_reason
    assert _fit_category(type_reason) == "course_type"

    ctx = compute_transcript_context(cat, set())
    _, signals = transcript_need_score(course_topic, ctx)
    assert any("Tự chọn chuyên ngành" in sig and "g_major_electives" not in sig for sig in signals)
    assert RankingWeights() is not None
