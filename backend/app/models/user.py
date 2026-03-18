import enum
import uuid
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class UserRole(str, enum.Enum):
    admin = "admin"
    data_admin = "data_admin"
    engineer = "engineer"
    viewer = "viewer"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=64)
    email: str = Field(index=True, unique=True, max_length=256)
    hashed_password: str
    role: UserRole = Field(
        sa_column=Column(SAEnum(UserRole), nullable=False, default=UserRole.viewer)
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
