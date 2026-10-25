"""Retain a browser-session family across password rotation for safe logout."""
from alembic import op

revision = 'hus_20261025_05'
down_revision = 'hus_20261025_04'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('ALTER TABLE auth_sessions ADD COLUMN family_id uuid')
    op.execute('UPDATE auth_sessions SET family_id=id')
    op.execute('ALTER TABLE auth_sessions ALTER COLUMN family_id SET NOT NULL')
    op.execute('CREATE INDEX ix_auth_sessions_family ON auth_sessions(family_id)')


def downgrade():
    raise RuntimeError('Session-history downgrade requires an explicit reviewed recovery procedure')
