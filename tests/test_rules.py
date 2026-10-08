from app.models import Catalog, ChoiceGroup, Course, Program
from app.rules import eligible_courses, explain_catalog, missing_prerequisites


def rules_catalog() -> Catalog:
    return Catalog(
        program=Program(
            program_id="rules_demo",
            name="Fixture kiểm tra luật",
            total_credits=24,
            catalog_status="draft_unverified",
            source_file="synthetic",
            source_pages="none",
            choice_groups=[
                ChoiceGroup(id="elective", name="Tự chọn", required_credits=6),
            ],
        ),
        courses=[
            Course(code="A", name="Nhập môn", credits=3, block="required"),
            Course(code="B", name="Dữ liệu", credits=3, block="required", prerequisites=[["A"]]),
            Course(code="C", name="AI", credits=3, block="required", prerequisites=[["A", "B"]]),
            Course(code="D", name="Nâng cao", credits=3, block="required", prerequisites=[["A"], ["B"]]),
            Course(code="E", name="Tự chọn 1", credits=3, block="elective", choice_group_ids=["elective"]),
            Course(code="F", name="Tự chọn 2", credits=3, block="elective", choice_group_ids=["elective"]),
            Course(code="G", name="Tự chọn 3", credits=3, block="elective", choice_group_ids=["elective"]),
            Course(
                code="X",
                name="Mâu thuẫn nguồn",
                credits=3,
                block="major",
                prerequisites=[["A"]],
                prerequisite_status="source_conflict",
            ),
            Course(
                code="Y",
                name="TT ngoài ngành",
                credits=3,
                block="major",
                prerequisites=[["ZZ9999"]],
                external_prerequisite_codes=["ZZ9999"],
            ),
        ],
    )


def verdict_map(passed: set[str], max_credits: int = 18) -> dict:
    catalog = rules_catalog()
    return {v.course.code: v for v in explain_catalog(catalog, passed, max_credits)}


def rules_of(verdict) -> set[str]:
    return {reason["rule"] for reason in verdict.reasons}


def test_missing_prerequisites_and_or_and_none():
    catalog = rules_catalog()
    by_code = {course.code: course for course in catalog.courses}
    assert missing_prerequisites(by_code["A"], set()) == []
    assert missing_prerequisites(by_code["B"], set()) == [["A"]]
    assert missing_prerequisites(by_code["B"], {"A"}) == []
    assert missing_prerequisites(by_code["C"], {"A"}) == []
    assert missing_prerequisites(by_code["C"], set()) == [["A", "B"]]
    assert missing_prerequisites(by_code["D"], {"A"}) == [["B"]]
    assert missing_prerequisites(by_code["D"], set()) == [["A"], ["B"]]


def test_missing_prerequisite_reason_lists_remaining_groups():
    verdict = verdict_map({"A"})["D"]
    assert not verdict.eligible
    assert rules_of(verdict) == {"missing_prerequisite"}
    reason = verdict.reasons[0]
    assert reason["missing_groups"] == [["B"]]
    # Đã qua A nên nhóm [A, B] đã thỏa, chỉ thiếu [B].
    assert verdict_map({"A"})["C"].eligible


def test_already_passed_and_credit_limit_reasons():
    assert rules_of(verdict_map({"A"})["A"]) == {"already_passed"}
    verdicts = verdict_map(set(), max_credits=2)
    assert "credit_limit" in rules_of(verdicts["B"])


def test_source_conflict_is_reported_even_with_prerequisites_met():
    verdict = verdict_map({"A"})["X"]
    assert not verdict.eligible
    assert rules_of(verdict) == {"source_conflict"}


def test_external_prerequisite_codes_are_flagged():
    verdict = verdict_map(set())["Y"]
    reason = next(r for r in verdict.reasons if r["rule"] == "missing_prerequisite")
    assert reason["external_codes"] == ["ZZ9999"]
    assert "danh mục ngành" in reason["message"]


def test_group_full_after_quota_and_free_before():
    # Nhóm cần 6 TC; E đã qua (3 TC) nên G chưa bị chặn.
    assert verdict_map({"E"})["G"].eligible
    # E + F = 6 TC → nhóm đủ, G bị group_full dù tiên quyết không có gì.
    verdict = verdict_map({"E", "F"})["G"]
    assert not verdict.eligible
    assert rules_of(verdict) == {"group_full"}
    assert verdict.reasons[0]["groups"] == ["elective"]


def test_explain_and_eligible_share_one_verdict_path():
    for passed in (set(), {"A"}, {"A", "B"}, {"E", "F"}, {"A", "B", "E", "F"}):
        catalog = rules_catalog()
        explained = {v.course.code for v in explain_catalog(catalog, passed, 18) if v.eligible}
        eligible = {course.code for course in eligible_courses(catalog, passed, 18)}
        assert explained == eligible
