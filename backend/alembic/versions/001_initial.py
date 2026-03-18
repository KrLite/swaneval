"""initial

Revision ID: 001
Revises:
Create Date: 2026-03-19
"""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ml_models",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, index=True),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("path_or_endpoint", sa.String(), nullable=False),
        sa.Column("revision", sa.String(), nullable=True),
        sa.Column("precision", sa.String(), nullable=True),
        sa.Column("device_map", sa.String(), nullable=True),
        sa.Column("api_key", sa.String(), nullable=True),
        sa.Column("extra_params", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, index=True),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_path", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("version", sa.String(), nullable=False, server_default="1.0"),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("schema_info", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "evaluations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, index=True),
        sa.Column("model_id", sa.Uuid(), sa.ForeignKey("ml_models.id"), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("celery_task_id", sa.String(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="2048"),
        sa.Column("few_shot", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("batch_size", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("extra_params", sa.JSON(), nullable=True),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "evaluation_dataset_link",
        sa.Column("evaluation_id", sa.Uuid(), sa.ForeignKey("evaluations.id"), primary_key=True),
        sa.Column("dataset_id", sa.Uuid(), sa.ForeignKey("datasets.id"), primary_key=True),
    )

    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "evaluation_id", sa.Uuid(), sa.ForeignKey("evaluations.id"), nullable=False, index=True
        ),
        sa.Column("dataset_name", sa.String(), nullable=False),
        sa.Column("metric_name", sa.String(), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("evaluation_results")
    op.drop_table("evaluation_dataset_link")
    op.drop_table("evaluations")
    op.drop_table("datasets")
    op.drop_table("ml_models")
