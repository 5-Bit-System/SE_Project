"""Test-first placeholder; deliberately returns no imports for the RED run."""

from dataclasses import dataclass

from app.importing.batch import BatchResult, BatchStatus
from app.models import Catalog
from app.transcript import StudentTranscript


@dataclass(frozen=True)
class TranscriptImportResult:
    batch: BatchResult
    transcript: StudentTranscript


def import_transcript_csv(
    content: str, transcript: StudentTranscript, catalog: Catalog,
) -> TranscriptImportResult:
    return TranscriptImportResult(
        BatchResult(BatchStatus.COMPLETED, ()), transcript.model_copy(deep=True),
    )
