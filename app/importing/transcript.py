"""In-memory CSV adapter to existing transcript models; no persistence or API."""

from dataclasses import dataclass

from pydantic import ValidationError

from app.importing.batch import BatchImportError, BatchResult, RowImportError, import_csv
from app.models import Catalog
from app.transcript import StudentTranscript, TranscriptRecord, resolve_program_id

TRANSCRIPT_COLUMNS = ("course_code", "grade", "term")


@dataclass(frozen=True)
class TranscriptImportResult:
    batch: BatchResult
    transcript: StudentTranscript


def import_transcript_csv(
    content: str, transcript: StudentTranscript, catalog: Catalog,
) -> TranscriptImportResult:
    """Return a new transcript; never overwrite existing courses or mutate input.

    CSV requires numeric grade (0..10); empty term means unknown. Reuse real
    model validators/passing rules. Catalog membership is not source approval.
    Duplicate courses are row rejections, consistent with unsupported retakes.
    """
    if transcript.program_id != resolve_program_id(catalog.program.program_id):
        raise BatchImportError("transcript_program_mismatch")
    allowed = {course.code for course in catalog.courses}
    if transcript.all_course_codes - allowed:
        raise BatchImportError("existing_transcript_foreign_course")
    updated = transcript.model_copy(deep=True)
    seen = updated.all_course_codes

    def accept(row: dict[str, str]) -> None:
        try:
            record = TranscriptRecord(
                course_code=row["course_code"], grade=row["grade"],
                term=row["term"].strip() or None,
            )
        except ValidationError:
            raise RowImportError("invalid_transcript_record") from None
        if record.course_code not in allowed:
            raise RowImportError("foreign_course_code")
        if record.course_code in seen:
            raise RowImportError("duplicate_course_code")
        updated.records.append(record)
        seen.add(record.course_code)

    batch = import_csv(content, accept, expected_columns=TRANSCRIPT_COLUMNS)
    return TranscriptImportResult(
        batch, StudentTranscript.model_validate(updated.model_dump()),
    )
