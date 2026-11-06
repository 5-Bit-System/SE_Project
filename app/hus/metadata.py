"""Evidence-bound applicability metadata, separate from crawler guesses and answer review."""

import hashlib
import re
from typing import Literal
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict

from app.hus.cleaning import infer_attachment_major, infer_major
from app.hus.models import (
    ApplicabilityMetadata, HUSDocument, MajorCategory, MetadataEvidence, MetadataField,
)

METADATA_FIELDS = (
    "major", "education_level", "program", "program_variant", "admission_cohort",
    "academic_year", "validity_status", "effective_from", "effective_to",
)


class ApplicabilityFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["1.0"] = "1.0"
    source_snapshot_id: str
    documents: dict[str, ApplicabilityMetadata]


def locator(field: str, text: str, start: int = 0, end: int | None = None) -> MetadataEvidence:
    end = len(text) if end is None else end
    return MetadataEvidence(field=field, start=start, end=end, quote=text[start:end])


def propose_fields(
    title: str, url: str, content: str, *, parent_url: str | None = None,
    parent_major: MajorCategory = MajorCategory.UNKNOWN,
) -> ApplicabilityMetadata:
    major = (infer_attachment_major(url, content, parent_major=parent_major)
             if parent_url else infer_major(title, url, content))
    proposal = MetadataField(
        proposed=major.value, proposal_method="classification_rules_v2",
        proposal_evidence=([locator("source_url", url)] + ([locator("title", title)] if title else []))
        if major != MajorCategory.UNKNOWN else [],
    )
    if parent_url and infer_major(Path(urlsplit(url).path).name, url, content) == MajorCategory.UNKNOWN:
        proposal.proposal_method = "parent_inheritance" if parent_major != MajorCategory.UNKNOWN else "unknown"
        proposal.proposal_evidence = [locator("parent_url", parent_url)] if parent_major != MajorCategory.UNKNOWN else []
    result = ApplicabilityMetadata(source_url=url, content_hash=hashlib.sha256(content.encode()).hexdigest(),
                                   major=proposal)
    # Only explicit title wording, never fetched_at, a URL year, or all body years.
    levels = []
    for pattern, value in ((r"thạc sĩ|\bmaster\b", "master"), (r"tiến sĩ|\bdoctoral\b|\bphd\b", "doctoral"),
                           (r"đại học|cử nhân|\bbachelor\b", "undergraduate")):
        match = re.search(pattern, title, re.I)
        if match:
            levels.append((value, locator("title", title, *match.span())))
    if len(levels) == 1:
        result.education_level = MetadataField(proposed=levels[0][0], proposal_method="explicit_title",
                                               proposal_evidence=[levels[0][1]])
    elif levels:
        result.education_level = MetadataField(proposal_method="mixed_levels_need_review",
                                               proposal_evidence=[evidence for _, evidence in levels])
    for name, pattern in (("admission_cohort", r"khóa\s+(K\d+|\d{4})\b"),
                           ("academic_year", r"năm học\s+(\d{4}\s*[-–]\s*\d{4})")):
        match = re.search(pattern, title, re.I)
        if match:
            setattr(result, name, MetadataField(proposed=match.group(1), proposal_method="explicit_title",
                                                proposal_evidence=[locator("title", title, *match.span())]))
    return result


def propose_metadata(doc: HUSDocument, parent_major: MajorCategory = MajorCategory.UNKNOWN) -> ApplicabilityMetadata:
    return propose_fields(doc.title, doc.url, doc.content, parent_url=doc.parent_url, parent_major=parent_major)


def validate_metadata(doc: HUSDocument, metadata: ApplicabilityMetadata) -> ApplicabilityMetadata:
    metadata = ApplicabilityMetadata.model_validate(metadata.model_dump())
    has_values = any(getattr(metadata, name).proposed != "unknown" or
                     getattr(metadata, name).verified != "unknown" for name in METADATA_FIELDS)
    if has_values or metadata.source_url is not None or metadata.content_hash is not None:
        if metadata.source_url != doc.url or metadata.content_hash != doc.content_hash:
            raise ValueError("Applicability metadata belongs to different source content")
    for name in METADATA_FIELDS:
        field = getattr(metadata, name)
        for evidence in field.proposal_evidence + field.evidence:
            source = getattr(doc, evidence.field) or ""
            if evidence.end > len(source) or source[evidence.start:evidence.end] != evidence.quote:
                raise ValueError(f"Metadata evidence locator does not match source: {name}")
    return metadata


def metadata_for(doc: HUSDocument) -> ApplicabilityMetadata:
    metadata = doc.applicability if doc.applicability != ApplicabilityMetadata() else propose_metadata(doc)
    return validate_metadata(doc, metadata)


def assign_proposal(doc: HUSDocument, parent_major: MajorCategory = MajorCategory.UNKNOWN) -> None:
    proposal = propose_metadata(doc, parent_major)
    # Preserve previously reviewed fields only when still bound to the exact same source.
    if doc.applicability.content_hash is not None:
        old = validate_metadata(doc, doc.applicability)
        for name in METADATA_FIELDS:
            reviewed = getattr(old, name)
            if reviewed.verified != "unknown":
                fresh = getattr(proposal, name)
                setattr(proposal, name, reviewed.model_copy(update={
                    "proposed": fresh.proposed, "proposal_method": fresh.proposal_method,
                    "proposal_evidence": fresh.proposal_evidence,
                }))
    doc.applicability = validate_metadata(doc, proposal)
    doc.major = MajorCategory(proposal.major.proposed)
