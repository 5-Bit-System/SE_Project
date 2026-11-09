"""Synthetic layer scoring must not hide router misses or manufacture semantics."""

import importlib
from copy import deepcopy
from pathlib import Path

import pytest


def scorer():
    path = Path(__file__).resolve().parents[2] / "tools/hus_rag_layer_metrics.py"
    assert path.exists(), "layer scoring is not implemented"
    return importlib.import_module("tools.hus_rag_layer_metrics").layer_metrics


def sample(qid="synthetic-1", category="f3"):
    question = {"question_id": qid, "request": {
        "question": "Nội dung MAT9998?", "major": "data_science", "version": "v1",
        "allow_generated_reference": True}}
    target = {"question_id": qid, "category": category, "expected_status": "answered",
              "expected_dataset": category, "expected_field": "content", "expected_facts": {},
              "evidence_ids": ["e1"]}
    evidence = {"evidence_id": "e1", "major": "data_science", "version": "v1",
                "source_ref": {"identity_field": "chunk_id", "identity": "c1"}}
    hit = {"chunk_id": "c1", "dataset": category, "field": "content", "major": "data_science",
           "version": "v1", "course_code": "MAT9998"}
    citation = {"dataset": category, "evidence_kind": "ai", "display_label": "kiến thức AI",
                "open_url": None, "metadata": {"chunk_id": "c1", "major": "data_science",
                                               "curriculum_version": "v1", "course_code": "MAT9998"}}
    observation = {"question_id": qid, "http_status": 200,
                   "routing_observation": {"dataset": category, "field": "content",
                                           "stage": "classifier_before_scope_and_evidence_guards"},
                   "response": {"mode": "hus_rag", "hus_answer": {
                       "status": "answered", "dataset": category, "major": "data_science",
                       "version": "v1", "facts": {}, "citations": [citation]}},
                   "retrieval_calls": [{"parameters": {"dataset": category, "field": "content",
                                         "major": "data_science", "version": "v1", "course_code": "MAT9998"},
                                        "hits": [hit]}],
                   "citation_integrity": {"passed": True}}
    return question, target, evidence, observation


def evaluate(question, target, evidence, observation):
    return scorer()([question], [target], [evidence], [observation])


def test_no_search_stays_in_routed_recall_denominator():
    q, g, e, obs = sample()
    obs["retrieval_calls"] = []
    obs["response"]["hus_answer"].update(status="no_information", citations=[])
    report = evaluate(q, g, e, obs)
    assert report["routing"]["positive_dataset_and_field_accuracy"]["value"] == 1
    assert report["retrieval"]["routed_recall_at_5"]["value"] == 0
    assert report["retrieval"]["conditional_recall_at_5"]["denominator"] == 0
    assert report["retrieval"]["eligible_cases_without_search"] == 1
    assert report["abstention"]["false_abstention_on_positive"]["numerator"] == 1


def test_anchor_retrieval_and_later_refusal_are_separate():
    q, g, e, obs = sample()
    obs["response"]["hus_answer"].update(status="no_information", citations=[])
    report = evaluate(q, g, e, obs)
    assert report["retrieval"]["routed_recall_at_5"]["value"] == 1
    assert report["retrieval"]["post_retrieval_false_abstention_cases"] == 1
    assert report["citation_source_support"]["source_supported_success_on_positive"]["value"] == 0


def test_f2_is_structured_lookup_and_field_aliases_are_canonicalized():
    q, g, e, obs = sample(category="f2")
    g.update(expected_field="course_name", expected_facts={"course_name": "Synthetic course"})
    e["source_ref"] = {"identity_field": "record_id", "identity": "program:MAT9998"}
    obs["routing_observation"]["field"] = "name"
    obs["retrieval_calls"] = []
    answer = obs["response"]["hus_answer"]
    answer["facts"] = {"field": "name", "value": "Synthetic course", "course_code": "MAT9998"}
    answer["citations"][0].update(evidence_kind="pdf", metadata={"provenance": {"portable_record": {
        "record_id": "program:MAT9998", "major": "data_science", "course_code": "MAT9998",
        "scope": {"curriculum_version": "v1"}}}})
    report = evaluate(q, g, e, obs)
    assert report["routing"]["positive_dataset_and_field_accuracy"]["value"] == 1
    assert report["retrieval"]["routed_recall_at_5"]["denominator"] == 0
    assert report["f2"]["source_backed_lookup_success"]["value"] == 1


