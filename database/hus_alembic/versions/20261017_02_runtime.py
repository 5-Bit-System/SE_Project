"""Runtime facts and immutable catalog snapshots.

Revision ID: hus_20261017_02
Revises: hus_20261017_01
"""

from alembic import op

revision = "hus_20261017_02"
down_revision = "hus_20261017_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE curricula ADD COLUMN program_id TEXT;
        ALTER TABLE curricula ADD COLUMN runtime_rules JSONB;
        ALTER TABLE curricula ADD CONSTRAINT ck_hus_runtime_rules_object
          CHECK (runtime_rules IS NULL OR jsonb_typeof(runtime_rules) = 'object');
        CREATE UNIQUE INDEX uq_hus_curricula_program_id ON curricula(program_id)
          WHERE program_id IS NOT NULL;
        ALTER TABLE curriculum_courses ADD COLUMN applicable_credits SMALLINT;
        ALTER TABLE curriculum_courses ADD COLUMN counted_in_total BOOLEAN;
        ALTER TABLE curriculum_courses ADD COLUMN runtime_metadata JSONB;
        ALTER TABLE curriculum_courses ADD COLUMN prerequisite_state TEXT;
        ALTER TABLE curriculum_courses ADD CONSTRAINT ck_hus_applicable_credits
          CHECK (applicable_credits IS NULL OR applicable_credits >= 0);
        ALTER TABLE curriculum_courses ADD CONSTRAINT ck_hus_metadata_object
          CHECK (runtime_metadata IS NULL OR jsonb_typeof(runtime_metadata) = 'object');
        CREATE TABLE hus_catalog_revisions (
          revision_id TEXT PRIMARY KEY,
          curriculum_id BIGINT NOT NULL REFERENCES curricula(curriculum_id),
          program_id TEXT NOT NULL,
          active BOOLEAN NOT NULL DEFAULT false,
          source_digest TEXT NOT NULL,
          payload JSONB NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_hus_revision_hash CHECK (revision_id ~ '^[a-f0-9]{64}$'),
          CONSTRAINT ck_hus_source_hash CHECK (source_digest ~ '^[a-f0-9]{64}$'),
          CONSTRAINT ck_hus_payload_object CHECK (jsonb_typeof(payload) = 'object')
        );
        CREATE UNIQUE INDEX uq_hus_active_program ON hus_catalog_revisions(program_id)
          WHERE active;
        CREATE UNIQUE INDEX uq_hus_active_curriculum ON hus_catalog_revisions(curriculum_id)
          WHERE active;
        CREATE INDEX ix_hus_revisions_curriculum ON hus_catalog_revisions(curriculum_id);
    """)


def downgrade() -> None:
    raise RuntimeError("HUS runtime downgrade would discard catalog snapshots")
