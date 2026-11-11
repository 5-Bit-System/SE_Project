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
    # Lưu ý an toàn: Lệnh ALTER TABLE ADD CONSTRAINT dưới đây sẽ thất bại nếu trong bảng accounts
    # vẫn còn tồn tại bất kỳ tài khoản nào mang role = 'reviewer'.
    # Người vận hành cần xóa hoặc di chuyển các tài khoản reviewer sang role khác trước khi downgrade.
    op.execute("""
        ALTER TABLE accounts DROP CONSTRAINT IF EXISTS accounts_role_check;
        ALTER TABLE accounts ADD CONSTRAINT accounts_role_check
            CHECK (role IN ('student', 'teacher', 'admin'));
    """)
