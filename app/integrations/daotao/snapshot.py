"""Lossless source contract; no academic interpretation or catalog matching."""

import hashlib
import json
import re


class PortalFailure(Exception):
    """Only a safe, predefined code may cross the portal boundary."""


def collection_review(payload: dict, save_status: str) -> dict:
    """Allowlisted technical proof only, independent of retained student records."""
    version = payload.get("connector_version")
    report = {
        "connector_version": version if version in {"b790d6af+identity1", "vnu-full-table-20261025"} else "unsupported",
        "completeness": "complete" if payload.get("completeness") == "complete" else "unknown",
        "save_status": save_status if save_status in {"saved", "unchanged", "retained"} else "failed",
        "unparsed_rows": len(payload.get("unknown_rows")) if isinstance(payload.get("unknown_rows"), list) else 0,
    }
    proof = payload.get("collection_evidence")
    if isinstance(proof, dict):
        checks = ("source_host_valid", "source_path_valid", "transcript_container_valid",
                  "filters_absent", "pagination_absent", "hidden_records_absent",
                  "virtualization_absent", "loading_absent", "network_idle")
        evidence = {key: proof.get(key) is True for key in checks}
        for key in ("stable_reads", "data_table_count"):
            value = proof.get(key)
            evidence[key] = value if type(value) is int and 0 <= value <= 100000 else 0
        report["evidence"] = evidence
    else:
        report["evidence"] = None
    return report


def source_profile(texts: list[str]) -> dict:
    """Read explicit labels only; missing or conflicting values remain unknown.

    Management class has the user-confirmed source format [cohort] [program].
    These are display values, never a reviewed academic program/policy binding.
    """
    labels = {"họ và tên": "name", "họ tên": "name",
              "ngành học": "program", "ngành": "program",
              "khóa học": "cohort", "khoá học": "cohort"}
    candidates = {key: set() for key in ("name", "program", "cohort")}
    management_classes = set()
    for body in texts:
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        for line in lines:
            parts = re.split(r"[:：\t]+", line, maxsplit=1)
            label = parts[0].strip().casefold()
            if label == "lớp quản lý":
                management_classes.add(parts[1].strip() if len(parts) == 2 else "")
                continue
            if label not in labels:
                continue
            value = parts[1].strip() if len(parts) == 2 else ""
            if (value and len(value) <= 200 and not re.search(r"[:：\t]", value)
                    and value.casefold() not in labels):
                candidates[labels[label]].add(value)
    result = {key: next(iter(values)) if len(values) == 1 else None
              for key, values in candidates.items()}
    if management_classes:
        # The requested source is Lớp quản lý, not the separate Khóa selector.
        result.update(program=None, cohort=None)
        if len(management_classes) == 1:
            value = next(iter(management_classes))
            match = re.fullmatch(r"([0-9]+)\s+([^\W\d_][^\r\n\t:：]*)", value)
            if match and len(value) <= 200:
                result.update(cohort=match[1], program=match[2].strip())
    return result


def verified_subject(text: str, requested: str, *, authenticated_subject: str | None = None) -> str:
    # A labelled portal identifier, when present, must agree. If it is absent,
    # require the account proven by DaotaoClient's fresh form POST/auth transition.
    # Caller-supplied username or nonempty grades alone never establish ownership.
    matches = re.findall(
        r"(?:Mã\s+(?:sinh\s+viên|SV)|MSSV|MSV)\s*[:：]?\s*"
        r"([a-z0-9][a-z0-9._-]*)(?![\w.-])", text, re.I)
    subjects = {value.casefold() for value in matches}
    expected = requested.strip().casefold()
    if subjects:
        if subjects != {expected}:
            raise PortalFailure("identity_unverified")
        return expected
    if authenticated_subject != expected:
        raise PortalFailure("identity_unverified")
    return expected


def snapshot(rows: list[list[str]], collection_evidence: dict | None = None) -> dict:
    terms, attempts, summary, unknown = [], [], [], []
    term = None
    for index, cells in enumerate(rows):
        cells = [str(cell) for cell in cells]
        joined = " ".join(cells)
        if re.match(r"\s*HỌC K[ỲÌ]\s+\d", joined, re.I):
            term = joined
            terms.append(term)
        elif len(cells) >= 7 and cells[0].strip().isdigit() and cells[1].strip():
            attempts.append({
                "row_key": str(index), "term": term, "code": cells[1],
                "name": cells[2], "credits": cells[3], "grade10": cells[4],
                "letter": cells[5], "grade4": cells[6], "cells": cells,
            })
        elif re.search(r"tổng|trung bình|tích lũy", joined, re.I):
            summary.append(cells)
        elif cells == ["Mã môn học"]:
            # Exact known table header, never a grade/course row or free-form text.
            continue
        else:
            unknown.append({"row_key": str(index), "cells": cells})
    if not attempts:
        raise PortalFailure("structure_changed")
    result = {"schema_version": 1, "connector_version": "b790d6af+identity1",
              "completeness": "unknown", "terms": terms, "attempts": attempts,
              "source_summary": summary, "unknown_rows": unknown, "rows": rows}
    if collection_evidence is not None:
        required = ("source_host_valid", "source_path_valid", "transcript_container_valid",
                    "filters_absent", "pagination_absent", "hidden_records_absent",
                    "virtualization_absent", "loading_absent", "network_idle")
        evidence = {key: collection_evidence.get(key) is True for key in required}
        evidence.update(layout_contract=collection_evidence.get("layout_contract"),
                        stable_reads=collection_evidence.get("stable_reads"),
                        data_table_count=collection_evidence.get("data_table_count"))
        result["collection_evidence"] = evidence
        result["connector_version"] = "vnu-full-table-20261025"
        if (all(evidence[key] for key in required) and not unknown
                and evidence["layout_contract"] == "vnu-full-table-20261025"
                and type(evidence["stable_reads"]) is int and evidence["stable_reads"] >= 3
                and type(evidence["data_table_count"]) is int and evidence["data_table_count"] == 1):
            result["completeness"] = "complete"
    result["digest"] = hashlib.sha256(
        json.dumps(result, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    return result
