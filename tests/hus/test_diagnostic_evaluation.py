"""Diagnostic measurement preserves failures and never sends gold to runtime."""

from copy import deepcopy
from pathlib import Path

import pytest


def runner():
    import importlib

    path = Path(__file__).resolve().parents[2] / "tools/evaluate_hus_diagnostic.py"
    assert path.exists(), "diagnostic runner has not been implemented"
    return importlib.import_module("tools.evaluate_hus_diagnostic")


def question():
    return {"question_id": "dev-1", "request": {
        "question": "Nội dung MAT9998?", "major": "data_science", "version": "v1",
        "allow_generated_reference": True}}


def test_collection_persists_execution_failure_without_dropping_case(tmp_path):
    module = runner()

    def execute(_request):
        raise RuntimeError("synthetic transport failure")

    predictions = module.collect_run([question()], tmp_path, execute)
    assert predictions[0]["http_status"] == 0
    assert "synthetic transport failure" in predictions[0]["execution_error"]
    assert module.rows(tmp_path / "predictions.jsonl") == predictions


def test_executor_receives_request_only_and_cannot_mutate_pack(tmp_path):
    module = runner()
    q = question()
    original = deepcopy(q)
    seen = []

    def execute(request):
        seen.append(set(request))
        request["question"] = "changed by executor"
        return {"http_status": 200, "response": {}, "retrieval_calls": []}

    module.collect_run([q], tmp_path, execute)
    assert q == original
    assert seen == [{"question", "major", "version", "allow_generated_reference"}]


def test_output_refuses_overwrite_and_frozen_pack_descendant(tmp_path):
    module = runner()
    pack = tmp_path / "pack"
    pack.mkdir()
    with pytest.raises(ValueError, match="exists"):
        module.prepare_output(pack, pack)
    with pytest.raises(ValueError, match="pack"):
        module.prepare_output(pack, pack / "new_run")


def test_no_retrieval_and_http_failure_remain_in_recall_denominator():
    module = runner()
    q = question()
    gold = {"question_id": q["question_id"], "category": "f3", "expected_status": "answered",
            "expected_dataset": "f3", "expected_field": "content", "expected_facts": {}, "evidence_ids": ["e1"]}
    evidence = {"evidence_id": "e1", "source_ref": {"identity_field": "chunk_id", "identity": "c1"}}
    prediction = {"question_id": q["question_id"], "request": q["request"],
                  "http_status": 500, "response": {}, "retrieval_calls": []}
    cases, metrics = module.build_scores([q], [gold], [evidence], [prediction],
                                         [{"question_id": q["question_id"], "passed": False}])
    assert cases[0]["failure"] == "http_or_execution_error"
    assert metrics["routed_recall_at_5"] == {"numerator": 0, "denominator": 1, "value": 0}
    assert metrics["http_errors"] == 1
    assert "abstention_on_12_missing_or_out_of_scope" not in metrics


def test_scoring_rejects_missing_audit_or_prediction():
    module = runner()
    with pytest.raises(ValueError, match="audit"):
        module.build_scores([question()], [], [], [], [])


def test_normalized_dev_metrics_do_not_claim_independent_acceptance():
    module = runner()
    report = module.development_summary([])
    assert report["semantic_citation_precision"] is None
    assert report["routed_recall_at_5"]["value"] is None
    assert report["abstention_on_missing_or_out_of_scope"]["denominator"] == 0


def test_name_only_f2_audit_uses_source_anchor_after_collection():
    module = runner()
    request = question()["request"] | {"question": "Môn có tên đầy đủ này có mấy tín chỉ?"}
    observation = {"question_id": "dev-1", "request": request, "http_status": 200,
                   "response": {"hus_answer": {"dataset": "f2", "status": "answered",
                       "facts": {"course_code": "MAT9998"}, "citations": []}}}
    target = {"category": "f2", "evidence_ids": ["e1"]}
    evidence = {"e1": {"source_ref": {"identity_field": "record_id", "identity": "program:MAT9998"}}}

    class Oracle:
        called = False

        def check(self, answer, major, **kwargs):
            self.called = True
            assert kwargs["code"] == "MAT9998"

    oracle = Oracle()
    audited = module.audit_development_prediction(observation, target, evidence, oracle, None, {})
    assert oracle.called
    assert audited["passed"] is True
    assert "MAT9998" not in request["question"]


def test_name_only_f2_cannot_hide_wrong_answer_code_behind_correct_anchor():
    module = runner()
    request = question()["request"] | {"question": "Môn này có mấy tín chỉ?"}
    observation = {"question_id": "dev-1", "request": request, "http_status": 200,
                   "response": {"hus_answer": {"dataset": "f2", "status": "answered",
                       "facts": {"course_code": "MAT9997"}, "citations": []}}}
    target = {"category": "f2", "evidence_ids": ["e1"]}
    evidence = {"e1": {"source_ref": {"identity_field": "record_id", "identity": "program:MAT9998"}}}
    result = module.audit_development_prediction(observation, target, evidence, object(), None, {})
    assert result["passed"] is False
    assert "code" in result["error"]


def test_route_observation_only_classifies_question_text_without_gold_hints():
    module = runner()
    seen = []

    def classify(text):
        seen.append(text)
        return "f2", "credits"

    observed = module.observe_route("synthetic question", classify)
    assert seen == ["synthetic question"]
    assert observed == {"dataset": "f2", "field": "credits",
                        "stage": "classifier_before_scope_and_evidence_guards"}
