"""Provisional source-anchor metrics; no runtime imports or inference in this module."""

from __future__ import annotations

import re
from collections import Counter
from copy import deepcopy

POSITIVE = {"f1", "f2", "f3"}
CODE = re.compile(r"\b[A-Z]{3}\d{4}[A-Z]?\b")


def collect_predictions(questions, execute):
    """The executor receives only a defensive copy of each frozen request."""
    collected = []
    for question in questions:
        try:
            result = execute(deepcopy(question["request"]))
        except Exception as exc:
            result = {"http_status": 0, "response": {}, "retrieval_calls": [],
                      "execution_error": f"{type(exc).__name__}: {str(exc)[:300]}"}
        collected.append({**result, "question_id": question["question_id"],
                          "request": deepcopy(question["request"])})
    return collected


def ratio(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator,
            "value": numerator / denominator if denominator else None}


def citation_identity(citation):
    meta = citation.get("metadata") or {}
    if citation.get("dataset") == "f2":
        record = meta.get("provenance", {}).get("portable_record", {})
        return "record_id", record.get("record_id")
    return "chunk_id", meta.get("chunk_id")


def citation_scope(citation):
    meta = citation.get("metadata") or {}
    record = meta.get("provenance", {}).get("portable_record", {})
    scope = record.get("scope") or meta.get("scope") or {}
    return {"major": record.get("major", meta.get("major")),
            "version": scope.get("curriculum_version", meta.get("curriculum_version", meta.get("program_version"))),
            "course_code": record.get("course_code", meta.get("course_code"))}


def scope_errors(request, answer, citations, calls):
    errors = {"major": False, "course_code": False, "version": False}
    codes = set(CODE.findall(request["question"].upper()))
    contexts = ([{"major": answer.get("major"), "version": answer.get("version"),
                  "course_code": answer.get("facts", {}).get("course_code")}] if answer else [])
    contexts += [citation_scope(c) for c in citations]
    contexts += [h for call in calls for h in call.get("hits", [])]
    for context in contexts:
        errors["major"] |= context.get("major") != request["major"]
        if request.get("version") is not None:
            errors["version"] |= context.get("version") != request["version"]
        code = context.get("course_code")
        if code and len(codes) == 1:
            errors["course_code"] |= code not in codes
    return errors


def facts_match(gold, facts):
    for field, expected in gold["expected_facts"].items():
        actual_field = {"course_name": "name", "prerequisites.raw_variants": "prerequisites"}.get(field, field)
        value = facts.get("value")
        if facts.get("field") == "course_info" and isinstance(value, dict):
            value = value.get(field)
        elif facts.get("field") != actual_field:
            return False
        if field == "prerequisites.raw_variants":
            if not isinstance(value, list) or set(value) != set(expected):
                return False
        elif value != expected:
            return False
    return True


