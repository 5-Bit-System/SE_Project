"""Account-owned portal source snapshots, independent of academic catalogs."""

from alembic import op

revision = "hus_20261023_03"
down_revision = "hus_20261017_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE portal_users (
          id UUID PRIMARY KEY, provider TEXT NOT NULL DEFAULT 'vnu',
          subject TEXT NOT NULL, profile JSONB NOT NULL DEFAULT '{}',
          generation BIGINT NOT NULL DEFAULT 0,
          current_snapshot_id UUID,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          UNIQUE(provider, subject)
        );
        CREATE TABLE portal_transcript_snapshots (
          id UUID PRIMARY KEY, owner UUID NOT NULL REFERENCES portal_users(id) ON DELETE CASCADE,
          digest TEXT NOT NULL, completeness TEXT NOT NULL,
          payload JSONB NOT NULL, fetched_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          UNIQUE(owner, id), UNIQUE(owner, digest),
          CHECK(completeness IN ('unknown', 'partial', 'complete'))
        );
        ALTER TABLE portal_users ADD CONSTRAINT fk_portal_current_owner
          FOREIGN KEY(id, current_snapshot_id)
          REFERENCES portal_transcript_snapshots(owner, id) DEFERRABLE INITIALLY DEFERRED;
        CREATE TABLE portal_transcript_attempts (
          snapshot UUID NOT NULL REFERENCES portal_transcript_snapshots(id) ON DELETE CASCADE,
          row_key TEXT NOT NULL, source JSONB NOT NULL,
          PRIMARY KEY(snapshot, row_key)
        );
    """)


def downgrade() -> None:
    raise RuntimeError("Restore a reviewed backup rather than discard personal source data")
