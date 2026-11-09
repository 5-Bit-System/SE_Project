"""Separate measured QA layers from saved observations, with no runtime imports."""

from __future__ import annotations

from collections import Counter

from tools.hus_rag_metrics import CODE, ratio, score_cases, summarize

ROUTING_STAGE = "classifier_before_scope_and_evidence_guards"
FIELD_ALIASES = {"course_name": "name", "prerequisites.raw_variants": "prerequisites"}


def canonical_field(field):
    return FIELD_ALIASES.get(field, field)


def _anchor_hit_matches(hit, anchor, target, expected_codes):
    if hit.get("chunk_id") != anchor["source_ref"]["identity"]:
        return False
    if (hit.get("dataset"), hit.get("major"), hit.get("version"), hit.get("field")) != (
        target["expected_dataset"], anchor["major"], anchor["version"], canonical_field(target["expected_field"])
    ):
        return False
    return len(expected_codes) != 1 or hit.get("course_code") in expected_codes


def _filter_excludes(anchor, target, parameters, expected_codes):
    expected = {"dataset": target["expected_dataset"], "major": anchor["major"],
                "version": anchor["version"], "field": canonical_field(target["expected_field"])}
    for key, value in expected.items():
        if parameters.get(key) is not None and parameters[key] != value:
            return True
    return (parameters.get("course_code") is not None and len(expected_codes) == 1
            and parameters["course_code"] not in expected_codes)


