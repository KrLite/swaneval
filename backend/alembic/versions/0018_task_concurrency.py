"""add concurrency to eval_tasks

Revision ID: 0018
Revises: 0017
Create Date: 2026-04-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "eval_tasks",
        sa.Column(
            "concurrency",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )


def downgrade() -> None:
    op.drop_column("eval_tasks", "concurrency")
