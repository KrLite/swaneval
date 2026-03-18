import enum
import uuid
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class TaskStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"


class SeedStrategy(str, enum.Enum):
    fixed = "fixed"
    random = "random"


class EvalTask(SQLModel, table=True):
    __tablename__ = "eval_tasks"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=256)
    status: TaskStatus = Field(
        sa_column=Column(SAEnum(TaskStatus), nullable=False, default=TaskStatus.pending)
    )
    model_id: uuid.UUID = Field(foreign_key="llm_models.id")
    dataset_ids: str = Field(default="")  # comma-separated UUIDs
    criteria_ids: str = Field(default="")  # comma-separated UUIDs
    params_json: str = Field(default='{"temperature": 0.7, "max_tokens": 1024}')
    repeat_count: int = Field(default=1)
    seed_strategy: SeedStrategy = Field(
        sa_column=Column(SAEnum(SeedStrategy), nullable=False, default=SeedStrategy.fixed)
    )
    created_by: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    started_at: datetime | None = Field(default=None)
    finished_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EvalSubtask(SQLModel, table=True):
    __tablename__ = "eval_subtasks"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(foreign_key="eval_tasks.id")
    run_index: int = Field(default=0)
    status: TaskStatus = Field(
        sa_column=Column(
            SAEnum(TaskStatus, name="subtaskstatus", create_constraint=False),
            nullable=False,
            default=TaskStatus.pending,
        )
    )
    progress_pct: float = Field(default=0.0)
    last_completed_index: int = Field(default=0)
    error_log: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
