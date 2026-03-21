"""add compute clusters

Revision ID: 0006
Revises: 0005
Create Date: 2026-03-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_now = sa.text("now()")
_zero = sa.text("0")
_false = sa.text("false")


def upgrade() -> None:
    # ── Create enum types ───────────────────────────────────────────
    clusterstatus = postgresql.ENUM(
        "connecting", "ready", "error", "provisioning", "offline",
        name="clusterstatus",
        create_type=False,
    )
    infrajobtype = postgresql.ENUM(
        "namespace_setup", "vllm_cache", "resource_quota", "probe",
        name="infrajobtype",
        create_type=False,
    )
    clusterstatus.create(op.get_bind(), checkfirst=True)
    infrajobtype.create(op.get_bind(), checkfirst=True)

    # ── compute_clusters ────────────────────────────────────────────
    tz = sa.DateTime(timezone=True)
    op.create_table(
        "compute_clusters",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column(
            "description", sa.String(),
            nullable=False, server_default="",
        ),
        sa.Column(
            "kubeconfig_encrypted", sa.String(),
            nullable=False, server_default="",
        ),
        sa.Column(
            "api_server_url", sa.String(),
            nullable=False, server_default="",
        ),
        sa.Column(
            "namespace", sa.String(),
            nullable=False, server_default="default",
        ),
        sa.Column(
            "status", clusterstatus,
            nullable=False, server_default="connecting",
        ),
        sa.Column(
            "status_message", sa.String(),
            nullable=False, server_default="",
        ),
        sa.Column(
            "gpu_count", sa.Integer(),
            nullable=False, server_default=_zero,
        ),
        sa.Column(
            "gpu_type", sa.String(),
            nullable=False, server_default="",
        ),
        sa.Column(
            "gpu_available", sa.Integer(),
            nullable=False, server_default=_zero,
        ),
        sa.Column(
            "cpu_total_millicores", sa.Integer(),
            nullable=False, server_default=_zero,
        ),
        sa.Column(
            "memory_total_bytes", sa.BigInteger(),
            nullable=False, server_default=_zero,
        ),
        sa.Column(
            "node_count", sa.Integer(),
            nullable=False, server_default=_zero,
        ),
        sa.Column(
            "vllm_cache_ready", sa.Boolean(),
            nullable=False, server_default=_false,
        ),
        sa.Column("last_probed_at", tz, nullable=True),
        sa.Column(
            "created_by", sa.Uuid(),
            sa.ForeignKey("users.id"), nullable=True,
        ),
        sa.Column(
            "created_at", tz,
            nullable=False, server_default=_now,
        ),
        sa.Column(
            "updated_at", tz,
            nullable=False, server_default=_now,
        ),
    )

    # ── cluster_infra_jobs ──────────────────────────────────────────
    op.create_table(
        "cluster_infra_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "cluster_id", sa.Uuid(),
            sa.ForeignKey("compute_clusters.id"), nullable=False,
        ),
        sa.Column("job_type", infrajobtype, nullable=False),
        sa.Column(
            "status", sa.String(),
            nullable=False, server_default="pending",
        ),
        sa.Column(
            "log", sa.String(),
            nullable=False, server_default="",
        ),
        sa.Column(
            "created_at", tz,
            nullable=False, server_default=_now,
        ),
        sa.Column(
            "updated_at", tz,
            nullable=False, server_default=_now,
        ),
    )

    # ── Add cluster_id to eval_tasks ────────────────────────────────
    op.add_column(
        "eval_tasks",
        sa.Column(
            "cluster_id", sa.Uuid(),
            sa.ForeignKey("compute_clusters.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("eval_tasks", "cluster_id")
    op.drop_table("cluster_infra_jobs")
    op.drop_table("compute_clusters")
    postgresql.ENUM(name="infrajobtype").drop(
        op.get_bind(), checkfirst=True,
    )
    postgresql.ENUM(name="clusterstatus").drop(
        op.get_bind(), checkfirst=True,
    )
