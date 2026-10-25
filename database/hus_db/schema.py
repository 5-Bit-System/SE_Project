"""HUS runtime columns and snapshot table (source tables retain their SQL DDL)."""

from sqlalchemy import BigInteger, Boolean, Column, Index, MetaData, Table, Text
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()
catalog_revisions = Table(
    "hus_catalog_revisions",
    metadata,
    Column("revision_id", Text, primary_key=True),
    Column("curriculum_id", BigInteger, nullable=False),
    Column("program_id", Text, nullable=False),
    Column("active", Boolean, nullable=False, server_default="false"),
    Column("source_digest", Text, nullable=False),
    Column("payload", JSONB, nullable=False),
)
Index("uq_hus_active_program", catalog_revisions.c.program_id, unique=True,
      postgresql_where=catalog_revisions.c.active.is_(True))
Index("uq_hus_active_curriculum", catalog_revisions.c.curriculum_id, unique=True,
      postgresql_where=catalog_revisions.c.active.is_(True))
