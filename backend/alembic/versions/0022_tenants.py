"""multi-tenant: tenants table + tenant_id on resources + users.active_tenant_id

Revision ID: 0022
Revises: 0021
Create Date: 2026-04-11
"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0022"
down_revision: str | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


RESOURCE_TABLES = [
    "datasets",
    "llm_models",
    "criteria",
    "eval_tasks",
    "reports",
    "compute_clusters",
    "external_benchmarks",
]


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_by",
            sa.Uuid(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    op.create_table(
        "tenant_memberships",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Uuid(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum(
                "owner",
                "admin",
                "member",
                "viewer",
                name="tenantrole",
                create_constraint=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "tenant_id", "user_id", name="uq_tenant_memberships_tenant_user"
        ),
    )
    op.create_index(
        "ix_tenant_memberships_tenant_id",
        "tenant_memberships",
        ["tenant_id"],
    )
    op.create_index(
        "ix_tenant_memberships_user_id",
        "tenant_memberships",
        ["user_id"],
    )

    # Seed a "default" tenant so we can backfill resource tables without
    # losing rows. Existing users are added as members with owner role.
    default_tenant_id = uuid.uuid4()
    op.execute(
        sa.text(
            "INSERT INTO tenants (id, slug, name, description, created_at, updated_at) "
            "VALUES (:id, 'default', 'Default Tenant', '', now(), now())"
        ).bindparams(id=default_tenant_id)
    )
    op.execute(
        sa.text(
            "INSERT INTO tenant_memberships (id, tenant_id, user_id, role, created_at) "
            "SELECT gen_random_uuid(), :tid, id, 'owner', now() FROM users"
        ).bindparams(tid=default_tenant_id)
    )

    # Add active_tenant_id to users.
    op.add_column(
        "users",
        sa.Column(
            "active_tenant_id",
            sa.Uuid(),
            sa.ForeignKey("tenants.id"),
            nullable=True,
        ),
    )
    op.execute(
        sa.text("UPDATE users SET active_tenant_id = :tid").bindparams(
            tid=default_tenant_id
        )
    )

    # Add tenant_id to every resource table, backfill, then make NOT NULL.
    for table in RESOURCE_TABLES:
        op.add_column(
            table,
            sa.Column(
                "tenant_id",
                sa.Uuid(),
                sa.ForeignKey("tenants.id"),
                nullable=True,
            ),
        )
        op.execute(
            sa.text(f"UPDATE {table} SET tenant_id = :tid").bindparams(
                tid=default_tenant_id
            )
        )
        op.alter_column(table, "tenant_id", nullable=False)
        op.create_index(
            f"ix_{table}_tenant_id",
            table,
            ["tenant_id"],
        )


def downgrade() -> None:
    for table in RESOURCE_TABLES:
        op.drop_index(f"ix_{table}_tenant_id", table_name=table)
        op.drop_column(table, "tenant_id")

    op.drop_column("users", "active_tenant_id")

    op.drop_index("ix_tenant_memberships_user_id", table_name="tenant_memberships")
    op.drop_index("ix_tenant_memberships_tenant_id", table_name="tenant_memberships")
    op.drop_table("tenant_memberships")

    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
