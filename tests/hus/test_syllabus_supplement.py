"""Section recovery must preserve source text and stop at the owning course."""

import pytest

from tools.audit_hus_source_review import SourceReviewError, captured_context, digest
from tools.prepare_hus_syllabus_supplement import candidate_block, course_blocks, missing_section


def context(text):
    return captured_context([{"page": 1, "raw_sha256": "raw", "text": text,
                              "text_sha256": digest(text.encode())}], "raw")


@pytest.mark.parametrize("heading", ["9. Kiểm tra, đánh giá kết quả học tập", "8.\nPhương pháp kiểm tra đánh giá:"])
def test_old_and_new_assessment_headings_keep_exact_quote(heading):
    number = int(heading[0])
    text = f"ĐỀ CƯƠNG HỌC PHẦN\n{heading}\nBài thực hành và bài kiểm tra được ghi ở đây.\n{number + 1}. Học liệu\nSách."
    ctx = context(text)
    span, reason = missing_section(ctx, course_blocks(text)[0], "assessment")
    assert reason is None
    assert span["source_quote"].startswith(heading)
    assert span["source_quote"] == text[span["start_char"]:span["end_char"]]
    assert "Học liệu" not in span["source_quote"]


def test_assessment_cannot_be_borrowed_from_following_course():
    text = ("ĐỀ CƯƠNG HỌC PHẦN\nMôn A không có mục đánh giá.\n"
            "ĐỀ CƯƠNG HỌC PHẦN\n9. Kiểm tra, đánh giá kết quả học tập\n"
            "Bài thực hành và bài kiểm tra của môn B.\n10. Học liệu\n")
    span, reason = missing_section(context(text), course_blocks(text)[0], "assessment")
    assert span is None and reason == "heading_absent_or_ambiguous"


def test_empty_objective_heading_does_not_inherit_learning_outcomes():
    text = "ĐỀ CƯƠNG HỌC PHẦN\n6. Mục tiêu của học phần:\n7. Chuẩn đầu ra\nKiến thức và kỹ năng.\n"
    span, reason = missing_section(context(text), course_blocks(text)[0], "objectives")
    assert span is None and reason == "heading_present_but_body_empty_or_insufficient"


def test_repeated_printed_code_is_owned_by_offsets_not_code_lookup():
    text = "ĐỀ CƯƠNG HỌC PHẦN\nMAT1202 môn A.\nĐỀ CƯƠNG HỌC PHẦN\nMAT1202 môn B."
    blocks = course_blocks(text)
    start = text.index("môn B")
    candidate = {"fields": {"content": [{"start_char": start, "end_char": start + 5}]}}
    assert candidate_block(candidate, blocks) == blocks[1]


def test_cross_course_existing_quote_is_rejected():
    text = "ĐỀ CƯƠNG HỌC PHẦN\nMôn A.\nĐỀ CƯƠNG HỌC PHẦN\nMôn B."
    candidate = {"fields": {"content": [{"start_char": 2, "end_char": len(text)}]}}
    with pytest.raises(SourceReviewError, match="cross course"):
        candidate_block(candidate, course_blocks(text))


def test_ambiguous_assessment_or_unbounded_section_is_queued():
    for tail, reason in [("", "section_end_not_located"),
                         ("\n9. Kiểm tra, đánh giá khác\n10. Học liệu", "heading_absent_or_ambiguous")]:
        text = "ĐỀ CƯƠNG HỌC PHẦN\n9. Kiểm tra, đánh giá kết quả học tập\nBài thi và thực hành." + tail
        span, observed = missing_section(context(text), course_blocks(text)[0], "assessment")
        assert span is None and observed == reason
