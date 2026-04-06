"""Permission groups and resource ACLs for RBAC."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class AccessLevel(str, enum.Enum):
    view = "view"
    evaluate = "evaluate"
    download = "download"
    edit = "edit"
    admin = "admin"


class PermissionGroup(SQLModel, table=True):
    __tablename__ = "permission_groups"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=128, unique=True)
    description: str = Field(default="")
    is_system: bool = Field(default=False)
    permissions_json: str = Field(default="[]")
    created_by: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )


class UserGroupMembership(SQLModel, table=True):
    __tablename__ = "user_group_memberships"
    __table_args__ = (UniqueConstraint("user_id", "group_id"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    group_id: uuid.UUID = Field(foreign_key="permission_groups.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )


class ResourceAcl(SQLModel, table=True):
    __tablename__ = "resource_acls"
    __table_args__ = (
        UniqueConstraint(
            "resource_type",
            "resource_id",
            "grantee_type",
            "grantee_id",
            "access_level",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    resource_type: str = Field(max_length=32)
    resource_id: uuid.UUID
    grantee_type: str = Field(max_length=16)  # "group" or "user"
    grantee_id: uuid.UUID
    access_level: AccessLevel = Field(
        sa_column=Column(
            SAEnum(AccessLevel, name="accesslevel", create_constraint=False),
            nullable=False,
        )
    )
    created_by: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )
