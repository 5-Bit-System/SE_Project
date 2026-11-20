"""Academic announcements migration.

Revision ID: hus_20261101_12
Revises: hus_20261101_11
Create Date: 2026-11-01 14:45:00
"""

from alembic import op

revision = "hus_20261101_12"
down_revision = "hus_20261101_11"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS academic_announcements (
            id VARCHAR(36) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            source_url VARCHAR(500) NOT NULL,
            audience VARCHAR(50) NOT NULL DEFAULT 'all',
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            effective_date TIMESTAMP WITH TIME ZONE NOT NULL,
            expiry_date TIMESTAMP WITH TIME ZONE NULL,
            created_by VARCHAR(100) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            published_at TIMESTAMP WITH TIME ZONE NULL
        );

        CREATE INDEX IF NOT EXISTS idx_announcements_status ON academic_announcements (status);
        CREATE INDEX IF NOT EXISTS idx_announcements_audience ON academic_announcements (audience);
        CREATE INDEX IF NOT EXISTS idx_announcements_dates ON academic_announcements (effective_date, expiry_date);
    """)


def downgrade():
    op.execute("""
        DROP TABLE IF EXISTS academic_announcements;
    """)
