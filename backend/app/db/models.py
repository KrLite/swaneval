import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlmodel import JSON, Column, Field, Relationship, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> uuid.UUID:
    return uuid.uuid4()


# ---------- Enums ----------


class ModelSourceType(str, Enum):
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    API = "api"


class DatasetSourceType(str, Enum):
    PRESET = "preset"
    HUGGINGFACE = "huggingface"
    MODELSCOPE = "modelscope"
    UPLOAD = "upload"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


# ---------- Link table ----------


class EvaluationDatasetLink(SQLModel, table=True):
    __tablename__ = "evaluation_dataset_link"

    evaluation_id: uuid.UUID = Field(foreign_key="evaluations.id", primary_key=True)
    dataset_id: uuid.UUID = Field(foreign_key="datasets.id", primary_key=True)


# ---------- Models ----------


class MLModel(SQLModel, table=True):
    """Registered ML model for evaluation."""

    __tablename__ = "ml_models"

    id: uuid.UUID = Field(default_factory=_new_id, primary_key=True)
    name: str = Field(index=True)
    source_type: ModelSourceType
    path_or_endpoint: str
    revision: str | None = None
    precision: str | None = None
    device_map: str | None = None
    api_key: str | None = None
    extra_params: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    evaluations: list["Evaluation"] = Relationship(back_populates="model")


class Dataset(SQLModel, table=True):
    """Evaluation dataset."""

    __tablename__ = "datasets"

    id: uuid.UUID = Field(default_factory=_new_id, primary_key=True)
    name: str = Field(index=True)
    source_type: DatasetSourceType
    source_path: str
    description: str | None = None
    version: str = "1.0"
    row_count: int | None = None
    schema_info: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    evaluations: list["Evaluation"] = Relationship(
        back_populates="datasets", link_model=EvaluationDatasetLink
    )


class Evaluation(SQLModel, table=True):
    """An evaluation task combining a model with one or more datasets."""

    __tablename__ = "evaluations"

    id: uuid.UUID = Field(default_factory=_new_id, primary_key=True)
    name: str = Field(index=True)
    model_id: uuid.UUID = Field(foreign_key="ml_models.id")
    status: TaskStatus = TaskStatus.PENDING
    celery_task_id: str | None = None

    # Evaluation parameters
    temperature: float = 0.0
    max_tokens: int = 2048
    few_shot: int = 0
    batch_size: int = 1
    extra_params: dict | None = Field(default=None, sa_column=Column(JSON))

    progress: float = 0.0
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    model: MLModel = Relationship(back_populates="evaluations")
    datasets: list[Dataset] = Relationship(
        back_populates="evaluations", link_model=EvaluationDatasetLink
    )
    results: list["EvaluationResult"] = Relationship(back_populates="evaluation")


class EvaluationResult(SQLModel, table=True):
    """Stores results for a completed evaluation."""

    __tablename__ = "evaluation_results"

    id: uuid.UUID = Field(default_factory=_new_id, primary_key=True)
    evaluation_id: uuid.UUID = Field(foreign_key="evaluations.id", index=True)
    dataset_name: str
    metric_name: str
    metric_value: float
    details: dict | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_utcnow)

    evaluation: Evaluation = Relationship(back_populates="results")
