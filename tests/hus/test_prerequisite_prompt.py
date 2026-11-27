from types import SimpleNamespace

import pytest

from app.hus import llm_answerer
from app.schemas.hus import HUSQuestion


@pytest.mark.parametrize(
    ("status", "raw", "named", "expected"),
    [
        ("unknown", [None, " "], [], "Chưa xác định"),
        ("present", ["Không"], [], "Không"),
        ("present", ["MAT1001"], [{"course_code": "MAT1001"}], "MAT1001"),
        ("conflict", ["MAT1001", "MAT1002"], [], "Nguồn ghi không thống nhất"),
        ("unresolved", ["Ghi chú nguồn"], [], "Chưa xác minh"),
    ],
)
def test_prompt_preserves_prerequisite_evidence(monkeypatch, status, raw, named, expected):
    bundle = SimpleNamespace(
        intent_source="rule",
        version=None,
        top_k_chunks=[],
        structured_data={"course": {
            "course_code": "MAT2001",
            "prerequisite_status": status,
            "prerequisites_raw": raw,
            "prerequisites_named": named,
        }},
    )
    monkeypatch.setattr(llm_answerer, "get_settings", lambda: SimpleNamespace(
        hus_rag_llm_enabled=True, gemini_api_key="dummy-key",
    ))
    monkeypatch.setattr(llm_answerer, "_resolve_f2_pdf_citation", lambda *_: None)
    prompts = []

    def capture_prompt(prompt, **_):
        prompts.append(prompt)
        return "Câu trả lời giả lập"

    monkeypatch.setattr(llm_answerer, "call_gemini_llm", capture_prompt)
    result = llm_answerer.generate_grounded_answer(
        HUSQuestion(major="mathematics", question="Môn MAT2001 có tiên quyết không?"),
        SimpleNamespace(retrieve_context=lambda *_, **__: bundle),
    )
    assert result == ("Câu trả lời giả lập", [])
    lines = [line for line in prompts[0].splitlines()
             if line.startswith("- Điều kiện tiên quyết: ")]
    assert len(lines) == 1
    assert lines[0].startswith(f"- Điều kiện tiên quyết: {expected}")