def score_cases(questions, gold, evidence, observations):
    expected_ids = [q["question_id"] for q in questions]
    if ([g["question_id"] for g in gold] != expected_ids
            or [o["question_id"] for o in observations] != expected_ids
            or len(set(expected_ids)) != len(expected_ids)):
        raise ValueError("All question/gold/prediction IDs must join exactly, without omissions")
    by_evidence = {e["evidence_id"]: e for e in evidence}
    cases = []
    for question, target, observed in zip(questions, gold, observations, strict=True):
        request = question["request"]
        answer = observed.get("response", {}).get("hus_answer") or {}
        status = answer.get("status")
        citations = answer.get("citations") or []
        calls = observed.get("retrieval_calls") or []
        positive = target["category"] in POSITIVE
        ranked = target["category"] in {"f1", "f3"}
        refs = [by_evidence[eid]["source_ref"] for eid in target["evidence_ids"]]
        anchors = {(r["identity_field"], r["identity"]) for r in refs}
        expected_chunks = {r["identity"] for r in refs if r["identity_field"] == "chunk_id"}
        top5 = calls[0].get("hits", [])[:5] if calls else []
        retrieved = {h["chunk_id"] for h in top5 if h["dataset"] == target["expected_dataset"]}
        recall = len(retrieved & expected_chunks) / len(expected_chunks) if ranked and expected_chunks else 0
        errors = scope_errors(request, answer, citations, calls)
        clean_scope = not any(errors.values())
        integrity = observed.get("citation_integrity", {}).get("passed") is True
        good_ai = all(c.get("evidence_kind") == "ai" and c.get("display_label") == "kiến thức AI"
                      and c.get("open_url") is None for c in citations) if target["category"] == "f3" else True
        facts_ok = facts_match(target, answer.get("facts") or {}) if target["category"] == "f2" else True
        anchored = sum(positive and c.get("dataset") == target["expected_dataset"]
                       and citation_identity(c) in anchors and integrity and clean_scope and good_ai and facts_ok
                       for c in citations)
        unjudged = sum(positive and citation_identity(c) not in anchors and integrity for c in citations)
        http_ok = observed.get("http_status") == 200
        supported = (positive and http_ok and status == "answered" and answer.get("dataset") == target["expected_dataset"]
                     and bool(anchored) and facts_ok and clean_scope and good_ai)
        status_ok = http_ok and status == target["expected_status"]
        guard_ok = not positive and status_ok and not citations and not answer.get("facts")
        failure = None
        if not http_ok:
            failure = "http_or_execution_error"
        elif positive and not supported:
            if any(errors.values()):
                failure = "scope_error"
            elif status != "answered":
                failure = ("no_retrieval_call" if ranked and not calls else
                           "post_retrieval_abstention" if ranked else "lookup_or_intent_abstention")
            elif not facts_ok:
                failure = "fact_mismatch"
            elif answer.get("dataset") != target["expected_dataset"]:
                failure = "wrong_dataset"
            elif not integrity:
                failure = "citation_integrity_error"
            elif not good_ai:
                failure = "AI_label_error"
            else:
                failure = "gold_anchor_not_cited_pending_semantic_review"
        elif not positive and not guard_ok:
            failure = "guardrail_status_or_content_error"
        cases.append({"question_id": question["question_id"], "major": request["major"],
                      "category": target["category"], "expected_status": target["expected_status"],
                      "actual_status": status, "positive": positive, "retrieval_eligible": ranked,
                      "recall_at_5": recall, "retrieval_called": bool(calls),
                      "top5_chunk_ids": [h["chunk_id"] for h in top5],
                      "expected_chunk_ids": sorted(expected_chunks), "status_correct": status_ok,
                      "source_supported_success": bool(supported), "facts_match": facts_ok,
                      "guardrail_success": bool(guard_ok),
                      "false_abstention": positive and http_ok and status in {"no_information", "needs_clarification"},
                      "http_error": not http_ok, "citation_count": len(citations),
                      "anchored_citations": anchored, "unjudged_alternative_citations": unjudged,
                      "citation_integrity_passed": integrity, "scope_errors": errors, "failure": failure})
    return cases


def summarize(cases):
    ranked = [c for c in cases if c["retrieval_eligible"]]
    positives = [c for c in cases if c["positive"]]
    guards = [c for c in cases if not c["positive"]]
    f2 = [c for c in cases if c["category"] == "f2"]
    answered = [c for c in positives if c["actual_status"] == "answered"]
    total_citations = sum(c["citation_count"] for c in cases)
    citations_ok = [c for c in cases if c["citation_count"]]
    return {
        "cases": len(cases),
        "routed_recall_at_5": ratio(sum(c["recall_at_5"] for c in ranked), len(ranked)),
        "f2_lookup_success": ratio(sum(c["source_supported_success"] for c in f2), len(f2)),
        "answer_status_accuracy": ratio(sum(c["status_correct"] for c in cases), len(cases)),
        "source_supported_success_on_positive": ratio(sum(c["source_supported_success"] for c in positives), len(positives)),
        "anchor_support_among_positive_answers": ratio(sum(c["source_supported_success"] for c in answered), len(answered)),
        "citation_anchor_precision_lower_bound": ratio(sum(c["anchored_citations"] for c in cases), total_citations),
        "citation_integrity_answer_pass_rate": ratio(sum(c["citation_integrity_passed"] for c in citations_ok), len(citations_ok)),
        "unjudged_alternative_citations": sum(c["unjudged_alternative_citations"] for c in cases),
        "guardrail_success": ratio(sum(c["guardrail_success"] for c in guards), len(guards)),
        "abstention_on_12_missing_or_out_of_scope": ratio(
            sum(c["guardrail_success"] for c in guards if c["category"] != "opt_in_required"),
            sum(c["category"] != "opt_in_required" for c in guards)),
        "opt_in_clarification": ratio(sum(c["guardrail_success"] for c in guards if c["category"] == "opt_in_required"),
                                      sum(c["category"] == "opt_in_required" for c in guards)),
        "false_abstention_on_positive": ratio(sum(c["false_abstention"] for c in positives), len(positives)),
        "scope_error_cases": {key: sum(c["scope_errors"][key] for c in cases) for key in ["major", "course_code", "version"]},
        "http_errors": sum(c["http_error"] for c in cases),
        "failure_counts": dict(Counter(c["failure"] for c in cases if c["failure"])),
        "semantic_citation_precision": None,
        "semantic_source_support": None,
        "human_review": "pending; source anchors/integrity do not certify semantic correctness",
    }
