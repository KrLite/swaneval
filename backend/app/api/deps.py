import uuid

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import get_session
from app.models.tenant import TenantMembership
from app.models.user import User
from app.services.auth import decode_access_token

security = HTTPBearer()


async def get_db() -> AsyncSession:
    async for session in get_session():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    user_id_str = decode_access_token(token)
    if not user_id_str:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "令牌无效或已过期")
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "令牌内容无效")

    user = await session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在或已停用")
    return user


async def get_current_tenant_id(
    x_tenant_id: str | None = Header(default=None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> uuid.UUID:
    """Resolve the tenant the current request is scoped to.

    Precedence:
    1. ``X-Tenant-ID`` header from the frontend (explicit switch)
    2. ``user.active_tenant_id`` as a persistent fallback
    3. Any tenant the user is a member of (first one wins)
    4. 403 if the user has no memberships at all

    Also enforces membership: if the header specifies a tenant the user
    is not a member of, the request is rejected rather than silently
    falling back. This prevents header-forgery cross-tenant access.
    """
    candidate: uuid.UUID | None = None
    if x_tenant_id:
        try:
            candidate = uuid.UUID(x_tenant_id)
        except ValueError as e:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "X-Tenant-ID 格式无效"
            ) from e
    elif current_user.active_tenant_id:
        candidate = current_user.active_tenant_id

    if candidate is not None:
        membership_stmt = select(TenantMembership).where(
            TenantMembership.tenant_id == candidate,
            TenantMembership.user_id == current_user.id,
        )
        membership = (await session.exec(membership_stmt)).first()
        if not membership:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "当前用户不属于该租户",
            )
        return candidate

    # No header, no active tenant → pick the user's first membership.
    first_stmt = select(TenantMembership).where(
        TenantMembership.user_id == current_user.id
    )
    first = (await session.exec(first_stmt)).first()
    if not first:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "当前用户未加入任何租户",
        )
    return first.tenant_id


def require_role(*roles: str):
    async def dependency(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "权限不足")
        return current_user

    return Depends(dependency)


def require_permission(*perms: str):
    async def dependency(
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db),
    ):
        from app.services.rbac import check_permission

        if current_user.role == "admin":
            return current_user
        for p in perms:
            if await check_permission(session, current_user, p):
                return current_user
        raise HTTPException(status.HTTP_403_FORBIDDEN, "权限不足")

    return Depends(dependency)
