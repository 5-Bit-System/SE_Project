"""Tests for F2 group course listing (Issue #174).

Verifies that inquiries asking for courses in a specific curriculum group
return structured course lists grounded in F2 data rather than the legacy refusal.
"""

from __future__ import annotations

import pytest

from app.schemas.hus import HUSQuestion
from app.services.hus_service import get_hus_answerer


@pytest.fixture(scope="module")
def answerer():
    return get_hus_answerer()


def test_group_course_listing_data_science_group_ii(answerer):
    """Querying group II in Data Science returns courses in Group II."""
    q = HUSQuestion(
        question="nhóm II gồm những môn học nào?",
        major="data_science",
        version="QD3569-2023",
    )
    ans = answerer.answer(q)
    assert ans.status == "answered"
    assert "Nhóm II" in ans.reply
    assert "HIS1056" in ans.reply
    assert "Cơ sở văn hóa Việt Nam" in ans.reply
    assert any(c.dataset == "f2" for c in ans.citations)
    # Must NOT contain the old refusal string
    assert "chưa hỗ trợ danh sách học phần theo nhóm" not in ans.reply


def test_group_course_listing_subgroup_v_2_1(answerer):
    """Querying sub-group V.2.1 in Data Science returns software skill electives."""
    q = HUSQuestion(
        question="danh sách môn trong nhóm V.2.1",
        major="data_science",
        version="QD3569-2023",
    )
    ans = answerer.answer(q)
    assert ans.status == "answered"
    assert "V.2.1" in ans.reply
    assert any(c.dataset == "f2" for c in ans.citations)


def test_group_course_listing_computer_science_group_iv(answerer):
    """Querying group IV in Computer Science returns required major courses."""
    q = HUSQuestion(
        question="nhóm IV gồm các môn nào?",
        major="computer_science",
        version="QD3568-2023",
    )
    ans = answerer.answer(q)
    assert ans.status == "answered"
    assert "Nhóm IV" in ans.reply
    assert any(c.dataset == "f2" for c in ans.citations)


def test_group_course_listing_mathematics_group_i(answerer):
    """Querying group I in Mathematics returns general education courses."""
    q = HUSQuestion(
        question="danh sách môn học nhóm I",
        major="mathematics",
        version="QD3565-2023",
    )
    ans = answerer.answer(q)
    assert ans.status == "answered"
    assert "Nhóm I" in ans.reply
    assert any(c.dataset == "f2" for c in ans.citations)


def test_group_course_listing_unknown_group_returns_clean_rejection(answerer):
    """Querying a nonexistent group returns clean missing info/clarification."""
    q = HUSQuestion(
        question="danh sách môn trong nhóm X.9.9",
        major="data_science",
        version="QD3569-2023",
    )
    ans = answerer.answer(q)
    assert ans.status in ("needs_clarification", "no_information")
    assert "Không có nhóm này" in ans.reply or "Cần một mã nhóm thống nhất" in ans.reply


def test_group_course_listing_cross_major_isolation(answerer):
    """Courses from Mathematics must not bleed into Data Science responses."""
    q_ds = HUSQuestion(
        question="nhóm II gồm những môn nào?",
        major="data_science",
        version="QD3569-2023",
    )
    ans_ds = answerer.answer(q_ds)
    # HIS1056 is in DS group II
    assert "HIS1056" in ans_ds.reply
    # Verify citations strictly point to Data Science curriculum
    for citation in ans_ds.citations:
        assert citation.dataset == "f2"
        assert "locator" in citation.model_dump()


def test_group_course_listing_required_major_group_v_1(answerer):
    """Group V.1 matches required major courses in Data Science."""
    q = HUSQuestion(
        question="danh sách môn học nhóm V.1",
        major="data_science",
        version="QD3569-2023",
    )
    ans = answerer.answer(q)
    assert ans.status == "answered"
    assert "Nhóm V.1" in ans.reply
    assert "Danh sách học phần thuộc nhóm:" in ans.reply
    assert ans.facts["value"]["course_count"] > 5


def test_group_course_listing_math_informatics_group_i(answerer):
    """Querying group I in Mathematics & Informatics succeeds with valid course list."""
    q = HUSQuestion(
        question="nhóm I gồm các môn học nào?",
        major="mathematics_informatics",
        version="QD3567-2023",
    )
    ans = answerer.answer(q)
    assert ans.status == "answered"
    assert "Nhóm I" in ans.reply
    assert ans.facts["value"]["course_count"] > 0

