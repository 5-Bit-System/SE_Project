import pytest

from app.importing.batch import (
    BatchImportError,
    BatchStatus,
    RowImportError,
    RowStatus,
    import_csv,
)


def test_all_valid_rows_reach_handler_once_and_complete():
    saved = []
    result = import_csv("code,name\nA,Alpha\nB,Beta\n", saved.append)
    assert [row["code"] for row in saved] == ["A", "B"]
    assert [row.line_number for row in result.rows] == [2, 3]
    assert all(row.status is RowStatus.IMPORTED for row in result.rows)
    assert result.status is BatchStatus.COMPLETED
    assert (result.imported_count, result.rejected_count) == (2, 0)


def test_middle_row_failure_does_not_lose_valid_rows_before_or_after():
    saved = []

    def persist(row):
        if row["code"] == "BAD":
            raise RowImportError("invalid record")
        saved.append(row["code"])

    result = import_csv("code\nGOOD1\nBAD\nGOOD2\n", persist)
    assert saved == ["GOOD1", "GOOD2"]
    assert [row.status for row in result.rows] == [RowStatus.IMPORTED, RowStatus.REJECTED, RowStatus.IMPORTED]
    assert result.rows[1].line_number == 3
    assert result.status is BatchStatus.PARTIAL
    assert (result.imported_count, result.rejected_count) == (2, 1)


def test_all_record_errors_produce_failed_batch_summary():
    result = import_csv("code\nA\nB\n", lambda _: (_ for _ in ()).throw(RowImportError("bad")))
    assert result.status is BatchStatus.FAILED
    assert (result.imported_count, result.rejected_count) == (0, 2)


def test_header_only_batch_is_completed_with_no_rows():
    calls = []
    result = import_csv("code,name\n", calls.append)
    assert result.status is BatchStatus.COMPLETED
    assert result.rows == ()
    assert calls == []


@pytest.mark.parametrize("payload", ["", "\nA\n", "code,code\nA,B\n"])
def test_blank_or_duplicate_headers_fail_before_any_side_effect(payload):
    calls = []
    with pytest.raises(BatchImportError):
        import_csv(payload, calls.append)
    assert calls == []


def test_malformed_csv_fails_before_any_side_effect():
    calls = []
    with pytest.raises(BatchImportError):
        import_csv('code,name\nA,"unterminated\n', calls.append)
    assert calls == []


def test_utf8_size_limit_fails_before_any_side_effect():
    calls = []
    with pytest.raises(BatchImportError, match="size"):
        import_csv("code,name\n" + "é" * (1024 * 1024), calls.append)
    assert calls == []


def test_row_count_limit_fails_before_any_side_effect():
    calls = []
    payload = "code\n" + "A\n" * 5001
    with pytest.raises(BatchImportError, match="row"):
        import_csv(payload, calls.append)
    assert calls == []


def test_handler_system_failure_is_not_misreported_as_bad_data():
    calls = []

    def persist(row):
        calls.append(row["code"])
        if row["code"] == "DB_DOWN":
            raise OSError("database unavailable")

    with pytest.raises(OSError, match="database unavailable"):
        import_csv("code\nOK\nDB_DOWN\nLATER\n", persist)
    assert calls == ["OK", "DB_DOWN"]


def test_summary_status_and_count_invariants_across_transitions():
    scenarios = [
        ("A\nB\n", {"A", "B"}, BatchStatus.COMPLETED, 2, 0),
        ("A\n", set(), BatchStatus.FAILED, 0, 1),
        ("A\nB\n", {"A"}, BatchStatus.PARTIAL, 1, 1),
    ]
    for codes, accepted, expected_status, imported, rejected in scenarios:
        def persist(row):
            if row["code"] not in accepted:
                raise RowImportError("invalid")

        result = import_csv("code\n" + codes, persist)
        assert result.status is expected_status
        assert result.imported_count == imported
        assert result.rejected_count == rejected
        assert result.imported_count + result.rejected_count == len(result.rows)


def test_whitespace_header_cell_is_rejected_before_side_effects():
    calls = []
    with pytest.raises(BatchImportError, match="csv_header_blank"):
        import_csv("code, ,name\nA,x,Alpha\n", calls.append)
    assert calls == []


@pytest.mark.parametrize("bad_row", ["B", "B,Beta,extra"])
def test_row_width_mismatch_after_valid_row_has_zero_side_effects(bad_row):
    calls = []
    with pytest.raises(BatchImportError, match="csv_row_width_mismatch"):
        import_csv(f"code,name\nA,Alpha\n{bad_row}\n", calls.append)
    assert calls == []


def test_invalid_unicode_is_rejected_before_side_effects():
    calls = []
    with pytest.raises(BatchImportError, match="invalid_unicode"):
        import_csv("code\n\ud800\n", calls.append)
    assert calls == []
