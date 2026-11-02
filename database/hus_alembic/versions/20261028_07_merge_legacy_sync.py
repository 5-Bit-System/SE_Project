"""Reconnect previously deployed transcript sync revisions to current VNU auth.

Restore the missing history rather than relabeling deployed databases. Both
parents must be applied; this merge itself changes no tables or source records.
"""

revision = "hus_20261028_07"
down_revision = ("hus_20261023_04", "hus_20261025_06")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    raise RuntimeError("Restore a reviewed backup instead of splitting deployed migration history")
