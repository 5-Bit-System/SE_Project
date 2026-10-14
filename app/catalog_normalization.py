"""One source-contract boundary shared by JSON import and PostgreSQL reads."""

from typing import Any

from pydantic import ValidationError

from app.errors import StorageDataError
from app.models import Catalog, Course, Program
from app.schemas.metadata import CourseEnvelope


def normalize_catalog(
    program_doc: dict[str, Any],
    course_document: Any,
    vocabulary_doc: dict[str, Any] | None = None,
) -> Catalog:
    try:
        if not isinstance(program_doc, dict) or (
            vocabulary_doc is not None and not isinstance(vocabulary_doc, dict)
        ):
            raise ValueError("Curriculum and vocabulary must be JSON objects")
        if isinstance(course_document, dict):
            envelope = CourseEnvelope.model_validate(course_document)
            if envelope.metadata_schema_version != "1.0" or envelope.vocabulary_version != "1.0":
                raise ValueError("Unsupported metadata/vocabulary version")
            if (
                not vocabulary_doc
                or vocabulary_doc.get("vocabulary_version") != envelope.vocabulary_version
            ):
                raise ValueError("Envelope requires matching vocabulary")
            for key in (
                "program_id",
                "catalog_revision",
                "metadata_schema_version",
                "vocabulary_version",
            ):
                expected = program_doc.get(key)
                if expected is None or expected != getattr(envelope, key):
                    raise ValueError(f"Curriculum/envelope {key} mismatch")
            catalog = Catalog(
                program=Program.model_validate(program_doc),
                courses=[Course.model_validate(c.model_dump()) for c in envelope.courses],
                metadata_schema_version=envelope.metadata_schema_version,
                vocabulary_version=envelope.vocabulary_version,
                vocabulary=vocabulary_doc,
            )
        elif isinstance(course_document, list):
            courses = []
            for item in course_document:
                if not isinstance(item, dict):
                    raise ValueError("Legacy course must be object")
                values = dict(item)
                values["prerequisite_status"] = {
                    "transcribed": "draft_unverified",
                    "source_conflict": "conflict",
                }.get(
                    values.get("prerequisite_status"),
                    values.get("prerequisite_status", "draft_unverified"),
                )
                values["field_evidence"] = values.get("field_evidence") or {}
                courses.append(Course.model_validate(values))
            catalog = Catalog(program=Program.model_validate(program_doc), courses=courses)
        else:
            raise ValueError("courses document must be envelope or legacy list")
        from app.catalog_validation import validate_catalog

        validate_catalog(catalog, vocabulary_doc)
        return catalog
    except (ValidationError, ValueError, TypeError, KeyError) as exc:
        raise StorageDataError(f"Invalid catalog source contract: {exc}") from None
