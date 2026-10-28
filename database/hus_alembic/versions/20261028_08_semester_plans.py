"""Account-owned semester plan alternatives with optimistic versioning."""

from alembic import op

revision = 'hus_20261028_08'
down_revision = 'hus_20261028_07'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE semester_plans (
          id UUID PRIMARY KEY,
          account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
          title TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 100),
          academic_year_start INTEGER NOT NULL CHECK (academic_year_start BETWEEN 2000 AND 2100),
          semester SMALLINT NOT NULL CHECK (semester BETWEEN 1 AND 3),
          program_id TEXT NOT NULL,
          selected_track_id TEXT,
          selected_graduation_path_id TEXT,
          max_credits SMALLINT NOT NULL CHECK (max_credits BETWEEN 1 AND 30),
          total_credits SMALLINT NOT NULL CHECK (total_credits BETWEEN 0 AND max_credits),
          courses JSONB NOT NULL CHECK (jsonb_typeof(courses) = 'array'),
          basis JSONB NOT NULL CHECK (jsonb_typeof(basis) = 'object'),
          version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_semester_plans_account ON semester_plans(account_id, updated_at DESC);
    """)


def downgrade():
    raise RuntimeError('Restore a reviewed backup rather than discard saved semester plans')
