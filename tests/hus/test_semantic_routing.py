"""Unit tests for semantic intent routing and multi-signal top-k chunk ranking."""

from __future__ import annotations

import pytest

from app.hus.rag_loader import HUSRAGData
from app.hus.retrieval import HUSRAGRetriever, RetrievalHit
from app.hus.semantic_routing import (
    ANCHOR_INTENTS,
    rank_top_k_chunks,
    semantic_question_intent,
)


def test_anchor_intents_cover_all_expected_datasets_and_fields():
    keys = {(dataset, field) for dataset, field, _ in ANCHOR_INTENTS}
    expected = {
        ("f2", "credits"),
        ("f2", "prerequisites"),
        ("f2", "hours"),
        ("f2", "name"),
        ("f2", "program_credits"),
        ("f2", "program_groups"),
        ("f2", "group_rules"),
        ("f1", "introduction"),
        ("f1", "careers"),
        ("f1", "further_study"),
        ("f1", "objectives"),
        ("f3", "content"),
        ("f3", "objectives"),
        ("f3", "suggested_assessment"),
    }
    assert keys == expected
    total_exemplars = sum(len(phrases) for _, _, phrases in ANCHOR_INTENTS)
    assert 60 <= total_exemplars <= 90


@pytest.mark.parametrize(
    ("question", "has_course", "expected_dataset", "expected_field"),
    [
        ("Môn Giải tích 1 này nặng mấy tín vậy?", True, "f2", "credits"),
        ("Tích lũy bao nhiêu tín chỉ khi hoàn thành môn học này?", True, "f2", "credits"),
        ("Cần qua môn gì trước khi đăng ký học phần MAT1101?", True, "f2", "prerequisites"),
        ("Điều kiện bắt buộc để học môn này là phải hoàn thành học phần nào trước?", True, "f2", "prerequisites"),
        ("Thời lượng học trên lớp và thực hành phân bổ bao nhiêu giờ?", True, "f2", "hours"),
        ("Mã học phần MAT1101 tên gọi đầy đủ của mã môn là gì?", True, "f2", "name"),
        ("Toàn khóa học phải tích lũy bao nhiêu tín chỉ?", False, "f2", "program_credits"),
        ("Quy định tín chỉ tự chọn tối thiểu của nhóm kiến thức là gì?", False, "f2", "group_rules"),
        ("Môn học này dạy những kiến thức gì và tóm tắt nội dung các chương?", True, "f3", "content"),
        ("Cách tính điểm và gợi ý kiểm tra giữa kỳ cuối kỳ của môn?", True, "f3", "suggested_assessment"),
        ("Học xong ra trường làm nghề gì và cơ hội việc làm ở đâu?", False, "f1", "careers"),
        ("Cơ hội học lên thạc sĩ tiến sĩ sau đại học như thế nào?", False, "f1", "further_study"),
    ],
)
def test_paraphrased_questions_route_to_expected_intent(
    question: str,
    has_course: bool,
    expected_dataset: str,
    expected_field: str,
):
    dataset, field, score = semantic_question_intent(question, has_course=has_course)
    assert (dataset, field) == (expected_dataset, expected_field)
    assert score >= 0.38


def test_curriculum_framework_structure_vs_general_introduction():
    ds_struct, field_struct, score_struct = semantic_question_intent(
        "Khung chương trình ngành Khoa học dữ liệu chia thành những khối kiến thức nào?",
        has_course=False,
    )
    assert (ds_struct, field_struct) == ("f2", "program_groups")
    assert score_struct >= 0.80

    ds_intro, field_intro, score_intro = semantic_question_intent(
        "Giới thiệu khung chương trình đào tạo của ngành Toán tin",
        has_course=False,
    )
    assert (ds_intro, field_intro) == ("f1", "introduction")
    assert score_intro >= 0.80


