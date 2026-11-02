"""Local system accounts, email verification and explicit VNU ownership."""

from alembic import op

revision = "hus_20261025_04"
down_revision = "hus_20261023_03"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE accounts ADD COLUMN id UUID NOT NULL DEFAULT gen_random_uuid();
        ALTER TABLE accounts ADD CONSTRAINT uq_accounts_id UNIQUE(id);
        ALTER TABLE accounts ADD COLUMN email TEXT;
        ALTER TABLE accounts ADD COLUMN email_normalized TEXT;
        CREATE UNIQUE INDEX uq_accounts_email ON accounts(email_normalized)
          WHERE email_normalized IS NOT NULL;
        ALTER TABLE accounts ADD COLUMN email_verified_at TIMESTAMPTZ;
        ALTER TABLE accounts ADD COLUMN display_name TEXT NOT NULL DEFAULT '';
        ALTER TABLE accounts ADD COLUMN auth_version BIGINT NOT NULL DEFAULT 0;
        ALTER TABLE accounts ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
        ALTER TABLE accounts ADD COLUMN seeded_for_dev BOOLEAN NOT NULL DEFAULT false;
        CREATE TABLE auth_sessions (
          id UUID PRIMARY KEY, account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
          token_digest TEXT NOT NULL UNIQUE, auth_version BIGINT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(), last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          idle_expires_at TIMESTAMPTZ NOT NULL, absolute_expires_at TIMESTAMPTZ NOT NULL,
          revoked_at TIMESTAMPTZ
        );
        CREATE INDEX ix_auth_sessions_account ON auth_sessions(account_id);
        CREATE INDEX ix_auth_sessions_expiry ON auth_sessions(idle_expires_at);
        CREATE TABLE email_verification_tokens (
          id UUID PRIMARY KEY, account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
          token_digest TEXT NOT NULL UNIQUE, registration_digest TEXT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(), expires_at TIMESTAMPTZ NOT NULL,
          used_at TIMESTAMPTZ
        );
        CREATE INDEX ix_email_tokens_account ON email_verification_tokens(account_id);
        CREATE TABLE account_portal_links (
          account_id UUID PRIMARY KEY REFERENCES accounts(id),
          portal_owner_id UUID NOT NULL UNIQUE REFERENCES portal_users(id) ON DELETE CASCADE,
          linked_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE TABLE auth_rate_limits (
          action TEXT NOT NULL, key_digest TEXT NOT NULL, window_start TIMESTAMPTZ NOT NULL,
          attempts INTEGER NOT NULL, PRIMARY KEY(action,key_digest,window_start)
        );
        CREATE TABLE auth_audit_events (
          id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          actor_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
          target_id UUID, action TEXT NOT NULL, result TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)


def downgrade():
    raise RuntimeError("Restore a reviewed backup rather than discard system accounts")
