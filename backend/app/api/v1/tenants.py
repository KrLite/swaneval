"""Tenant management endpoints: create, list mine, switch, member ops."""

import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_db, require_role
from app.models.tenant import Tenant, TenantMembership, TenantRole
from app.models.user import User

router = APIRouter()


class TenantCreate(BaseModel):
    slug: str
    name: str
    description: str = ""


class TenantResponse(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    slug: str
    name: str
    description: str
    created_at: datetime


class TenantMemberAdd(BaseModel):
    user_id: uuid.UUID
    role: TenantRole = TenantRole.member


_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$")


@router.post("", response_model=TenantResponse, status_code=201)
async def create_tenant(
    body: TenantCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = require_role("admin"),
):
    """Create a new tenant. Admin-only.

    The creator is automatically enrolled as an `owner` member so the
    UI's tenant switcher sees it immediately without a separate step.
    """
    if not _SLUG_RE.match(body.slug):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "slug 必须为 3–64 个小写字母/数字/短横线，首尾不能是短横线",
        )

    existing = await session.exec(select(Tenant).where(Tenant.slug == body.slug))
    if existing.first():
        raise HTTPException(status.HTTP_409_CONFLICT, "slug 已存在")

    tenant = Tenant(
        slug=body.slug,
        name=body.name,
        description=body.description,
        created_by=current_user.id,
    )
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)

    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=current_user.id,
        role=TenantRole.owner,
    )
    session.add(membership)
    await session.commit()

    return tenant


@router.get("/mine", response_model=list[TenantResponse])
async def list_my_tenants(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return every tenant the current user is a member of."""
    stmt = (
        select(Tenant)
        .join(TenantMembership, TenantMembership.tenant_id == Tenant.id)
        .where(TenantMembership.user_id == current_user.id)
        .order_by(col(Tenant.created_at).asc())
    )
    return (await session.exec(stmt)).all()


@router.post("/switch/{tenant_id}")
async def switch_active_tenant(
    tenant_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Persist the current user's active tenant choice.

    The frontend already sends `X-Tenant-ID` on every request for
    immediate effect; this endpoint just makes the choice stick
    across sessions. Verifies membership before writing.
    """
    membership_stmt = select(TenantMembership).where(
        TenantMembership.tenant_id == tenant_id,
        TenantMembership.user_id == current_user.id,
    )
    if not (await session.exec(membership_stmt)).first():
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "当前用户不属于该租户",
        )

    current_user.active_tenant_id = tenant_id
    current_user.updated_at = datetime.now(timezone.utc)
    session.add(current_user)
    await session.commit()
    return {"ok": True, "active_tenant_id": str(tenant_id)}


@router.post("/{tenant_id}/members", status_code=201)
async def add_tenant_member(
    tenant_id: uuid.UUID,
    body: TenantMemberAdd,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a user to a tenant. Requires owner/admin membership."""
    current_mem_stmt = select(TenantMembership).where(
        TenantMembership.tenant_id == tenant_id,
        TenantMembership.user_id == current_user.id,
    )
    current_mem = (await session.exec(current_mem_stmt)).first()
    if not current_mem or current_mem.role not in (TenantRole.owner, TenantRole.admin):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "需要 owner 或 admin 角色",
        )

    # Reject duplicates — unique constraint would error at commit anyway.
    dup_stmt = select(TenantMembership).where(
        TenantMembership.tenant_id == tenant_id,
        TenantMembership.user_id == body.user_id,
    )
    if (await session.exec(dup_stmt)).first():
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "该用户已是该租户成员",
        )

    new_mem = TenantMembership(
        tenant_id=tenant_id,
        user_id=body.user_id,
        role=body.role,
    )
    session.add(new_mem)
    await session.commit()
    return {"id": str(new_mem.id), "role": new_mem.role.value}


@router.delete("/{tenant_id}/members/{user_id}", status_code=204)
async def remove_tenant_member(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a user from a tenant. Requires owner/admin membership."""
    current_mem_stmt = select(TenantMembership).where(
        TenantMembership.tenant_id == tenant_id,
        TenantMembership.user_id == current_user.id,
    )
    current_mem = (await session.exec(current_mem_stmt)).first()
    if not current_mem or current_mem.role not in (TenantRole.owner, TenantRole.admin):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "需要 owner 或 admin 角色",
        )

    target_stmt = select(TenantMembership).where(
        TenantMembership.tenant_id == tenant_id,
        TenantMembership.user_id == user_id,
    )
    target = (await session.exec(target_stmt)).first()
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "成员未找到")

    await session.delete(target)
    await session.commit()


__all__ = ["router"]