def test_disambiguation_objectives_with_and_without_course():
    ds_course, field_course, score_course = semantic_question_intent(
        "Mục tiêu đào tạo và chuẩn đầu ra đạt được kỹ năng năng lực gì?",
        has_course=True,
    )
    assert (ds_course, field_course) == ("f3", "objectives")
    assert score_course >= 0.38

    ds_prog, field_prog, score_prog = semantic_question_intent(
        "Mục tiêu đào tạo và chuẩn đầu ra đạt được kỹ năng năng lực gì?",
        has_course=False,
    )
    assert (ds_prog, field_prog) == ("f1", "objectives")
    assert score_prog >= 0.38


def test_has_course_prevents_program_only_misrouting():
    ds, field, score = semantic_question_intent(
        "Tổng khối lượng tích lũy của môn này là bao nhiêu tín chỉ?",
        has_course=True,
    )
    assert (ds, field) == ("f2", "credits")
    assert score >= 0.38


@pytest.mark.parametrize(
    "question",
    [
        "Kỳ tới mình nên đăng ký học môn nào để dễ qua?",
        "Giúp mình lập lộ trình học tập và xếp lịch học kỳ sau",
        "Bạn có thể chọn môn học giúp mình vào kỳ tới được không?",
        "Cho mình hỏi thời tiết hôm nay và chuyển tiền ngân hàng thế nào?",
    ],
)
def test_out_of_scope_questions_return_none(question: str):
    dataset, field, score = semantic_question_intent(question, has_course=False)
    assert (dataset, field, score) == (None, None, 0.0)


def test_unrelated_gibberish_scores_below_threshold():
    dataset, field, score = semantic_question_intent(
        "Con mèo đang nằm ngủ trên mái nhà màu xanh",
        has_course=False,
    )
    assert dataset is None
    assert field is None
    assert score < 0.38


def test_rank_top_k_chunks_backfills_when_base_hits_empty():
    data = HUSRAGData.load_current()
    candidates = data.chunks("f1", major="computer_science")
    assert len(candidates) > 0

    hits = rank_top_k_chunks(
        "triển vọng công việc và vị trí nghề nghiệp sau khi ra trường",
        candidates,
        top_k=5,
        base_hits=(),
    )
    assert 1 <= len(hits) <= 5
    assert all(isinstance(h, RetrievalHit) for h in hits)
    assert hits[0].chunk.metadata.get("field") == "careers"
    # Verify deterministic ordering
    hits_repeat = rank_top_k_chunks(
        "triển vọng công việc và vị trí nghề nghiệp sau khi ra trường",
        candidates,
        top_k=5,
        base_hits=(),
    )
    assert [h.chunk.chunk_id for h in hits] == [h.chunk.chunk_id for h in hits_repeat]


def test_rank_top_k_chunks_preserves_base_hits_and_fills_remaining():
    data = HUSRAGData.load_current()
    retriever = HUSRAGRetriever(data)
    candidates = data.chunks("f3", major="data_science", allow_generated=True)
    assert len(candidates) > 0
    sample_code = candidates[0].metadata["course_code"]
    base_hits = retriever.search(
        f"{sample_code} nội dung",
        dataset="f3",
        major="data_science",
        allow_generated=True,
        top_k=2,
    )
    assert len(base_hits) >= 1

    # Pass all F3 chunks of sample_code so rank_top_k_chunks can backfill additional fields
    course_candidates = data.chunks(
        "f3",
        major="data_science",
        course_code=sample_code,
        allow_generated=True,
    )
    ranked = rank_top_k_chunks(
        f"{sample_code} nội dung và mục tiêu đánh giá",
        course_candidates,
        top_k=3,
        base_hits=base_hits[:1],
    )
    assert len(ranked) == min(3, len(course_candidates))
    assert ranked[0].chunk.chunk_id == base_hits[0].chunk.chunk_id
    assert ranked[0].score == base_hits[0].score
    assert len({h.chunk.chunk_id for h in ranked}) == len(ranked)
