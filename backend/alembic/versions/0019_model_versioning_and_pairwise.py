"""add version/base_model_id to llm_models; add pairwise_comparisons; add elo criterion type

Revision ID: 0019
Revises: 0018
Create Date: 2026-04-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # LLMModel version metadata
    op.add_column(
        "llm_models",
        sa.Column("version", sa.String(length=64), nullable=False, server_default="v1"),
    )
    op.add_column(
        "llm_models",
        sa.Column(
            "base_model_id",
            sa.Uuid(),
            sa.ForeignKey("llm_models.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_llm_models_base_model_id",
        "llm_models",
        ["base_model_id"],
    )

    # PairwiseComparison table for ELO rating
    op.create_table(
        "pairwise_comparisons",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "task_id",
            sa.Uuid(),
            sa.ForeignKey("eval_tasks.id"),
            nullable=False,
        ),
        sa.Column(
            "criterion_id",
            sa.Uuid(),
            sa.ForeignKey("criteria.id"),
            nullable=False,
        ),
        sa.Column("prompt_text", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "model_a_id",
            sa.Uuid(),
            sa.ForeignKey("llm_models.id"),
            nullable=False,
        ),
        sa.Column(
            "model_b_id",
            sa.Uuid(),
            sa.ForeignKey("llm_models.id"),
            nullable=False,
        ),
        sa.Column(
            "result_a_id",
            sa.Uuid(),
            sa.ForeignKey("eval_results.id"),
            nullable=False,
        ),
        sa.Column(
            "result_b_id",
            sa.Uuid(),
            sa.ForeignKey("eval_results.id"),
            nullable=False,
        ),
        sa.Column(
            "winner",
            sa.Enum("a", "b", "tie", name="pairwisewinner", create_constraint=False),
            nullable=False,
        ),
        sa.Column("judge_reasoning", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_pairwise_comparisons_task_id",
        "pairwise_comparisons",
        ["task_id"],
    )
    op.create_index(
        "ix_pairwise_comparisons_criterion_id",
        "pairwise_comparisons",
        ["criterion_id"],
    )

    # Add "elo" to the criteriontype enum. Postgres requires ALTER TYPE.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE criteriontype ADD VALUE IF NOT EXISTS 'elo'")


def downgrade() -> None:
    op.drop_index("ix_pairwise_comparisons_criterion_id", table_name="pairwise_comparisons")
    op.drop_index("ix_pairwise_comparisons_task_id", table_name="pairwise_comparisons")
    op.drop_table("pairwise_comparisons")

    op.drop_index("ix_llm_models_base_model_id", table_name="llm_models")
    op.drop_column("llm_models", "base_model_id")
    op.drop_column("llm_models", "version")
    # Note: cannot safely remove enum value 'elo' on downgrade in Postgres.
