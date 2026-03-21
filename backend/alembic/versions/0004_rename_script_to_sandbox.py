"""rename script to sandbox

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-21
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("ALTER TYPE criteriontype ADD VALUE IF NOT EXISTS 'sandbox'")
    op.execute("COMMIT")
    op.execute("UPDATE criteria SET type = 'sandbox' WHERE type = 'script'")

def downgrade() -> None:
    op.execute("UPDATE criteria SET type = 'script' WHERE type = 'sandbox'")
