import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class EvalResult(SQLModel, table=True):
    __tablename__ = "eval_results"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(foreign_key="eval_tasks.id", index=True)
    subtask_id: uuid.UUID = Field(foreign_key="eval_subtasks.id")
    dataset_id: uuid.UUID = Field(foreign_key="datasets.id")
    criterion_id: uuid.UUID = Field(foreign_key="criteria.id")
    prompt_text: str = Field(default="")
    expected_output: str = Field(default="")
    model_output: str = Field(default="")
    score: float = Field(default=0.0)
    latency_ms: float = Field(default=0.0)
    tokens_generated: int = Field(default=0)
    first_token_ms: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