def test_http500_is_an_error_not_false_or_true_abstention():
    q, g, e, obs = sample()
    obs.update(http_status=500, response={}, retrieval_calls=[])
    report = evaluate(q, g, e, obs)
    assert report["abstention"]["http_errors"] == 1
    assert report["abstention"]["false_abstention_on_positive"]["numerator"] == 0
    assert report["retrieval"]["routed_recall_at_5"]["denominator"] == 1


def test_correct_classifier_does_not_hide_wrong_search_field_filter():
    q, g, e, obs = sample()
    obs["retrieval_calls"][0]["parameters"]["field"] = "objectives"
    obs["retrieval_calls"][0]["hits"] = []
    report = evaluate(q, g, e, obs)
    assert report["routing"]["positive_dataset_and_field_accuracy"]["value"] == 1
    assert report["retrieval"]["wrong_search_field_cases"] == 1
    assert report["retrieval"]["anchor_excluded_by_observed_filter_cases"] == 1


def test_valid_citation_bytes_do_not_imply_anchor_or_semantic_support():
    q, g, e, obs = sample()
    obs["response"]["hus_answer"]["citations"][0]["metadata"]["chunk_id"] = "alternative-unreviewed"
    report = evaluate(q, g, e, obs)
    support = report["citation_source_support"]
    assert support["citation_integrity_answer_pass_rate"]["value"] == 1
    assert support["source_supported_success_on_positive"]["value"] == 0
    assert support["semantic_source_support"] is None
    assert support["semantic_citation_precision"] is None
    assert report["independent_holdout_accepted"] is False


def test_wrong_scope_anchor_id_never_counts_as_retrieval_support():
    q, g, e, obs = sample()
    obs["retrieval_calls"][0]["hits"][0]["major"] = "mathematics"
    report = evaluate(q, g, e, obs)
    assert report["retrieval"]["routed_recall_at_5"]["value"] == 0
    assert report["retrieval"]["anchor_hit_scope_mismatch_cases"] == 1


def test_controls_are_scored_for_refusal_without_positive_routing_accuracy():
    q, g, e, obs = sample()
    g.update(category="missing_evidence", expected_status="no_information")
    obs["routing_observation"].update(dataset=None, field=None)
    obs["retrieval_calls"] = []
    obs["response"]["hus_answer"].update(status="no_information", citations=[])
    report = evaluate(q, g, e, obs)
    assert report["routing"]["positive_dataset_and_field_accuracy"]["denominator"] == 0
    assert report["routing"]["control_cases"] == 1
    assert report["abstention"]["correct_missing_or_out_of_scope_refusal"]["value"] == 1


def test_missing_routing_trace_is_not_inferred_from_an_answer():
    q, g, e, obs = sample()
    obs.pop("routing_observation")
    report = evaluate(q, g, e, obs)
    assert report["routing"]["missing_classifier_observation_cases"] == 1
    assert report["routing"]["positive_dataset_and_field_accuracy"]["numerator"] == 0


def test_partial_search_metadata_is_reported_as_unknown_not_a_correct_filter():
    q, g, e, obs = sample()
    obs["retrieval_calls"][0]["parameters"] = {}
    report = evaluate(q, g, e, obs)
    assert report["retrieval"]["missing_filter_observation_cases"] == 1
    assert report["cases"][0]["retrieval_filter_observed"] is False


def test_scorer_does_not_mutate_captured_predictions_or_targets():
    q, g, e, obs = sample()
    originals = deepcopy((q, g, e, obs))
    evaluate(q, g, e, obs)
    assert (q, g, e, obs) == originals


def test_id_omissions_are_rejected_before_scoring():
    q, g, e, obs = sample()
    with pytest.raises(ValueError, match="join"):
        scorer()([q], [g], [e], [])
