import enum
import uuid
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class CriterionType(str, enum.Enum):
    preset = "preset"
    regex = "regex"
    script = "script"
    llm_judge = "llm_judge"


class Criterion(SQLModel, table=True):
    __tablename__ = "criteria"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, max_length=256)
    type: CriterionType = Field(sa_column=Column(SAEnum(CriterionType), nullable=False))
    config_json: str = Field(default="{}")
    created_by: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
