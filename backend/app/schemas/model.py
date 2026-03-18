import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.llm_model import ModelType


class LLMModelCreate(BaseModel):
    name: str
    provider: str
    endpoint_url: str
    api_key: str = ""
    model_type: ModelType


class LLMModelUpdate(BaseModel):
    name: str | None = None
    endpoint_url: str | None = None
    api_key: str | None = None


class LLMModelResponse(BaseModel):
    id: uuid.UUID
    name: str
    provider: str
    endpoint_url: str
    model_type: ModelType
    created_at: datetime
