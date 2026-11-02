"""VNU student identities survive source deletion; admin keeps local credentials."""

from alembic import op

revision = 'hus_20261025_06'
down_revision = 'hus_20261025_05'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE accounts ADD COLUMN vnu_subject TEXT UNIQUE;
        ALTER TABLE accounts ADD CONSTRAINT ck_accounts_vnu_subject
          CHECK(vnu_subject IS NULL OR (length(vnu_subject) BETWEEN 1 AND 128
                AND vnu_subject=lower(btrim(vnu_subject))));
        ALTER TABLE auth_sessions ADD COLUMN auth_method TEXT NOT NULL DEFAULT 'local'
          CHECK(auth_method IN ('local','vnu'));
        UPDATE accounts a SET vnu_subject=p.subject
          FROM account_portal_links l JOIN portal_users p ON p.id=l.portal_owner_id
          WHERE a.id=l.account_id AND a.role='student';
        UPDATE auth_sessions s SET revoked_at=COALESCE(s.revoked_at,now())
          FROM accounts a WHERE a.id=s.account_id AND a.role<>'admin';
    """)


def downgrade():
    raise RuntimeError('Restore a reviewed backup rather than discard VNU identities')
