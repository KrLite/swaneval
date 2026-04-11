"""Multi-tenant isolation model.

Each Tenant is an isolated namespace for datasets, models, criteria,
tasks, reports, and clusters. Users join tenants via TenantMembership
with a role scoped to that tenant. A user may belong to many tenants;
the UI picks one active tenant at a time and the axios client sends
it in `X-Tenant-ID`.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class TenantRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"
    viewer = "viewer"


class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    slug: str = Field(index=True, unique=True, max_length=64)
    # Short URL-safe identifier. Used in API paths and headers.

    name: str = Field(max_length=128)
    description: str = Field(default="")

    created_by: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )


class TenantMembership(SQLModel, table=True):
    """Many-to-many join between users and tenants with a per-tenant role."""

    __tablename__ = "tenant_memberships"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "user_id",
            name="uq_tenant_memberships_tenant_user",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenant_id: uuid.UUID = Field(foreign_key="tenants.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    role: TenantRole = Field(
        sa_column=Column(
            SAEnum(TenantRole, name="tenantrole", create_constraint=False),
            nullable=False,
        )
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )
