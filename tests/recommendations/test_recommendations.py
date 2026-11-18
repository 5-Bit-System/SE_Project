
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
    # Strict eligibility keeps NLP/CV blocked while MAT3533 is not passed.
    strict = eligible_courses(khmtt, set(passed), 15)
    strict_codes = {c.code for c in strict}
    assert "MAT3533" in strict_codes
    assert "MAT3561E" not in strict_codes and "MAT3562E" not in strict_codes

    # Sinh viên bị điểm F môn MAT3533 (Học máy) -> kỳ tới ưu tiên học lại MAT3533;
    # môn nối tiếp chỉ được xếp nếu đi cùng MAT3533 trong cùng kỳ.
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
    for follow in ("MAT3561E", "MAT3562E"):
        if follow in codes:
            item = next(r for r in res.recommendations if r.code == follow)
            assert any("MAT3533" in reason for reason in item.eligibility_reason)
    retake_item = next(r for r in res.recommendations if r.code == "MAT3533")
    assert retake_item.is_retake is True
    assert any("điểm F" in sig for sig in retake_item.transcript_signals)
    assert 13 <= res.selected_credits <= 17

    # Ngân sách chỉ đủ 1 môn (3 TC) -> không bao giờ xếp NLP/CV đứng lẻ không có MAT3533.
    tight = recommend(
        khmtt,
        RecommendationRequest(
            program_id=khmtt.program.program_id,
            passed_course_codes=passed,
            failed_course_codes=["MAT3533"],
            max_credits=3,
            credit_tolerance=0,
            limit=5,
            goal="xử lí ngôn ngữ tự nhiên thị giác máy tính",
        ),
    )
    tight_codes = [r.code for r in tight.recommendations]
    assert "MAT3561E" not in tight_codes and "MAT3562E" not in tight_codes


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


def test_thesis_is_heavily_penalized_when_not_in_final_semester():
    from app.models import GraduationPath, GraduationSelection, RankingWeights, StructuredPreference
    from app.recommendation.scoring import compute_transcript_context, transcript_need_score

    thesis = Course(
        code="MAT4080",
        name="Khóa luận tốt nghiệp",
        credits=7,
        block="graduation",
        requirement_type="graduation",
        graduation_path_ids=["V.3.1"],
        topics=["machine_learning"],
        prerequisite_status="verified",
        source_status="verified",
    )
    replacement = Course(
        code="MAT1203",
        name="Phân tích và thiết kế hệ thống thông tin",
        credits=4,
        block="graduation",
        requirement_type="graduation",
        graduation_path_ids=["V.3.2"],
        topics=["software_engineering"],
        prerequisite_status="verified",
        source_status="verified",
    )
    normals = [
        Course(
            code=f"MAT30{i}",
            name=f"Học phần chuyên ngành {i}",
            credits=3 if i % 2 else 4,
            block="major",
            requirement_type="required",
            topics=["machine_learning"] if i == 1 else ["data_science"],
            prerequisite_status="verified",
            source_status="verified",
        )
        for i in range(1, 7)
    ]
    cat = Catalog(
        program=Program(
            program_id="demo_thesis",
            name="Demo KHMTTT",
            total_credits=28,
            catalog_status="verified",
            source_file="synthetic",
            source_pages="none",
            graduation_selection=GraduationSelection(
                mode="exactly_one_path",
                required_credits=7,
                paths=[
                    GraduationPath(id="V.3.1", name="Khóa luận tốt nghiệp", course_codes=["MAT4080"]),
                    GraduationPath(id="V.3.2", name="Các học phần thay thế", course_codes=["MAT1203"]),
                ],
            ),
        ),
        courses=[thesis, replacement, *normals],
    )

    pref = StructuredPreference(interest_topics=["machine_learning"])
    early_ctx = compute_transcript_context(
        cat, set(), selected_graduation_path_id="V.3.1", target_remaining_terms=3
    )
    early_score, early_signals = transcript_need_score(thesis, early_ctx)
    assert early_score <= 0.05
    assert any("kỳ cuối" in sig and "3 học kỳ" in sig for sig in early_signals)

    rep_ctx = compute_transcript_context(
        cat, set(), selected_graduation_path_id="V.3.2", target_remaining_terms=3
    )
    rep_score, _ = transcript_need_score(replacement, rep_ctx)
    assert rep_score >= 0.30

    # Across Balanced, Graduation, and Direction weights, early thesis is excluded both when
    # graduation is far away (terms=3) and when transcript still has 0/28 TC (even if terms=1).
    for terms in (3, 1):
        for weights in (
            RankingWeights(topic=0.245, keyword=0.14, course_type=0.245, workload=0.07, orientation=0.1, difficulty=0.1, career=0.1),
            RankingWeights(topic=0.105, keyword=0.105, course_type=0.455, workload=0.035, orientation=0.1, difficulty=0.1, career=0.1),
            RankingWeights(topic=0.455, keyword=0.175, course_type=0.035, workload=0.035, orientation=0.1, difficulty=0.1, career=0.1),
        ):
            early_res = recommend(
                cat,
                RecommendationRequest(
                    program_id="demo_thesis",
                    max_credits=16,
                    credit_tolerance=2,
                    target_remaining_terms=terms,
                    selected_graduation_path_id="V.3.1",
                    preference=pref,
                    ranking_weights=weights,
                ),
            )
            assert "MAT4080" not in [item.code for item in early_res.recommendations]
            assert any("tạm hoãn MAT4080" in w for w in early_res.warnings)

    # When genuinely in final semester (17/28 TC passed, only MAT306 4TC + MAT4080 7TC remaining),
    # thesis is NOT deferred and gets recommended.
    final_res = recommend(
        cat,
        RecommendationRequest(
            program_id="demo_thesis",
            passed_course_codes=["MAT301", "MAT302", "MAT303", "MAT304", "MAT305"],
            max_credits=16,
            credit_tolerance=2,
            target_remaining_terms=1,
            selected_graduation_path_id="V.3.1",
            preference=pref,
        ),
    )
    assert "MAT4080" in [item.code for item in final_res.recommendations]


def test_khmtt_thesis_readiness_gate_across_scenarios():
    import json

    from app.config import PROJECT_ROOT
    from app.models import RankingWeights
    from app.recommendation.scoring import is_thesis_course
    from database.hus_db.catalog_builder import build_catalogs

    bundle = json.loads((PROJECT_ROOT / "database/data/hus_source.json").read_text(encoding="utf-8"))
    cats = {c.program.program_id: c for c in build_catalogs(bundle)}
    khmtt = cats["khmtt_7480113qtd_2022"]

    # Replacement graduation courses are never treated as thesis.
    for code in ("MAT1203", "MAT3377"):
        course = next(c for c in khmtt.courses if c.code == code)
        assert not is_thesis_course(course)
    assert is_thesis_course(next(c for c in khmtt.courses if c.code == "MAT4080"))

    req_minus_two = [
        c.code
        for c in khmtt.courses
        if c.requirement_type == "required"
        and c.counted_in_total
        and c.code not in {"MAT3374", "MAT3373E"}
    ]
    # 107/129 TC earned -> 22 TC remaining (MAT3374 3TC, MAT3373E 3TC, 9TC V.2.2 electives, MAT4080 7TC).
    passed_107 = [
        *req_minus_two,
        "FLF1107",
        "HUS1021",
        "HUS1022",
        "MAT1208",
        "MAT3519",
        "MAT2034",
    ]
    variants = (
        RankingWeights(topic=0.245, keyword=0.14, course_type=0.245, workload=0.07, orientation=0.1, difficulty=0.1, career=0.1),
        RankingWeights(topic=0.105, keyword=0.105, course_type=0.455, workload=0.035, orientation=0.1, difficulty=0.1, career=0.1),
        RankingWeights(topic=0.455, keyword=0.175, course_type=0.035, workload=0.035, orientation=0.1, difficulty=0.1, career=0.1),
    )
    for terms in (3, 1, None):
        for weights in variants:
            res = recommend(
                khmtt,
                RecommendationRequest(
                    program_id=khmtt.program.program_id,
                    passed_course_codes=passed_107,
                    max_credits=20,
                    credit_tolerance=2,
                    target_remaining_terms=terms,
                    selected_graduation_path_id="V.3.1",
                    ranking_weights=weights,
                ),
            )
            codes = [item.code for item in res.recommendations]
            assert "MAT4080" not in codes
            assert {"MAT3374", "MAT3373E"} <= set(codes)
            assert res.selected_credits == 15
            assert any("tạm hoãn MAT4080" in w for w in res.warnings)

    # Replacement path V.3.2 is NOT deferred as thesis even at 107/129 TC.
    res_v32 = recommend(
        khmtt,
        RecommendationRequest(
            program_id=khmtt.program.program_id,
            passed_course_codes=[*passed_107, "MAT3374", "MAT3373E"],
            max_credits=20,
            credit_tolerance=2,
            target_remaining_terms=1,
            selected_graduation_path_id="V.3.2",
        ),
    )
    assert "MAT1203" in [item.code for item in res_v32.recommendations]

    # True final semester: 119/129 TC earned (1 V.2.2 elective 3TC + MAT4080 7TC left).
    all_req = [c.code for c in khmtt.courses if c.requirement_type == "required" and c.counted_in_total]
    passed_119 = [*all_req, "FLF1107", "HUS1021", "HUS1022", "MAT1208", "MAT3519", "MAT2034", "MAT3148", "MAT3538"]
    final_119 = recommend(
        khmtt,
        RecommendationRequest(
            program_id=khmtt.program.program_id,
            passed_course_codes=passed_119,
            max_credits=20,
            credit_tolerance=2,
            target_remaining_terms=1,
            selected_graduation_path_id="V.3.1",
        ),
    )
    assert "MAT4080" in [item.code for item in final_119.recommendations]
    assert final_119.selected_credits == 10

    # True final semester: 122/129 TC earned (only MAT4080 7TC left).
    passed_122 = [*passed_119, "MAT3561E"]
    final_122 = recommend(
        khmtt,
        RecommendationRequest(
            program_id=khmtt.program.program_id,
            passed_course_codes=passed_122,
            max_credits=20,
            credit_tolerance=2,
            target_remaining_terms=1,
            selected_graduation_path_id="V.3.1",
        ),
    )
    assert [item.code for item in final_122.recommendations] == ["MAT4080"]
    assert final_122.selected_credits == 7


