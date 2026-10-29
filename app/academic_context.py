"""Source-owned academic facts with explicit provenance and fail-closed readiness.

This module does not select a policy for a real student. Callers must supply a
server-reviewed binding and applicable policy; unreviewed sources remain view-only.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from app.models import Catalog


class AcademicContextError(ValueError):
    """Safe boundary codes, never raw source/student data."""


@dataclass(frozen=True)
class AcademicPolicy:
    version: str
    source_ref: str
    program_ids: tuple[str, ...]
    # Explicit source-reviewed bands: minimum grade10, maximum grade10, grade4.
    letter_bands: dict[str, tuple[float, float, float | None]]
    failing_letters: tuple[str, ...] = ("F",)
    min_cohort: int | None = None
    retake_strategy: str = "unresolved"


def _number(value: Any) -> Decimal | None:
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        return None
    text = str(value).strip()
    if not re.fullmatch(r"\d+(?:[.,]\d+)?", text):
        return None
    try:
        number = Decimal(text.replace(",", "."))
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _outcome(rows: list[dict], credits: int, policy: AcademicPolicy) -> tuple[str, str]:
    if len(rows) != 1:
        if policy.retake_strategy != "later_final_after_f_d_or_d_plus":
            return "unresolved", "retake_policy_unresolved"
        ordered = []
        for row in rows:
            term = str(row.get("term") or "")
            match = re.fullmatch(r"HỌC K[ỲÌ]\s+([1-3])\s*-\s*(\d{4})\s*[-–]\s*(\d{4})(?:\..*)?",
                                 term.strip(), re.I)
            if not match or int(match[3]) != int(match[2]) + 1:
                return "unresolved", "retake_term_unresolved"
            ordered.append(((int(match[2]), int(match[1])), row))
        if len({key for key, _ in ordered}) != len(ordered):
            return "unresolved", "retake_term_unresolved"
        ordered.sort(key=lambda item: item[0])
        for _, row in ordered:
            state, reason = _outcome([row], credits, policy)
            if state == "unresolved":
                return state, reason
        if any(row.get("letter") not in {"F", "D", "D+"} for _, row in ordered[:-1]):
            return "unresolved", "retake_policy_unresolved"
        return _outcome([ordered[-1][1]], credits, policy)
    attempt = rows[0]
    if _number(attempt.get("credits")) != Decimal(str(credits)):
        return "unresolved", "source_catalog_credit_conflict"
    letter = str(attempt.get("letter") or "").strip()
    band = policy.letter_bands.get(letter)
    if not band:
        return "unresolved", "unsupported_or_missing_grade"
    grade = _number(attempt.get("grade10"))
    if grade is None or not Decimal(str(band[0])) <= grade <= Decimal(str(band[1])):
        return "unresolved", "source_grade_conflict"
    grade4 = _number(attempt.get("grade4"))
    if band[2] is None:
        raw_grade4 = attempt.get("grade4")
        if raw_grade4 is not None and str(raw_grade4).strip():
            return "unresolved", "source_grade_conflict"
    elif grade4 != Decimal(str(band[2])):
        return "unresolved", "source_grade_conflict"
    return ("not_completed" if letter in policy.failing_letters else "completed"), "policy_matched"


def build_context(
    snapshot: dict | None, *, owner_id: str, catalog: Catalog,
    catalog_revision: str, binding: dict | None = None,
    policy: AcademicPolicy | None = None,
) -> dict:
    """Derive immutable facts. Only ready contexts expose a usable completed set."""
    source = snapshot or {}
    fingerprint = {
        "owner": owner_id, "source": source, "catalog_revision": catalog_revision,
        "catalog": catalog.model_dump(mode="json"), "binding": binding,
        "policy": None if policy is None else {
            "version": policy.version, "source": policy.source_ref,
            "program_ids": policy.program_ids, "bands": policy.letter_bands,
            "failing_letters": policy.failing_letters,
            "min_cohort": policy.min_cohort, "retake_strategy": policy.retake_strategy,
        },
    }
    revision = hashlib.sha256(json.dumps(fingerprint, ensure_ascii=False,
                                        sort_keys=True).encode("utf-8")).hexdigest()
    result = {"revision": revision, "program_id": catalog.program.program_id,
              "catalog_revision": catalog_revision, "catalog_status": catalog.program.catalog_status,
              "source_digest": source.get("digest"), "completeness": source.get("completeness"),
              "policy_version": policy.version if policy else None,
              "policy_source": policy.source_ref if policy else None,
              "status": "needs_source_review", "blocking_reasons": [],
              "outcomes": [], "completed_course_codes": [], "project_gpa": None}
    reasons = result["blocking_reasons"]
    if not snapshot:
        reasons.append("source_missing")
    elif source.get("completeness") != "complete":
        reasons.append("source_incomplete")
    if source.get("unknown_rows"):
        reasons.append("unparsed_source_rows")
    if not isinstance(source.get("unknown_rows"), list):
        reasons.append("source_rows_invalid")
    if not isinstance(source.get("digest"), str) or not source["digest"].strip():
        reasons.append("source_digest_missing")
    if type(source.get("schema_version")) is not int or source.get("schema_version") != 1:
        reasons.append("source_schema_unsupported")
    attempts = source.get("attempts")
    if not isinstance(attempts, list) or any(not isinstance(row, dict) for row in attempts):
        reasons.append("source_rows_invalid")
        return result
    if not attempts:
        reasons.append("source_empty_unverified")
    keys = [row.get("row_key") for row in attempts]
    if any(not isinstance(key, str) or not key for key in keys):
        reasons.append("source_row_keys_invalid")
    elif len(set(keys)) != len(keys):
        reasons.append("source_row_keys_invalid")
    if (not binding or binding.get("verified") is not True or not binding.get("evidence_ref")
            or binding.get("program_id") != catalog.program.program_id
            or binding.get("catalog_revision") != catalog_revision):
        reasons.append("program_binding_unverified")
        result["status"] = "needs_program_binding"
        return result
    if (policy is None or not policy.source_ref or not policy.version
            or catalog.program.program_id not in policy.program_ids
            or binding.get("policy_version") != policy.version
            or (policy.min_cohort is not None and (
                type(binding.get("cohort")) is not int or binding["cohort"] < policy.min_cohort))):
        reasons.append("policy_not_applicable")
        result["status"] = "needs_policy_review"
        return result
    groups: dict[str, list[dict]] = defaultdict(list)
    if catalog.program.catalog_status != "verified":
        reasons.append("catalog_unverified")
        result["status"] = "needs_policy_review"
    if getattr(catalog.program, "planning_blockers", []):
        reasons.append("program_rules_review_required")
        result["status"] = "needs_policy_review"
    for attempt in attempts:
        groups[str(attempt.get("code") or "").strip()].append(attempt)
    courses = {course.code: course for course in catalog.courses}
    for code, rows in sorted(groups.items()):
        if code not in courses:
            state, reason = "out_of_catalog", "exact_mapping_unresolved"
        elif courses[code].source_status != "verified":
            state, reason = "unresolved", "course_source_unverified"
        else:
            state, reason = _outcome(rows, courses[code].credits, policy)
        result["outcomes"].append({"code": code, "state": state, "reason": reason,
                                   "row_keys": [row.get("row_key") for row in rows]})
    if any(outcome["state"] in {"unresolved", "out_of_catalog"}
           for outcome in result["outcomes"]):
        reasons.append("course_outcomes_unresolved")
        result["status"] = "needs_policy_review"
    elif not reasons:
        result["status"] = "ready"
        result["completed_course_codes"] = [outcome["code"] for outcome in result["outcomes"]
                                             if outcome["state"] == "completed"]
    return result


def require_ready(context: dict, expected_revision: str | None = None) -> set[str]:
    if expected_revision is not None and expected_revision != context["revision"]:
        raise AcademicContextError("context_changed")
    if context["status"] != "ready":
        raise AcademicContextError("academic_context_not_ready")
    return set(context["completed_course_codes"])
