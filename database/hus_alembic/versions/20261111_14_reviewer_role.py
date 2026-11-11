"""Allow reviewer role in accounts_role_check."""

from alembic import op

revision = "hus_20261111_14"
down_revision = "hus_20261105_13"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE accounts DROP CONSTRAINT IF EXISTS accounts_role_check;
        ALTER TABLE accounts ADD CONSTRAINT accounts_role_check
            CHECK (role IN ('student', 'teacher', 'admin', 'reviewer'));
    """)


def downgrade():
    op.execute("""
        ALTER TABLE accounts DROP CONSTRAINT IF EXISTS accounts_role_check;
        ALTER TABLE accounts ADD CONSTRAINT accounts_role_check
            CHECK (role IN ('student', 'teacher', 'admin'));
    """)
