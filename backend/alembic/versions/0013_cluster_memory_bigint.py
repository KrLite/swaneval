"""change memory_total_bytes to bigint

Revision ID: 0013
Revises: 0012
Create Date: 2026-03-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "compute_clusters",
        "memory_total_bytes",
        type_=sa.BigInteger(),
        existing_type=sa.Integer(),
    )


def downgrade() -> None:
    op.alter_column(
        "compute_clusters",
        "memory_total_bytes",
        type_=sa.Integer(),
        existing_type=sa.BigInteger(),
    )
