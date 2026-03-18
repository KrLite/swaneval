import uuid
from datetime import datetime

from pydantic import BaseModel


class EvalResultResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    subtask_id: uuid.UUID
    dataset_id: uuid.UUID
    criterion_id: uuid.UUID
    prompt_text: str
    expected_output: str
    model_output: str
    score: float
    latency_ms: float
    tokens_generated: int
    first_token_ms: float
    created_at: datetime


class LeaderboardEntry(BaseModel):
    model_id: uuid.UUID
    model_name: str
    criterion_id: uuid.UUID
    criterion_name: str
    avg_score: float
    total_prompts: int
    avg_latency_ms: float
