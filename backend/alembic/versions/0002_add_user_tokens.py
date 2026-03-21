"""add user tokens

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-20
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.add_column("users", sa.Column("hf_token", sa.String(), server_default="", nullable=False))
    op.add_column("users", sa.Column("ms_token", sa.String(), server_default="", nullable=False))

def downgrade() -> None:
    op.drop_column("users", "ms_token")
    op.drop_column("users", "hf_token")
