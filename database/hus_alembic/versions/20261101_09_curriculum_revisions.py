"""Curriculum revision drafts, publication workflow, and review audit history."""

from alembic import op

revision = "hus_20261101_09"
down_revision = "hus_20261028_08"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE curriculum_revisions (
            revision_id TEXT PRIMARY KEY,
            program_id TEXT NOT NULL,
            cohort TEXT,
            version_title TEXT NOT NULL,
            source_filename TEXT,
            source_digest TEXT NOT NULL,
            payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
            status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'validated', 'approved', 'published', 'rejected')),
            validation_summary JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(validation_summary) = 'object'),
            created_by UUID REFERENCES accounts(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            reviewed_by UUID REFERENCES accounts(id) ON DELETE SET NULL,
            reviewed_at TIMESTAMPTZ,
            review_decision TEXT CHECK (review_decision IN ('approved', 'rejected', NULL)),
            review_notes TEXT,
            published_at TIMESTAMPTZ,
            is_active BOOLEAN NOT NULL DEFAULT false
        );

        CREATE INDEX ix_curriculum_revisions_program ON curriculum_revisions(program_id, created_at DESC);
        CREATE UNIQUE INDEX uq_curriculum_revisions_active ON curriculum_revisions(program_id) WHERE is_active = true;

        CREATE TABLE curriculum_reviews (
            id UUID PRIMARY KEY,
            revision_id TEXT NOT NULL REFERENCES curriculum_revisions(revision_id) ON DELETE CASCADE,
            reviewer_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
            action TEXT NOT NULL CHECK (action IN ('created', 'validated', 'approved', 'rejected', 'published', 'rolled_back')),
            reason TEXT NOT NULL,
            details JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX ix_curriculum_reviews_revision ON curriculum_reviews(revision_id, created_at DESC);
    """)


def downgrade():
    op.execute("""
        DROP TABLE IF EXISTS curriculum_reviews;
        DROP TABLE IF EXISTS curriculum_revisions;
    """)
