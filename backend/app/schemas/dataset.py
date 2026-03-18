import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.dataset import SourceType


class DatasetCreate(BaseModel):
    name: str
    description: str = ""
    tags: str = ""


class DatasetMountRequest(BaseModel):
    name: str
    description: str = ""
    server_path: str
    format: str = "jsonl"
    tags: str = ""


class DatasetResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    source_type: SourceType
    source_uri: str
    format: str
    tags: str
    version: int
    size_bytes: int
    row_count: int
    created_at: datetime


class DatasetVersionResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    version: int
    file_path: str
    changelog: str
    row_count: int
    created_at: datetime


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
