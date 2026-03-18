import enum
import uuid
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class SourceType(str, enum.Enum):
    upload = "upload"
    huggingface = "huggingface"
    modelscope = "modelscope"
    server_path = "server_path"
    preset = "preset"


class Dataset(SQLModel, table=True):
    __tablename__ = "datasets"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, max_length=256)
    description: str = Field(default="")
    source_type: SourceType = Field(sa_column=Column(SAEnum(SourceType), nullable=False))
    source_uri: str = Field(default="")
    format: str = Field(default="jsonl", max_length=32)
    tags: str = Field(default="")  # comma-separated
    version: int = Field(default=1)
    size_bytes: int = Field(default=0)
    row_count: int = Field(default=0)
    created_by: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DatasetVersion(SQLModel, table=True):
    __tablename__ = "dataset_versions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    dataset_id: uuid.UUID = Field(foreign_key="datasets.id")
    version: int
    file_path: str
    changelog: str = Field(default="")
    row_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
