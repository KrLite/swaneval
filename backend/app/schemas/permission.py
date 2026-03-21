import uuid

from pydantic import BaseModel


class PermissionGroupCreate(BaseModel):
    name: str
    description: str = ""
    permissions: list[str] = []


class PermissionGroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None


class PermissionGroupResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    name: str
    description: str
    is_system: bool
    permissions: list[str] = []
    member_count: int = 0


class GroupMemberAdd(BaseModel):
    user_ids: list[uuid.UUID]


class ResourceAclCreate(BaseModel):
    resource_type: str
    resource_id: uuid.UUID
    grantee_type: str  # "group" or "user"
    grantee_id: uuid.UUID
    access_level: str


class ResourceAclResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    resource_type: str
    resource_id: uuid.UUID
    grantee_type: str
    grantee_id: uuid.UUID
    access_level: str
