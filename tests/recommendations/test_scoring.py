"""Tests for modular course scoring: pref_fit_score, transcript_need_score, and blending."""

import pytest

from app.models import Course, RankingWeights, StructuredPreference
from app.recommendation.scoring import (
    gaussian_level_match,
    pref_fit_score,
)


def test_gaussian_level_match_exact_and_decay():
    # Exact match gives 1.0
    assert gaussian_level_match("moderate", "moderate", "workload") == pytest.approx(1.0)
    assert gaussian_level_match("moderate", "moderate", "difficulty") == pytest.approx(1.0)

    # 1-level difference decays smoothly (~0.6065 for sigma=1.0)
    score_1diff = gaussian_level_match("light", "moderate", "workload")
    assert 0.60 <= score_1diff <= 0.61
    assert 0.60 <= gaussian_level_match("easy", "moderate", "difficulty") <= 0.61

    # 2-level difference decays further (~0.1353 for sigma=1.0)
    score_2diff = gaussian_level_match("light", "heavy", "workload")
    assert 0.13 <= score_2diff <= 0.14
    assert 0.13 <= gaussian_level_match("easy", "advanced", "difficulty") <= 0.14
    assert score_1diff > score_2diff > 0.0

    # None or unknown returns 0.0
    assert gaussian_level_match(None, "moderate", "workload") == 0.0
    assert gaussian_level_match("moderate", None, "workload") == 0.0
    assert gaussian_level_match("unknown", "moderate", "workload") == 0.0


def test_pref_fit_score_topic_career_and_gaussian():
    course = Course(
        code="CS101",
        name="Lập trình web và AI",
        credits=3,
        block="elective",
        topics=["web_development", "machine_learning"],
        career_paths=["software_engineer"],
        difficulty="moderate",
        workload="moderate",
        orientation="practice",
        source_status="verified",
        prerequisite_status="verified",
    )

    # Match specified preference fields
    pref_full = StructuredPreference(
        interest_topics=["web_development", "machine_learning"],
        career_paths=["software_engineer"],
        difficulty="moderate",
        workload="moderate",
        orientation="practice",
    )
    score_full = pref_fit_score(course, pref_full)
    assert 0.70 <= score_full <= 0.72

    # If ranking weights only consider matched dimensions, score reaches 1.0
    custom_weights = RankingWeights(
        topic=0.6,
        career=0.1,
        difficulty=0.1,
        workload=0.1,
        orientation=0.1,
        keyword=0.0,
        course_type=0.0,
    )
    assert pref_fit_score(course, pref_full, weights=custom_weights) == pytest.approx(1.0)

    # Partial match with Gaussian workload decay
    pref_partial = StructuredPreference(
        interest_topics=["web_development"],
        difficulty="easy",  # 1 step difference from moderate
        workload="light",  # 1 step difference from moderate
    )
    score_partial = pref_fit_score(course, pref_partial)
    assert 0.0 < score_partial < score_full
    assert 0.4 <= score_partial <= 0.8


def test_transcript_need_score_retake_dag_and_required():
    from app.recommendation.scoring import transcript_need_score

    # Setup catalog courses for DAG dependency check
    course_foundation = Course(
        code="MAT101",
        name="Giải tích cơ sở",
        credits=4,
        block="required",
        prerequisites=[],
        source_status="verified",
        prerequisite_status="verified",
    )
    course_dep1 = Course(
        code="MAT102",
        name="Giải tích 2",
        credits=4,
        block="required",
        prerequisites=[["MAT101"]],
        source_status="verified",
        prerequisite_status="verified",
    )
    course_dep2 = Course(
        code="MAT103",
        name="Phương trình vi phân",
        credits=3,
        block="elective",
        prerequisites=[["MAT101"]],
        source_status="verified",
        prerequisite_status="verified",
    )
    course_leaf = Course(
        code="ENG101",
        name="Tiếng Anh chuyên ngành",
        credits=2,
        block="elective",
        prerequisites=[],
        source_status="verified",
        prerequisite_status="verified",
    )
    catalog_courses = [course_foundation, course_dep1, course_dep2, course_leaf]

    # 1. Foundation course unlocks MAT102 & MAT103 -> higher DAG score than leaf
    score_foundation = transcript_need_score(
        course_foundation,
        catalog_courses=catalog_courses,
        failed_course_codes=set(),
    )
    score_leaf = transcript_need_score(
        course_leaf,
        catalog_courses=catalog_courses,
        failed_course_codes=set(),
    )
    assert score_foundation > score_leaf
    assert score_foundation >= 0.5

    # 2. Retake of a failed course gets prioritized
    score_retake = transcript_need_score(
        course_leaf,
        catalog_courses=catalog_courses,
        failed_course_codes={"ENG101"},
    )
    assert score_retake > score_leaf
    assert score_retake >= 0.4



def test_combine_scores_alpha_blending():
    from app.recommendation.scoring import combine_scores

    pref = 0.8
    need = 0.4

    # Balanced alpha=0.5
    assert combine_scores(pref, need, alpha=0.5) == pytest.approx(0.6)

    # Preference-oriented alpha=0.7
    assert combine_scores(pref, need, alpha=0.7) == pytest.approx(0.68)

    # Progress/graduation-oriented alpha=0.3
    assert combine_scores(pref, need, alpha=0.3) == pytest.approx(0.52)

    # Boundary alpha
    assert combine_scores(pref, need, alpha=1.0) == pytest.approx(pref)
    assert combine_scores(pref, need, alpha=0.0) == pytest.approx(need)


def test_softmax_probabilities_properties():
    from app.recommendation.scoring import softmax_probabilities

    # 1. Test with list
    scores = [0.2, 0.5, 0.8]
    probs = softmax_probabilities(scores, temperature=1.0)
    assert sum(probs) == pytest.approx(1.0)
    assert probs[2] > probs[1] > probs[0]

    # 2. Test with dict (course_code -> score)
    scores_dict = {"CS101": 0.8, "CS102": 0.6, "CS103": 0.3}
    probs_dict = softmax_probabilities(scores_dict, temperature=1.0)
    assert isinstance(probs_dict, dict)
    assert sum(probs_dict.values()) == pytest.approx(1.0)
    assert probs_dict["CS101"] > probs_dict["CS102"] > probs_dict["CS103"]

    # 3. Empty or single element
    assert softmax_probabilities([]) == []
    assert softmax_probabilities([0.5]) == [1.0]

    # 4. Numerical stability with large scores
    large_scores = [1000.0, 1001.0, 1002.0]
    large_probs = softmax_probabilities(large_scores)
    assert sum(large_probs) == pytest.approx(1.0)
    assert large_probs[2] > large_probs[1] > large_probs[0]



def test_score_course_backward_compatibility_and_dual_mode():
    from app.recommendation.scoring import score_course

    course = Course(
        code="CS201",
        name="Cơ sở dữ liệu",
        credits=3,
        block="required",
        topics=["databases"],
        difficulty="moderate",
        workload="moderate",
        source_status="verified",
        prerequisite_status="verified",
    )
    pref = StructuredPreference(
        interest_topics=["databases"],
        difficulty="moderate",
        workload="moderate",
    )

    # 1. Backward compatible mode (alpha=None)
    score_compat = score_course(course, pref)
    assert 0.4 <= score_compat <= 1.0

    # 2. Dual mode with alpha=0.5 blending
    score_dual = score_course(
        course,
        pref,
        catalog_courses=[course],
        failed_course_codes={"CS201"},
        alpha=0.5,
    )
    assert 0.0 <= score_dual <= 1.0
