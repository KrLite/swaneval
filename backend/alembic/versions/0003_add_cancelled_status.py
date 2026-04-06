"""add cancelled status

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-21
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'cancelled'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values easily.
    # The value will remain but be unused.
    pass
