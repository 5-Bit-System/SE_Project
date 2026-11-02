import pytest

from app.importing.batch import BatchImportError, BatchStatus
from app.importing.transcript import import_transcript_csv
from app.rules import evaluate_eligibility
from app.transcript import StudentTranscript, TranscriptRecord
from tests.support.catalog_fixtures import mark_catalog_reviewed_for_test

HEADER = "course_code,grade,term\n"


def test_invalid_grade_between_valid_rows_preserves_both_and_original(toy_catalog):
    original = StudentTranscript(program_id="toy")
    result = import_transcript_csv(
        HEADER + "toy101,8,1\nTOY102,12,2\nTOY102,6,2\n", original, toy_catalog,
    )
    assert result.batch.imported_count == 2
    assert result.batch.rejected_count == 1
    assert result.batch.status is BatchStatus.PARTIAL
    assert result.batch.rows[1].line_number == 3
    assert result.batch.rows[1].error_code == "invalid_transcript_record"
    assert result.transcript.grade_map == {"TOY101": 8, "TOY102": 6}
    assert original.records == []
    assert all(isinstance(row, TranscriptRecord) for row in result.transcript.records)


def test_existing_grade_and_selection_are_preserved_without_aliasing(toy_catalog):
    original = StudentTranscript(
        program_id="toy", selected_track_id="synthetic-track",
        records=[TranscriptRecord(course_code="TOY101", grade=7)],
    )
    before = original.model_dump()
    result = import_transcript_csv(
        HEADER + "toy101,9,1\nTOY102,8,2\nTOY102,9,3\n", original, toy_catalog,
    )
    assert (result.batch.imported_count, result.batch.rejected_count) == (1, 2)
    assert result.transcript.grade_map == {"TOY101": 7, "TOY102": 8}
    assert result.transcript.selected_track_id == "synthetic-track"
    assert original.model_dump() == before
    result.transcript.records[0].grade = 1
    assert original.records[0].grade == 7


@pytest.mark.parametrize("grade", ["-1", "12", "nan", "inf", "bad", ""])
def test_real_model_rejects_invalid_grades_without_creating_records(toy_catalog, grade):
    result = import_transcript_csv(
        HEADER + f"TOY101,{grade},1\n", StudentTranscript(program_id="toy"), toy_catalog,
    )
    assert result.batch.status is BatchStatus.FAILED
    assert result.transcript.records == []


@pytest.mark.parametrize("row", [",8,1", "TOY101,8,13", "FOREIGN,8,1"])
def test_blank_code_invalid_term_and_foreign_course_are_rejected(toy_catalog, row):
    result = import_transcript_csv(
        HEADER + row + "\n", StudentTranscript(program_id="toy"), toy_catalog,
    )
    assert result.batch.rejected_count == 1
    assert result.transcript.records == []


def test_different_program_and_unknown_existing_course_reject_batch(toy_catalog):
    for original in (
        StudentTranscript(program_id="other"),
        StudentTranscript(program_id="toy", records=[TranscriptRecord(course_code="FOREIGN", grade=8)]),
    ):
        before = original.model_dump()
        with pytest.raises(BatchImportError):
            import_transcript_csv(HEADER + "TOY101,8,1\n", original, toy_catalog)
        assert original.model_dump() == before


@pytest.mark.parametrize("payload", ["code,grade,term\n", "course_code,grade,term,passed\nTOY101,8,1,true\n"])
def test_schema_is_checked_even_when_no_rows_exist(toy_catalog, payload):
    with pytest.raises(BatchImportError, match="schema"):
        import_transcript_csv(payload, StudentTranscript(program_id="toy"), toy_catalog)


def test_header_only_is_completed_and_optional_term_stays_none(toy_catalog):
    original = StudentTranscript(program_id="toy")
    empty = import_transcript_csv(HEADER, original, toy_catalog)
    assert empty.batch.status is BatchStatus.COMPLETED
    assert empty.batch.rows == ()
    result = import_transcript_csv(HEADER + "TOY101,0,\nTOY102,10,12\n", original, toy_catalog)
    assert result.batch.imported_count == 2
    assert result.transcript.records[0].term is None
    assert result.transcript.failed_course_codes == {"TOY101"}


@pytest.mark.parametrize("grade,unlocked", [(4.9, False), (5.0, True)])
def test_imported_transcript_uses_existing_passing_rule_and_eligibility(toy_catalog, grade, unlocked):
    catalog = mark_catalog_reviewed_for_test(toy_catalog)
    original = StudentTranscript(program_id="toy")
    before = evaluate_eligibility(catalog, original.passed_course_codes).model_dump()
    result = import_transcript_csv(HEADER + f"TOY101,{grade},1\n", original, catalog)
    available = evaluate_eligibility(catalog, result.transcript.passed_course_codes)
    assert ("TOY102" in {row.code for row in available.eligible_courses}) is unlocked
    assert evaluate_eligibility(catalog, original.passed_course_codes).model_dump() == before


def test_import_does_not_promote_unreviewed_catalog_metadata(toy_catalog):
    result = import_transcript_csv(HEADER + "TOY101,9,1\n", StudentTranscript(program_id="toy"), toy_catalog)
    assert result.batch.imported_count == 1
    assert evaluate_eligibility(toy_catalog, result.transcript.passed_course_codes).eligible_courses == []
