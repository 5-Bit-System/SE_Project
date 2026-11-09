"""Metric regressions use synthetic observations, never execute holdout queries."""

from copy import deepcopy
from pathlib import Path

import httpx

from tools.evaluate_hus_rag import capture_response, verify_saved_run
from tools.hus_rag_metrics import collect_predictions, score_cases, summarize


def sample():
    question = {"question_id": "synthetic-1", "request": {
        "question": "Nội dung MAT9998?", "major": "data_science", "version": "v1",
        "allow_generated_reference": True}}
    gold = {"question_id": "synthetic-1", "category": "f3", "expected_status": "answered",
            "expected_dataset": "f3", "expected_field": "content", "expected_facts": {},
            "evidence_ids": ["e1"]}
    evidence = {"evidence_id": "e1", "major": "data_science", "version": "v1",
                "source_ref": {"identity_field": "chunk_id", "identity": "c1"}}
    citation = {"dataset": "f3", "evidence_kind": "ai", "display_label": "kiến thức AI",
                "open_url": None, "metadata": {"chunk_id": "c1", "major": "data_science",
                                               "curriculum_version": "v1", "course_code": "MAT9998"}}
    observed = {"question_id": "synthetic-1", "http_status": 200,
                "response": {"mode": "hus_rag", "hus_answer": {
                    "status": "answered", "dataset": "f3", "major": "data_science",
                    "version": "v1", "facts": {}, "citations": [citation]}},
                "retrieval_calls": [{"hits": [{"chunk_id": "c1", "dataset": "f3",
                    "major": "data_science", "version": "v1", "course_code": "MAT9998"}]}],
                "citation_integrity": {"passed": True, "error": None}}
    return question, gold, evidence, observed


def evaluate(q, g, e, observed):
    cases = score_cases([q], [g], [e], [observed])
    return cases[0], summarize(cases)


def test_no_retriever_call_is_a_recall_miss_and_false_abstention():
    q, g, e, obs = sample()
    obs["retrieval_calls"] = []
    obs["response"]["hus_answer"].update(status="no_information", citations=[])
    case, report = evaluate(q, g, e, obs)
    assert case["failure"] == "no_retrieval_call"
    assert report["routed_recall_at_5"]["value"] == 0
    assert report["routed_recall_at_5"]["denominator"] == 1
    assert report["false_abstention_on_positive"]["numerator"] == 1


def test_zero_citations_does_not_report_perfect_precision():
    q, g, e, obs = sample()
    obs["response"]["hus_answer"]["citations"] = []
    _, report = evaluate(q, g, e, obs)
    assert report["citation_anchor_precision_lower_bound"]["value"] is None
    assert report["source_supported_success_on_positive"]["value"] == 0


def test_gold_anchor_must_be_in_actual_top_five():
    q, g, e, obs = sample()
    hit = obs["retrieval_calls"][0]["hits"][0]
    obs["retrieval_calls"][0]["hits"] = [dict(hit, chunk_id=f"other-{i}") for i in range(5)] + [hit]
    _, report = evaluate(q, g, e, obs)
    assert report["routed_recall_at_5"]["value"] == 0


def test_wrong_scope_cannot_count_as_supported():
    q, g, e, obs = sample()
    obs["response"]["hus_answer"]["citations"][0]["metadata"]["major"] = "mathematics"
    case, report = evaluate(q, g, e, obs)
    assert case["scope_errors"]["major"] is True
    assert report["source_supported_success_on_positive"]["value"] == 0


def test_ai_null_link_is_valid_but_missing_label_is_not():
    q, g, e, obs = sample()
    assert evaluate(q, g, e, obs)[1]["source_supported_success_on_positive"]["value"] == 1
    obs["response"]["hus_answer"]["citations"][0]["display_label"] = "PDF"
    assert evaluate(q, g, e, obs)[1]["source_supported_success_on_positive"]["value"] == 0


def test_http_error_stays_in_all_denominators():
    q, g, e, obs = sample()
    obs.update(http_status=503, response={"detail": "unavailable"}, retrieval_calls=[])
    _, report = evaluate(q, g, e, obs)
    assert report["routed_recall_at_5"]["denominator"] == 1
    assert report["answer_status_accuracy"]["value"] == 0
    assert report["http_errors"] == 1
    assert report["false_abstention_on_positive"]["numerator"] == 0


def test_f2_fact_mismatch_is_not_support_even_with_valid_citation():
    q, g, e, obs = sample()
    g.update(category="f2", expected_dataset="f2", expected_field="credits", expected_facts={"credits": 3})
    e["source_ref"] = {"identity_field": "record_id", "identity": "program:MAT9998"}
    obs["response"]["hus_answer"].update(dataset="f2", facts={"field": "credits", "value": 9, "course_code": "MAT9998"})
    citation = obs["response"]["hus_answer"]["citations"][0]
    citation.update(dataset="f2", evidence_kind="pdf")
    citation["metadata"] = {"provenance": {"portable_record": {
        "record_id": "program:MAT9998", "major": "data_science", "course_code": "MAT9998",
        "scope": {"curriculum_version": "v1"}}}}
    _, report = evaluate(q, g, e, obs)
    assert report["f2_lookup_success"]["value"] == 0
    assert report["source_supported_success_on_positive"]["value"] == 0
    assert report["citation_anchor_precision_lower_bound"]["value"] == 0


def test_abstention_does_not_earn_positive_answer_credit():
    q, g, e, obs = sample()
    g.update(category="missing_evidence", expected_status="no_information")
    obs["response"]["hus_answer"].update(status="no_information", facts={}, citations=[])
    _, report = evaluate(q, g, e, obs)
    assert report["guardrail_success"]["value"] == 1
    assert report["source_supported_success_on_positive"]["denominator"] == 0
    assert report["semantic_citation_precision"] is None


def test_executor_receives_request_only_and_cannot_mutate_frozen_question():
    q, _, _, _ = sample()
    original = deepcopy(q)
    received = []
    def execute(request):
        received.append(set(request))
        request["question"] = "mutated synthetic input"
        return {"http_status": 200, "response": {}, "retrieval_calls": []}
    predictions = collect_predictions([q], execute)
    assert received == [{"question", "major", "version", "allow_generated_reference"}]
    assert q == original
    assert predictions[0]["question_id"] == q["question_id"]


def test_plaintext_http_error_keeps_status_body_and_retrieval_trace():
    q, g, e, obs = sample()
    response = httpx.Response(500, text="Synthetic internal error")
    captured = capture_response(response, obs["retrieval_calls"])
    assert captured["http_status"] == 500
    assert captured["raw_response_text"] == "Synthetic internal error"
    assert captured["response_json_error"]
    assert captured["retrieval_calls"] == obs["retrieval_calls"]
    case, report = evaluate(q, g, e, {**captured, "question_id": q["question_id"]})
    assert case["http_error"] is True
    assert report["routed_recall_at_5"]["value"] == 1
    assert report["source_supported_success_on_positive"]["value"] == 0


def test_saved_measurement_replays_without_new_inference():
    root = Path(__file__).resolve().parents[2]
    report = verify_saved_run(root / "data/hus/evaluation/runs/p12_baseline_v1")
    assert report["reproduced"] is True
    assert report["questions"] == 48
    assert report["new_rag_inference"] is False
