"""add gpu_ids and env_vars to eval_tasks

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-19
"""
from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("eval_tasks", sa.Column("gpu_ids", sa.String(), server_default="", nullable=False))
    op.add_column("eval_tasks", sa.Column("env_vars", sa.String(), server_default="", nullable=False))


def downgrade() -> None:
    op.drop_column("eval_tasks", "env_vars")
    op.drop_column("eval_tasks", "gpu_ids")
