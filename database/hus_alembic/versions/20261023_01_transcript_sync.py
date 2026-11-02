"""Track the last successful transcript synchronization per student.

Revision ID: hus_20261023_01
Revises: hus_20261017_02
"""

from alembic import op

revision = "hus_20261023_01"
down_revision = "hus_20261017_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Allow adoption if the documented ALTER TABLE was already applied manually.
    op.execute("""
        ALTER TABLE public.students
          ADD COLUMN IF NOT EXISTS last_transcript_synced_at TIMESTAMPTZ NULL;
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'students'
              AND column_name = 'last_transcript_synced_at'
              AND data_type = 'timestamp with time zone'
              AND is_nullable = 'YES' AND column_default IS NULL
          ) THEN
            RAISE EXCEPTION 'students.last_transcript_synced_at has an incompatible definition';
          END IF;
        END $$;
    """)


def downgrade() -> None:
    raise RuntimeError("Downgrade would discard transcript synchronization timestamps")