def layer_metrics(questions, gold, evidence, predictions):
    """Score fixed observations; evidence/gold are never forwarded to a runtime.

    Predictions include oracle audits under citation_integrity. Routing is the
    classifier observed before scope/evidence guards, not the response dataset.
    Retrieval uses the first actual call's top5 as the established runner does.
    """
    base_cases = score_cases(questions, gold, evidence, predictions)
    baseline = summarize(base_cases)
    evidence_by_id = {item["evidence_id"]: item for item in evidence}
    cases = []
    control_routes = Counter()
    for question, target, observed, base in zip(questions, gold, predictions, base_cases, strict=True):
        route = observed.get("routing_observation")
        route_valid = isinstance(route, dict) and route.get("stage") == ROUTING_STAGE
        dataset_ok = route_valid and route.get("dataset") == target["expected_dataset"]
        field_ok = route_valid and canonical_field(route.get("field")) == canonical_field(target["expected_field"])
        calls = observed.get("retrieval_calls") or []
        first = calls[0] if calls else {}
        parameters = first.get("parameters") or {}
        anchors = [evidence_by_id[eid] for eid in target["evidence_ids"]
                   if evidence_by_id[eid]["source_ref"]["identity_field"] == "chunk_id"]
        expected_codes = set(CODE.findall(question["request"]["question"].upper()))
        top5 = first.get("hits", [])[:5]
        scoped_anchors = [anchor for anchor in anchors if any(
            _anchor_hit_matches(hit, anchor, target, expected_codes) for hit in top5)]
        raw_anchor_ids = {anchor["source_ref"]["identity"] for anchor in anchors}
        raw_anchor_hits = [hit for hit in top5 if hit.get("chunk_id") in raw_anchor_ids]
        scoped_recall = len(scoped_anchors) / len(anchors) if base["retrieval_eligible"] and anchors else 0
        filter_observed = (bool(calls) and isinstance(first.get("parameters"), dict)
                           and {"dataset", "field", "major", "version"} <= parameters.keys())
        excluded = (filter_observed and bool(anchors)
                    and all(_filter_excludes(anchor, target, parameters, expected_codes) for anchor in anchors))
        search_dataset_wrong = bool(calls) and parameters.get("dataset") is not None and parameters["dataset"] != target["expected_dataset"]
        search_field_wrong = (bool(calls) and parameters.get("field") is not None
                              and canonical_field(parameters["field"]) != canonical_field(target["expected_field"]))
        scope_mismatch = any(not any(_anchor_hit_matches(hit, anchor, target, expected_codes)
                                    for anchor in anchors) for hit in raw_anchor_hits)
        if not base["positive"]:
            name = f"{route.get('dataset')}/{route.get('field')}" if route_valid else "missing_classifier_observation"
            control_routes[(target["category"], name)] += 1
        cases.append({
            **base,
            "classifier_observation_present": route_valid,
            "classifier_dataset": route.get("dataset") if route_valid else None,
            "classifier_field": route.get("field") if route_valid else None,
            "expected_classifier_field": canonical_field(target["expected_field"]),
            "positive_dataset_correct": bool(base["positive"] and dataset_ok),
            "positive_field_correct": bool(base["positive"] and field_ok),
            "positive_dataset_and_field_correct": bool(base["positive"] and dataset_ok and field_ok),
            "scope_checked_recall_at_5": scoped_recall,
            "scope_checked_anchor_hit": bool(scoped_anchors),
            "retrieval_filter_observed": filter_observed,
            "wrong_search_dataset": bool(base["retrieval_eligible"] and search_dataset_wrong),
            "wrong_search_field": bool(base["retrieval_eligible"] and search_field_wrong),
            "anchor_excluded_by_observed_filter": bool(base["retrieval_eligible"] and excluded),
            "anchor_hit_scope_mismatch": bool(base["retrieval_eligible"] and scope_mismatch),
        })
    positives = [case for case in cases if case["positive"]]
    eligible = [case for case in cases if case["retrieval_eligible"]]
    searched = [case for case in eligible if case["retrieval_called"]]
    controls = [case for case in cases if not case["positive"]]
    refusals = [case for case in controls if case["category"] in {"missing_evidence", "out_of_scope"}]
    consent = [case for case in controls if case["category"] == "opt_in_required"]
    positive_false_refusal = [case for case in positives if case["false_abstention"]]
    support_keys = ["source_supported_success_on_positive", "anchor_support_among_positive_answers",
                    "citation_anchor_precision_lower_bound", "citation_integrity_answer_pass_rate",
                    "unjudged_alternative_citations", "semantic_citation_precision", "semantic_source_support"]
    return {
        "schema_version": "1.0", "scope": "saved_development_observations_not_independent_acceptance",
        "cases_count": len(cases), "independent_holdout_accepted": False,
        "routing": {
            "stage": ROUTING_STAGE,
            "positive_dataset_accuracy": ratio(sum(case["positive_dataset_correct"] for case in positives), len(positives)),
            "positive_field_accuracy": ratio(sum(case["positive_field_correct"] for case in positives), len(positives)),
            "positive_dataset_and_field_accuracy": ratio(sum(case["positive_dataset_and_field_correct"] for case in positives), len(positives)),
            "missing_classifier_observation_cases": sum(not case["classifier_observation_present"] for case in cases),
            "control_cases": len(controls),
            "control_classifications": [{"category": category, "classification": route, "count": count}
                                        for (category, route), count in sorted(control_routes.items())],
            "limits": "Positive routing accuracy is separate from safety guards; control refusals do not require a positive data route.",
        },
        "retrieval": {
            "routed_recall_at_5": ratio(sum(case["scope_checked_recall_at_5"] for case in eligible), len(eligible)),
            "conditional_recall_at_5": ratio(sum(case["scope_checked_recall_at_5"] for case in searched), len(searched)),
            "conditional_top5_anchor_hit_rate": ratio(sum(case["scope_checked_anchor_hit"] for case in searched), len(searched)),
            "actual_search_call_rate": ratio(len(searched), len(eligible)),
            "eligible_cases_without_search": len(eligible) - len(searched),
            "missing_filter_observation_cases": sum(not case["retrieval_filter_observed"] for case in searched),
            "wrong_search_dataset_cases": sum(case["wrong_search_dataset"] for case in eligible),
            "wrong_search_field_cases": sum(case["wrong_search_field"] for case in eligible),
            "anchor_excluded_by_observed_filter_cases": sum(case["anchor_excluded_by_observed_filter"] for case in eligible),
            "anchor_hit_scope_mismatch_cases": sum(case["anchor_hit_scope_mismatch"] for case in eligible),
            "post_retrieval_false_abstention_cases": sum(case["retrieval_called"] for case in positive_false_refusal if case["retrieval_eligible"]),
            "legacy_id_only_routed_recall_at_5": baseline["routed_recall_at_5"],
            "definition": "First real search top5; anchor ID plus evidence major/version/field and explicit query code must agree. No-call counts as miss. Conditional recall has a separate denominator.",
        },
        "f2": {
            "source_backed_lookup_success": baseline["f2_lookup_success"],
            "definition": "Structured facts, correct scope, expected source anchor and external integrity audit; excluded from retrieval Recall@5.",
        },
        "citation_source_support": {**{key: baseline[key] for key in support_keys},
                                    "definition": "Integrity/anchor matching do not certify semantic entailment or reviewer-approved alternative evidence."},
        "abstention": {
            "correct_missing_or_out_of_scope_refusal": ratio(sum(case["guardrail_success"] for case in refusals), len(refusals)),
            "correct_opt_in_clarification": ratio(sum(case["guardrail_success"] for case in consent), len(consent)),
            "false_abstention_on_positive": baseline["false_abstention_on_positive"],
            "required_guard_failure_cases": sum(not case["guardrail_success"] for case in controls),
            "guard_failures_excluding_http_errors": sum(not case["guardrail_success"] and not case["http_error"] for case in controls),
            "http_errors": baseline["http_errors"],
            "definition": "HTTP errors remain failures and denominators, but are not counted as true or false abstentions.",
        },
        "scope_errors": baseline["scope_error_cases"],
        "cases": cases,
        "limits": ["Provisional source anchors; semantic metrics stay null until real human review.",
                   "Field aliases are canonicalized only for scoring, never injected into requests.",
                   "No gold-forced search, source expansion or new RAG inference occurs in this scorer."],
    }