def test_same_semester_co_enrollment_khmtt_107_and_constraints():
    import json

    from app.config import PROJECT_ROOT
    from app.models import RankingWeights
    from app.rules import evaluate_eligibility
    from database.hus_db.catalog_builder import build_catalogs

    bundle = json.loads((PROJECT_ROOT / "database/data/hus_source.json").read_text(encoding="utf-8"))
    khmtt = next(c for c in build_catalogs(bundle) if c.program.program_id == "khmtt_7480113qtd_2022")

    # 107/129 TC earned: missing MAT3374 (3), MAT1207 (3, prereq MAT3374), MAT3373E (3),
    # 6 TC of V.2.2 electives (e.g. MAT3538, MAT3561E), and MAT4080 (7 TC graduation thesis).
    req_minus_three = [
        c.code
        for c in khmtt.courses
        if c.requirement_type == "required"
        and c.counted_in_total
        and c.code not in {"MAT3374", "MAT1207", "MAT3373E"}
    ]
    passed_107 = [
        *req_minus_three,
        "FLF1107",
        "HUS1021",
        "HUS1022",
        "MAT1208",
        "MAT3519",
        "MAT2034",
        "MAT3148",
    ]

    # /eligibility stays strict: MAT1207 remains blocked until MAT3374 is completed.
    strict = evaluate_eligibility(
        khmtt, set(passed_107), max_credits=22, selected_graduation_path_id="V.3.1"
    )
    assert "MAT3374" in {c.code for c in strict.eligible_courses}
    assert "MAT1207" not in {c.code for c in strict.eligible_courses}
    assert "MAT1207" in {b.code for b in strict.blocked_courses}

    variants = (
        RankingWeights(topic=0.245, keyword=0.14, course_type=0.245, workload=0.07, orientation=0.1, difficulty=0.1, career=0.1),
        RankingWeights(topic=0.105, keyword=0.105, course_type=0.455, workload=0.035, orientation=0.1, difficulty=0.1, career=0.1),
        RankingWeights(topic=0.455, keyword=0.175, course_type=0.035, workload=0.035, orientation=0.1, difficulty=0.1, career=0.1),
    )
    for terms in (2, 1, None):
        for weights in variants:
            res = recommend(
                khmtt,
                RecommendationRequest(
                    program_id=khmtt.program.program_id,
                    passed_course_codes=passed_107,
                    max_credits=20,
                    credit_tolerance=2,
                    target_remaining_terms=terms,
                    selected_graduation_path_id="V.3.1",
                    ranking_weights=weights,
                    limit=20,
                ),
            )
            codes = [item.code for item in res.recommendations]
            assert "MAT4080" not in codes
            assert {"MAT3374", "MAT1207", "MAT3373E"} <= set(codes)
            assert res.selected_credits == 15
            assert any("tạm hoãn MAT4080" in w for w in res.warnings)
            mat1207 = next(item for item in res.recommendations if item.code == "MAT1207")
            assert any("cùng kỳ" in r and "MAT3374" in r for r in mat1207.eligibility_reason)
            assert not any("đã thỏa các prerequisite" in r for r in mat1207.eligibility_reason)
            assert any("MAT3374" in s for s in mat1207.transcript_signals)
            assert res.plan_explanation is not None
            assert "MAT1207" in res.plan_explanation.bundle_rationale
            assert "MAT3374" in res.plan_explanation.bundle_rationale

    # Next semester (122/129 TC after passing those 5 courses) recommends MAT4080 (7 TC).
    passed_122 = [*passed_107, "MAT3374", "MAT1207", "MAT3373E", "MAT3538", "MAT3561E"]
    final_res = recommend(
        khmtt,
        RecommendationRequest(
            program_id=khmtt.program.program_id,
            passed_course_codes=passed_122,
            max_credits=20,
            credit_tolerance=2,
            target_remaining_terms=1,
            selected_graduation_path_id="V.3.1",
            limit=20,
        ),
    )
    assert [item.code for item in final_res.recommendations] == ["MAT4080"]
    assert final_res.selected_credits == 7

    # Tight budget (max_credits=3, credit_tolerance=0): MAT1207 must NEVER be picked alone.
    tight = recommend(
        khmtt,
        RecommendationRequest(
            program_id=khmtt.program.program_id,
            passed_course_codes=passed_107,
            max_credits=3,
            credit_tolerance=0,
            selected_graduation_path_id="V.3.1",
            goal="công nghệ phần mềm",
            limit=5,
        ),
    )
    assert tight.selected_credits <= 3
    assert "MAT1207" not in [item.code for item in tight.recommendations]


