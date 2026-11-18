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
    assert gaussian_level_match("intermediate", "intermediate", "difficulty") == pytest.approx(1.0)

    # 1-level difference decays smoothly (~0.6065 for sigma=1.0)
    score_1diff = gaussian_level_match("light", "moderate", "workload")
    assert 0.60 <= score_1diff <= 0.61

    # 2-level difference decays further (~0.1353 for sigma=1.0)
    score_2diff = gaussian_level_match("light", "heavy", "workload")
    assert 0.13 <= score_2diff <= 0.14
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
        difficulty="intermediate",
        workload="moderate",
        orientation="practice",
        source_status="verified",
        prerequisite_status="verified",
    )

    # Perfect match
    pref_full = StructuredPreference(
        interest_topics=["web_development", "machine_learning"],
        career_paths=["software_engineer"],
        difficulty="intermediate",
        workload="moderate",
        orientation="practice",
    )
    score_full = pref_fit_score(course, pref_full)
    assert score_full == pytest.approx(1.0)

    # Partial match with Gaussian workload decay
    pref_partial = StructuredPreference(
        interest_topics=["web_development"],
        difficulty="introductory",  # 1 step difference from intermediate
        workload="light",  # 1 step difference from moderate
    )
    score_partial = pref_fit_score(course, pref_partial)
    assert 0.0 < score_partial < score_full
    assert 0.4 <= score_partial <= 0.8
