import uuid

from pydantic import BaseModel

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole = UserRole.viewer


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: UserRole
    is_active: bool
