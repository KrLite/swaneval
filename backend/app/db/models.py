"""Database models for EvalScope GUI."""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Boolean, DateTime, Text, JSON,
    ForeignKey, Enum as SQLEnum, Float
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User roles."""
    ADMIN = "admin"
    DATA_MANAGER = "data_manager"
    EVALUATOR = "evaluator"
    GUEST = "guest"


class ModelType(str, enum.Enum):
    """Model types."""
    LOCAL = "local"
    HUGGINGFACE = "huggingface"
    API = "api"


class TaskStatus(str, enum.Enum):
    """Task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class DatasetSource(str, enum.Enum):
    """Dataset sources."""
    PRESET = "preset"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"
    SERVER_PATH = "server_path"


class User(Base):
    """User model."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.GUEST)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    evaluations: Mapped[List["Evaluation"]] = relationship("Evaluation", back_populates="user")
    models: Mapped[List["ModelConfig"]] = relationship("ModelConfig", back_populates="user")


class ModelConfig(Base):
    """Model configuration model."""
    __tablename__ = "model_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    model_type: Mapped[ModelType] = mapped_column(SQLEnum(ModelType))
    path: Mapped[str] = mapped_column(Text)  # HF path, local path, or API endpoint
    api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    config: Mapped[Optional[JSON]] = mapped_column(JSON, nullable=True)  # revision, precision, device_map
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="models")
    evaluations: Mapped[List["Evaluation"]] = relationship("Evaluation", back_populates="model_config")


class Dataset(Base):
    """Dataset model."""
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[DatasetSource] = mapped_column(SQLEnum(DatasetSource))
    path: Mapped[str] = mapped_column(Text)  # HF ID, local path, or server path
    version: Mapped[int] = mapped_column(Integer, default=1)
    tags: Mapped[Optional[JSON]] = mapped_column(JSON, nullable=True)
    dataset_metadata: Mapped[Optional[JSON]] = mapped_column("metadata", JSON, nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    evaluations: Mapped[List["Evaluation"]] = relationship("Evaluation", back_populates="dataset")


class Evaluation(Base):
    """Evaluation model."""
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_config_id: Mapped[int] = mapped_column(Integer, ForeignKey("model_configs.id"))
    dataset_id: Mapped[int] = mapped_column(Integer, ForeignKey("datasets.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    # Configuration
    generation_config: Mapped[Optional[JSON]] = mapped_column(JSON, nullable=True)
    dataset_args: Mapped[Optional[JSON]] = mapped_column(JSON, nullable=True)
    eval_config: Mapped[Optional[JSON]] = mapped_column(JSON, nullable=True)

    # Results
    status: Mapped[TaskStatus] = mapped_column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    metrics: Mapped[Optional[JSON]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    model_config: Mapped["ModelConfig"] = relationship("ModelConfig", back_populates="evaluations")
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="evaluations")
    user: Mapped["User"] = relationship("User", back_populates="evaluations")
    results: Mapped[List["EvaluationResult"]] = relationship("EvaluationResult", back_populates="evaluation")


class EvaluationResult(Base):
    """Evaluation result model."""
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    evaluation_id: Mapped[int] = mapped_column(Integer, ForeignKey("evaluations.id"))
    prompt: Mapped[Text] = mapped_column(Text)
    expected_output: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    actual_output: Mapped[Optional[Text]] = mapped_column(Text, nullable=True)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    dataset_metadata: Mapped[Optional[JSON]] = mapped_column("metadata", JSON, nullable=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="results")