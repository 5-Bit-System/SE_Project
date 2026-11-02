"""Small CSV import harness with explicit batch and row outcomes.

The caller owns persistence and must commit each row independently. This module
validates the complete CSV shape before invoking the handler so malformed batch
structure cannot produce partial side effects.
"""

import csv
import io
from dataclasses import dataclass
from enum import StrEnum
from typing import Callable

MAX_CSV_BYTES = 1024 * 1024
MAX_ROWS = 5000


class BatchImportError(ValueError):
    """The batch cannot safely be parsed; no row handler has run."""


class RowImportError(ValueError):
    """Expected row-level validation or persistence rejection."""

    def __init__(self, code: str = "invalid_row"):
        self.code = code[:64]
        super().__init__(self.code)


class RowStatus(StrEnum):
    IMPORTED = "imported"
    REJECTED = "rejected"


class BatchStatus(StrEnum):
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class RowOutcome:
    line_number: int
    status: RowStatus
    error_code: str | None = None


@dataclass(frozen=True)
class BatchResult:
    status: BatchStatus
    rows: tuple[RowOutcome, ...]

    @property
    def imported_count(self) -> int:
        return sum(row.status is RowStatus.IMPORTED for row in self.rows)

    @property
    def rejected_count(self) -> int:
        return sum(row.status is RowStatus.REJECTED for row in self.rows)


def _parse_records(
    content: str, expected_columns: tuple[str, ...] | None = None,
) -> list[tuple[int, dict[str, str]]]:
    if not isinstance(content, str):
        raise BatchImportError("content_must_be_text")
    try:
        size = len(content.encode("utf-8-sig"))
    except UnicodeEncodeError:
        raise BatchImportError("invalid_unicode") from None
    if size > MAX_CSV_BYTES:
        raise BatchImportError("csv_size_limit_exceeded")
    if not content:
        raise BatchImportError("csv_empty")

    try:
        reader = csv.reader(io.StringIO(content, newline=""), strict=True)
        header = next(reader, None)
        if not header:
            raise BatchImportError("csv_header_missing")
        normalized = [item.strip() for item in header]
        if any(not item for item in normalized):
            raise BatchImportError("csv_header_blank")
        if len({item.casefold() for item in normalized}) != len(normalized):
            raise BatchImportError("csv_header_duplicate")
        if expected_columns is not None and tuple(normalized) != expected_columns:
            raise BatchImportError("csv_header_schema")

        records = []
        for values in reader:
            if not values:
                continue
            if len(values) != len(normalized):
                raise BatchImportError("csv_row_width_mismatch")
            records.append((reader.line_num, dict(zip(normalized, values, strict=True))))
            if len(records) > MAX_ROWS:
                raise BatchImportError("csv_row_limit_exceeded")
    except csv.Error:
        raise BatchImportError("csv_malformed") from None
    return records


def import_csv(
    content: str, handler: Callable[[dict[str, str]], object], *,
    expected_columns: tuple[str, ...] | None = None,
) -> BatchResult:
    """Parse a bounded CSV, then process rows independently in source order.

    `handler` should raise RowImportError for an expected record failure. Other
    exceptions indicate a systemic failure and propagate, while earlier
    independently committed rows remain committed by the caller.
    """
    records = _parse_records(content, expected_columns)
    outcomes = []
    for line_number, record in records:
        try:
            handler(record)
        except RowImportError as error:
            outcomes.append(RowOutcome(line_number, RowStatus.REJECTED, error.code))
        else:
            outcomes.append(RowOutcome(line_number, RowStatus.IMPORTED))

    imported = sum(row.status is RowStatus.IMPORTED for row in outcomes)
    rejected = len(outcomes) - imported
    status = (
        BatchStatus.PARTIAL if imported and rejected
        else BatchStatus.FAILED if rejected
        else BatchStatus.COMPLETED
    )
    return BatchResult(status, tuple(outcomes))
