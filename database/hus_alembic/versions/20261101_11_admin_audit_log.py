"""Privileged admin action audit logging."""

from alembic import op

revision = "hus_20261101_11"
down_revision = "hus_20261101_10"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE admin_audit_logs (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            actor_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
            actor_email TEXT,
            action TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            result TEXT NOT NULL DEFAULT 'ok',
            summary TEXT NOT NULL,
            details JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(details) = 'object'),
            ip_address TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX ix_admin_audit_logs_action ON admin_audit_logs(action);
        CREATE INDEX ix_admin_audit_logs_target ON admin_audit_logs(target_type, target_id);
        CREATE INDEX ix_admin_audit_logs_created_at ON admin_audit_logs(created_at DESC);
        CREATE INDEX ix_admin_audit_logs_actor ON admin_audit_logs(actor_id);
    """)


def downgrade():
    op.execute("""
        DROP TABLE IF EXISTS admin_audit_logs;
    """)
