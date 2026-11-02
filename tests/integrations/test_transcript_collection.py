"""Completeness requires every source-layout check, not counts or a user flag."""

import copy

import pytest

from app.integrations.daotao.snapshot import PortalFailure, snapshot

ROWS = [["HỌC KỲ 1 - 2099-2100"], ["1", "TEST001", "Invented course", "3", "7.5", "B", "3"],
        ["Tổng tín chỉ: 3"]]


def evidence():
    return dict.fromkeys(("source_host_valid", "source_path_valid", "transcript_container_valid",
                          "filters_absent", "pagination_absent", "hidden_records_absent",
                          "virtualization_absent", "loading_absent", "network_idle"), True) | {
                              "layout_contract": "vnu-full-table-20261025", "stable_reads": 3,
                              "data_table_count": 1}


def test_complete_capture_preserves_rows_values_and_idempotent_digest():
    original = copy.deepcopy(ROWS)
    result = snapshot(ROWS, evidence())
    assert result["completeness"] == "complete"
    assert result["rows"] == original == ROWS
    assert result["digest"] == snapshot(ROWS, evidence())["digest"]
    assert snapshot(ROWS)["completeness"] == "unknown"


@pytest.mark.parametrize("key", list(evidence()))
def test_one_missing_or_false_source_check_prevents_complete(key):
    checks = evidence()
    checks.pop(key)
    assert snapshot(ROWS, checks)["completeness"] == "unknown"


@pytest.mark.parametrize("changes", [{"filters_absent": "true"}, {"stable_reads": True},
    {"stable_reads": 2}, {"data_table_count": True}, {"data_table_count": 2},
    {"pagination_absent": False}, {"network_idle": False}])
def test_truthy_values_or_incomplete_capture_cannot_bypass_the_contract(changes):
    assert snapshot(ROWS, {**evidence(), **changes})["completeness"] == "unknown"


def test_unparsed_source_rows_and_empty_sources_are_not_marked_complete():
    result = snapshot([*ROWS, ["Unexpected source row"]], evidence())
    assert result["completeness"] == "unknown"
    assert result["unknown_rows"][0]["cells"] == ["Unexpected source row"]
    with pytest.raises(PortalFailure, match="structure_changed"):
        snapshot([], evidence())
