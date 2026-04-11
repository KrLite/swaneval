"""add compliance_records table

Revision ID: 0020
Revises: 0019
Create Date: 2026-04-11
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "compliance_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "resource_type",
            sa.Enum(
                "model",
                "dataset",
                name="complianceresourcetype",
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("license_spdx", sa.String(length=128), nullable=False, server_default=""),
        sa.Column(
            "license_status",
            sa.Enum(
                "compliant",
                "restricted",
                "unknown",
                name="compliancestatus",
                create_constraint=False,
            ),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column("cve_findings_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("last_scanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_compliance_records_resource_id",
        "compliance_records",
        ["resource_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_compliance_records_resource_id", table_name="compliance_records"
    )
    op.drop_table("compliance_records")
