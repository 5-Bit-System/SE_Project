"""Versioned catalogs; composite foreign keys enforce revision isolation.

JSON payloads retain source facts that are not yet normalized. Courses,
prerequisites and memberships used by the runtime have relational keys.
Session chat and user-entered transcripts are deliberately not persisted.
"""

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)
payload_type = JSON().with_variant(JSONB(), "postgresql")

programs = Table(
    "programs",
    metadata,
    Column("program_id", String(80), primary_key=True),
    Column("name", String(200), nullable=False),
)
catalog_revisions = Table(
    "catalog_revisions",
    metadata,
    Column("revision_id", String(64), primary_key=True),
    Column("program_id", String(80), ForeignKey("programs.program_id"), nullable=False),
    Column("active", Boolean, nullable=False, server_default=text("false")),
    Column("payload", payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index(
    "uq_active_catalog_per_program",
    catalog_revisions.c.program_id,
    unique=True,
    postgresql_where=catalog_revisions.c.active.is_(True),
    sqlite_where=catalog_revisions.c.active.is_(True),
)
courses = Table(
    "courses",
    metadata,
    Column(
        "revision_id", String(64), ForeignKey("catalog_revisions.revision_id"), primary_key=True
    ),
    Column("code", String(30), primary_key=True),
    Column("position", Integer, nullable=False),
    Column("name", String(300), nullable=False),
    Column("credits", Integer, nullable=False),
    Column("block", String(80), nullable=False),
    Column("payload", payload_type, nullable=False),
    CheckConstraint("credits > 0", name="positive_credits"),
    UniqueConstraint("revision_id", "position"),
)


def course_fk(*, code_column: str = "course_code") -> ForeignKeyConstraint:
    return ForeignKeyConstraint(
        ["revision_id", code_column], ["courses.revision_id", "courses.code"]
    )


course_sources = Table(
    "course_sources",
    metadata,
    Column("revision_id", String(64), primary_key=True),
    Column("course_code", String(30), primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("source_page", Integer, nullable=False),
    Column("payload", payload_type, nullable=False),
    course_fk(),
)
choice_groups = Table(
    "choice_groups",
    metadata,
    Column(
        "revision_id", String(64), ForeignKey("catalog_revisions.revision_id"), primary_key=True
    ),
    Column("group_id", String(100), primary_key=True),
    Column("required_credits", Integer, nullable=False),
    Column("selection_mode", String(60), nullable=False),
    Column("payload", payload_type, nullable=False),
    CheckConstraint("required_credits >= 0", name="nonnegative_quota"),
)
choice_group_courses = Table(
    "choice_group_courses",
    metadata,
    Column("revision_id", String(64), primary_key=True),
    Column("group_id", String(100), primary_key=True),
    Column("course_code", String(30), primary_key=True),
    Column("position", Integer, nullable=False),
    ForeignKeyConstraint(
        ["revision_id", "group_id"], ["choice_groups.revision_id", "choice_groups.group_id"]
    ),
    course_fk(),
)
prerequisite_groups = Table(
    "prerequisite_groups",
    metadata,
    Column("revision_id", String(64), primary_key=True),
    Column("course_code", String(30), primary_key=True),
    Column("group_no", Integer, primary_key=True),
    Column("source_status", String(40), nullable=False),
    course_fk(),
    CheckConstraint("group_no >= 0", name="nonnegative_group"),
)
prerequisite_options = Table(
    "prerequisite_options",
    metadata,
    Column("revision_id", String(64), primary_key=True),
    Column("course_code", String(30), primary_key=True),
    Column("group_no", Integer, primary_key=True),
    Column("option_no", Integer, primary_key=True),
    Column("required_code", String(30), nullable=True),
    Column("external_code", String(30), nullable=True),
    Column("verification_status", String(40), nullable=False),
    ForeignKeyConstraint(
        ["revision_id", "course_code", "group_no"],
        [
            "prerequisite_groups.revision_id",
            "prerequisite_groups.course_code",
            "prerequisite_groups.group_no",
        ],
    ),
    course_fk(code_column="required_code"),
    CheckConstraint(
        "(required_code IS NOT NULL AND external_code IS NULL) OR "
        "(required_code IS NULL AND external_code IS NOT NULL)",
        name="one_reference",
    ),
    CheckConstraint(
        "external_code IS NULL OR verification_status = 'unverified'",
        name="external_unverified",
    ),
)
tracks = Table(
    "tracks",
    metadata,
    Column(
        "revision_id", String(64), ForeignKey("catalog_revisions.revision_id"), primary_key=True
    ),
    Column("track_id", String(100), primary_key=True),
    Column("payload", payload_type, nullable=False),
)
track_choice_groups = Table(
    "track_choice_groups",
    metadata,
    Column("revision_id", String(64), primary_key=True),
    Column("track_id", String(100), primary_key=True),
    Column("group_id", String(100), primary_key=True),
    ForeignKeyConstraint(["revision_id", "track_id"], ["tracks.revision_id", "tracks.track_id"]),
    ForeignKeyConstraint(
        ["revision_id", "group_id"], ["choice_groups.revision_id", "choice_groups.group_id"]
    ),
)
graduation_paths = Table(
    "graduation_paths",
    metadata,
    Column(
        "revision_id", String(64), ForeignKey("catalog_revisions.revision_id"), primary_key=True
    ),
    Column("path_id", String(100), primary_key=True),
    Column("payload", payload_type, nullable=False),
)
graduation_path_courses = Table(
    "graduation_path_courses",
    metadata,
    Column("revision_id", String(64), primary_key=True),
    Column("path_id", String(100), primary_key=True),
    Column("course_code", String(30), primary_key=True),
    ForeignKeyConstraint(
        ["revision_id", "path_id"], ["graduation_paths.revision_id", "graduation_paths.path_id"]
    ),
    course_fk(),
)
graduation_path_tracks = Table(
    "graduation_path_tracks",
    metadata,
    Column("revision_id", String(64), primary_key=True),
    Column("path_id", String(100), primary_key=True),
    Column("track_id", String(100), primary_key=True),
    ForeignKeyConstraint(
        ["revision_id", "path_id"], ["graduation_paths.revision_id", "graduation_paths.path_id"]
    ),
    ForeignKeyConstraint(["revision_id", "track_id"], ["tracks.revision_id", "tracks.track_id"]),
)
demo_profiles = Table(
    "demo_profiles",
    metadata,
    Column(
        "revision_id", String(64), ForeignKey("catalog_revisions.revision_id"), primary_key=True
    ),
    Column("profile_id", String(80), primary_key=True),
    Column("payload", payload_type, nullable=False),
)
transcript_records = Table(
    "transcript_records",
    metadata,
    Column("revision_id", String(64), primary_key=True),
    Column("profile_id", String(80), primary_key=True),
    Column("course_code", String(30), primary_key=True),
    Column("position", Integer, nullable=False),
    Column("grade", Float, nullable=True),
    Column("passed", Boolean, nullable=False),
    Column("term", Integer, nullable=False),
    Column("payload", payload_type, nullable=False),
    ForeignKeyConstraint(
        ["revision_id", "profile_id"], ["demo_profiles.revision_id", "demo_profiles.profile_id"]
    ),
    course_fk(),
    CheckConstraint("grade IS NULL OR (grade >= 0 AND grade <= 10)", name="grade_range"),
    CheckConstraint("term >= 1 AND term <= 12", name="term_range"),
    CheckConstraint("grade IS NULL OR passed = (grade >= 5)", name="pass_matches_grade"),
    UniqueConstraint("revision_id", "profile_id", "position"),
)
