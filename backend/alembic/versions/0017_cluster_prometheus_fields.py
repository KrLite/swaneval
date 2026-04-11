"""add prometheus_url and dcgm_namespace to compute_clusters

Revision ID: 0017
Revises: 0016
Create Date: 2026-04-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "compute_clusters",
        sa.Column(
            "prometheus_url",
            sa.String(),
            nullable=False,
            server_default="",
        ),
    )
    op.add_column(
        "compute_clusters",
        sa.Column(
            "dcgm_namespace",
            sa.String(),
            nullable=False,
            server_default="gpu-operator",
        ),
    )


def downgrade() -> None:
    op.drop_column("compute_clusters", "dcgm_namespace")
    op.drop_column("compute_clusters", "prometheus_url")
