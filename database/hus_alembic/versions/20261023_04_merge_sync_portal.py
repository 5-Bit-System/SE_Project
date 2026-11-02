"""Join transcript synchronization and portal migration histories.

Both preceding revisions were developed independently from hus_20261017_02.
Do not rewrite either history: databases may have already applied either branch.
"""

revision = "hus_20261023_04"
down_revision = ("hus_20261023_01", "hus_20261023_03")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    raise RuntimeError("Restore a reviewed backup instead of splitting migration history")
