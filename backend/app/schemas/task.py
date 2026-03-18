import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.eval_task import SeedStrategy, TaskStatus


class TaskCreate(BaseModel):
    name: str
    model_id: uuid.UUID
    dataset_ids: list[uuid.UUID]
    criteria_ids: list[uuid.UUID]
    params_json: str = '{"temperature": 0.7, "max_tokens": 1024}'
    repeat_count: int = 1
    seed_strategy: SeedStrategy = SeedStrategy.fixed


class TaskResponse(BaseModel):
    id: uuid.UUID
    name: str
    status: TaskStatus
    model_id: uuid.UUID
    dataset_ids: str
    criteria_ids: str
    params_json: str
    repeat_count: int
    seed_strategy: SeedStrategy
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class SubtaskResponse(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    run_index: int
    status: TaskStatus
    progress_pct: float
    last_completed_index: int
    error_log: str
