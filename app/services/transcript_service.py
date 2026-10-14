"""Service xử lý bảng điểm và hồ sơ học tập."""


from app.transcript import (
    PROGRAM_ALIASES,
    StudentTranscript,
    TranscriptRecord,
    resolve_program_id,
)

__all__ = [
    "PROGRAM_ALIASES",
    "StudentTranscript",
    "TranscriptRecord",
    "resolve_program_id",
]
