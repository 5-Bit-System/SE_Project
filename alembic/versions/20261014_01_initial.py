"""Create versioned catalog and synthetic profile persistence.

The schema snapshot is frozen alongside this migration, so future application
schema edits cannot change the meaning of this migration.
"""

from pathlib import Path
import runpy

from alembic import op

revision = "20261014_01"
down_revision = None
branch_labels = None
depends_on = None


def snapshot():
    return runpy.run_path(str(Path(__file__).resolve().parents[1] / "schema_v1.py"))["metadata"]


def upgrade():
    snapshot().create_all(op.get_bind(), checkfirst=False)


def downgrade():
    snapshot().drop_all(op.get_bind(), checkfirst=False)
