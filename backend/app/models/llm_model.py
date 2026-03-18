import enum
import uuid
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class ModelType(str, enum.Enum):
    api = "api"
    local = "local"
    huggingface = "huggingface"


class LLMModel(SQLModel, table=True):
    __tablename__ = "llm_models"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, max_length=256)
    provider: str = Field(max_length=64)
    endpoint_url: str
    api_key: str = Field(default="")
    model_type: ModelType = Field(sa_column=Column(SAEnum(ModelType), nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
