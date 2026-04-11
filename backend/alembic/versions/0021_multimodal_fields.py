"""multimodal: dataset.modality, eval_result.input_images_json, llm_model.supports_vision

Revision ID: 0021
Revises: 0020
Create Date: 2026-04-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0021"
down_revision: str | None = "0020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "datasets",
        sa.Column(
            "modality",
            sa.String(length=32),
            nullable=False,
            server_default="text",
        ),
    )
    op.add_column(
        "eval_results",
        sa.Column(
            "input_images_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "llm_models",
        sa.Column(
            "supports_vision",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("llm_models", "supports_vision")
    op.drop_column("eval_results", "input_images_json")
    op.drop_column("datasets", "modality")