def test_co_enrollment_bnb_optimal_when_dependent_scores_higher_and_blocks_unsafe():
    from app.models import GraduationPath, GraduationSelection, StructuredPreference

    # Dependent MAT1207 scores much higher than prerequisite MAT3374, while X1/X2 score in between.
    cat = Catalog(
        program=Program(
            program_id="co_bnb",
            name="Co-enrollment B&B",
            total_credits=30,
            catalog_status="verified",
            source_file="synthetic",
            source_pages="none",
            choice_groups=[ChoiceGroup(id="g1", name="Group 1", required_credits=3)],
            graduation_selection=GraduationSelection(
                mode="exactly_one_path",
                required_credits=7,
                paths=[GraduationPath(id="P1", name="Thesis", course_codes=["THESIS"])],
            ),
        ),
        courses=[
            Course(
                code="MAT3374", name="Thực tập", credits=3, block="major",
                requirement_type="elective", topics=["databases"],
                prerequisite_status="verified", source_status="verified",
            ),
            Course(
                code="MAT1207", name="Công nghệ phần mềm", credits=3, block="major",
                requirement_type="required", prerequisites=[["MAT3374"]],
                topics=["machine_learning"], career_paths=["ai_engineer"],
                prerequisite_status="verified", source_status="verified",
            ),
            Course(
                code="X1", name="Độc lập 1", credits=3, block="elective",
                requirement_type="elective", choice_group_ids=["g1"],
                topics=["mathematics"], prerequisite_status="verified", source_status="verified",
            ),
            Course(
                code="X2", name="Độc lập 2", credits=3, block="elective",
                requirement_type="elective", choice_group_ids=["g1"],
                topics=["mathematics"], prerequisite_status="verified", source_status="verified",
            ),
            Course(
                code="UNVER_DEP", name="Chưa xác minh nguồn", credits=3, block="major",
                prerequisites=[["MAT3374"]], prerequisite_status="verified", source_status="draft_unverified",
            ),
            Course(
                code="LOOP1", name="Vòng 1", credits=3, block="major",
                prerequisites=[["LOOP2"]], prerequisite_status="verified", source_status="verified",
            ),
            Course(
                code="LOOP2", name="Vòng 2", credits=3, block="major",
                prerequisites=[["LOOP1"]], prerequisite_status="verified", source_status="verified",
            ),
            Course(
                code="THESIS", name="Khóa luận tốt nghiệp", credits=7, block="graduation",
                requirement_type="graduation", graduation_path_ids=["P1"],
                prerequisites=[["MAT3374"]], prerequisite_status="verified", source_status="verified",
            ),
            Course(
                code="AFTER_THESIS", name="Sau khóa luận", credits=3, block="major",
                prerequisites=[["THESIS"]], prerequisite_status="verified", source_status="verified",
            ),
        ],
    )
    pref = StructuredPreference(interest_topics=["machine_learning"], career_paths=["ai_engineer"])

    # With 6 TC budget, {MAT3374, MAT1207} beats {MAT3374, X1} or {X1, X2} even though MAT1207 depends on lower-scored MAT3374.
    res6 = recommend(
        cat,
        RecommendationRequest(
            program_id="co_bnb", max_credits=6, credit_tolerance=0,
            target_remaining_terms=3, selected_graduation_path_id="P1",
            preference=pref, limit=5,
        ),
    )
    codes6 = [item.code for item in res6.recommendations]
    assert set(codes6) == {"MAT3374", "MAT1207"}
    assert "UNVER_DEP" not in codes6
    assert "LOOP1" not in codes6 and "LOOP2" not in codes6
    assert "THESIS" not in codes6 and "AFTER_THESIS" not in codes6

    # With 3 TC budget, MAT1207 CANNOT be picked alone.
    res3 = recommend(
        cat,
        RecommendationRequest(
            program_id="co_bnb", max_credits=3, credit_tolerance=0,
            target_remaining_terms=3, selected_graduation_path_id="P1",
            preference=pref, limit=5,
        ),
    )
    assert "MAT1207" not in [item.code for item in res3.recommendations]
    assert res3.selected_credits == 3
