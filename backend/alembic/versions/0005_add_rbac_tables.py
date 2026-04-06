"""add rbac tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-21
"""

import json
import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# System group definitions: name -> (description, permissions)
SYSTEM_GROUPS = {
    "Administrators": (
        "Full system access",
        [
            "datasets.read",
            "datasets.write",
            "datasets.download",
            "tasks.read",
            "tasks.create",
            "tasks.manage",
            "results.read",
            "reports.read",
            "reports.generate",
            "reports.export",
            "models.read",
            "models.write",
            "criteria.read",
            "criteria.write",
            "clusters.read",
            "clusters.manage",
            "admin.users",
            "admin.groups",
            "admin.acl",
        ],
    ),
    "Data Administrators": (
        "Manage datasets and criteria, view all results",
        [
            "datasets.read",
            "datasets.write",
            "datasets.download",
            "criteria.read",
            "criteria.write",
            "tasks.read",
            "results.read",
            "reports.read",
            "models.read",
        ],
    ),
    "Engineers": (
        "Run evaluation tasks, view permitted data",
        [
            "datasets.read",
            "datasets.download",
            "tasks.read",
            "tasks.create",
            "results.read",
            "reports.read",
            "models.read",
            "criteria.read",
        ],
    ),
    "Viewers": (
        "View permitted results and reports",
        [
            "datasets.read",
            "tasks.read",
            "results.read",
            "reports.read",
            "models.read",
            "criteria.read",
        ],
    ),
}

# Role -> group name mapping for migration of existing users
ROLE_TO_GROUP = {
    "admin": "Administrators",
    "data_admin": "Data Administrators",
    "engineer": "Engineers",
    "viewer": "Viewers",
}


def upgrade() -> None:
    # ── Create accesslevel enum (idempotent) ────────────────────────────
    op.execute(
        sa.text(
            "DO $$ BEGIN CREATE TYPE accesslevel AS ENUM "
            "('view', 'evaluate', 'download', 'edit', 'admin'); "
            "EXCEPTION WHEN duplicate_object THEN null; END $$;"
        )
    )
    accesslevel = postgresql.ENUM(
        "view",
        "evaluate",
        "download",
        "edit",
        "admin",
        name="accesslevel",
        create_type=False,
    )

    # ── permission_groups ──────────────────────────────────────────────
    op.create_table(
        "permission_groups",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("description", sa.String(), nullable=False, server_default=""),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("permissions_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
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

    # ── user_group_memberships ─────────────────────────────────────────
    op.create_table(
        "user_group_memberships",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "group_id",
            sa.Uuid(),
            sa.ForeignKey("permission_groups.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("user_id", "group_id"),
    )

    # ── resource_acls ──────────────────────────────────────────────────
    op.create_table(
        "resource_acls",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("resource_type", sa.String(32), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("grantee_type", sa.String(16), nullable=False),
        sa.Column("grantee_id", sa.Uuid(), nullable=False),
        sa.Column("access_level", accesslevel, nullable=False),
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
        sa.UniqueConstraint(
            "resource_type",
            "resource_id",
            "grantee_type",
            "grantee_id",
            "access_level",
        ),
    )

    # ── Seed system groups ─────────────────────────────────────────────
    op.execute("COMMIT")

    conn = op.get_bind()
    group_ids = {}
    for name, (description, permissions) in SYSTEM_GROUPS.items():
        gid = uuid.uuid4()
        group_ids[name] = gid
        conn.execute(
            sa.text(
                "INSERT INTO permission_groups"
                " (id, name, description, is_system,"
                " permissions_json, created_at, updated_at)"
                " VALUES (:id, :name, :desc, true,"
                " :perms, now(), now())"
            ),
            {
                "id": str(gid),
                "name": name,
                "desc": description,
                "perms": json.dumps(permissions),
            },
        )

    # ── Migrate existing users into groups based on role ───────────────
    for role, group_name in ROLE_TO_GROUP.items():
        gid = group_ids[group_name]
        rows = conn.execute(
            sa.text("SELECT id FROM users WHERE role = :role"),
            {"role": role},
        ).fetchall()
        for row in rows:
            conn.execute(
                sa.text(
                    "INSERT INTO user_group_memberships (id, user_id, group_id, created_at) "
                    "VALUES (:id, :uid, :gid, now())"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "uid": str(row[0]),
                    "gid": str(gid),
                },
            )


def downgrade() -> None:
    op.drop_table("resource_acls")
    op.drop_table("user_group_memberships")
    op.drop_table("permission_groups")
    postgresql.ENUM(name="accesslevel").drop(op.get_bind(), checkfirst=True)
