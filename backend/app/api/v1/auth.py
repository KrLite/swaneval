from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth import create_access_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_db)):
    # Check uniqueness
    stmt = select(User).where((User.username == body.username) | (User.email == body.email))
    existing = (await session.exec(stmt)).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username or email already taken")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == body.username)
    user = (await session.exec(stmt)).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account disabled")

    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
