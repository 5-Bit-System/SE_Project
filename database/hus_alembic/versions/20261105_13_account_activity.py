"""Account-scoped consultation events without conversation content."""

from alembic import op

revision = "hus_20261105_13"
down_revision = "hus_20261101_12"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE account_activity_events (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
            kind TEXT NOT NULL CHECK (kind IN ('advisor', 'recommendation')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_account_activity_recent
            ON account_activity_events(account_id, created_at DESC, id DESC);
        CREATE INDEX ix_auth_audit_account_history
            ON auth_audit_events(target_id, created_at DESC)
            WHERE action IN ('login', 'login_vnu', 'logout');
    """)


def downgrade():
    raise RuntimeError("Restore a reviewed backup rather than discard account activity")
