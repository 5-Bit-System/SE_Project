"""Crawler sources, jobs lifecycle, and crawled document review governance."""

from alembic import op

revision = "hus_20261101_10"
down_revision = "hus_20261101_09"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE crawler_sources (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            base_url TEXT NOT NULL,
            schedule TEXT NOT NULL DEFAULT 'manual',
            depth_limit INT NOT NULL DEFAULT 3,
            is_active BOOLEAN NOT NULL DEFAULT true,
            allow_patterns JSONB NOT NULL DEFAULT '[]'::jsonb,
            deny_patterns JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE TABLE crawler_jobs (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL REFERENCES crawler_sources(id) ON DELETE CASCADE,
            status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'running', 'paused', 'completed', 'failed', 'cancelled')),
            pages_discovered INT NOT NULL DEFAULT 0,
            pages_crawled INT NOT NULL DEFAULT 0,
            documents_found INT NOT NULL DEFAULT 0,
            error_message TEXT,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            created_by UUID REFERENCES accounts(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX ix_crawler_jobs_source ON crawler_jobs(source_id, created_at DESC);
        CREATE INDEX ix_crawler_jobs_status ON crawler_jobs(status);

        CREATE TABLE crawled_documents (
            id TEXT PRIMARY KEY,
            source_id TEXT REFERENCES crawler_sources(id) ON DELETE SET NULL,
            job_id TEXT REFERENCES crawler_jobs(id) ON DELETE SET NULL,
            url TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            title TEXT NOT NULL,
            major TEXT NOT NULL DEFAULT 'general',
            doc_type TEXT NOT NULL DEFAULT 'general_info',
            markdown_content TEXT NOT NULL,
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            review_status TEXT NOT NULL DEFAULT 'pending' CHECK (review_status IN ('pending', 'approved', 'rejected')),
            reviewer_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
            review_reason TEXT,
            reviewed_at TIMESTAMPTZ,
            is_published BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        CREATE INDEX ix_crawled_docs_hash ON crawled_documents(content_hash);
        CREATE INDEX ix_crawled_docs_status ON crawled_documents(review_status);
        CREATE INDEX ix_crawled_docs_major ON crawled_documents(major);
    """)


def downgrade():
    op.execute("""
        DROP TABLE IF EXISTS crawled_documents;
        DROP TABLE IF EXISTS crawler_jobs;
        DROP TABLE IF EXISTS crawler_sources;
    """)
