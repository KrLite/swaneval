"""Pairwise comparison records for ELO-rating criteria.

Each row represents a single judge decision between two model outputs
on the same prompt. ELO scores are computed lazily by reading all rows
for a given (task, criterion) and replaying them in created_at order.
The table is write-append-only; updates would be meaningless because
the ranking is a pure function of the full history.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel


class PairwiseWinner(str, enum.Enum):
    a = "a"
    b = "b"
    tie = "tie"


class PairwiseComparison(SQLModel, table=True):
    __tablename__ = "pairwise_comparisons"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(foreign_key="eval_tasks.id", index=True)
    criterion_id: uuid.UUID = Field(foreign_key="criteria.id", index=True)
    prompt_text: str = Field(default="")

    model_a_id: uuid.UUID = Field(foreign_key="llm_models.id")
    model_b_id: uuid.UUID = Field(foreign_key="llm_models.id")
    result_a_id: uuid.UUID = Field(foreign_key="eval_results.id")
    result_b_id: uuid.UUID = Field(foreign_key="eval_results.id")

    winner: PairwiseWinner = Field(
        sa_column=Column(
            SAEnum(PairwiseWinner, name="pairwisewinner", create_constraint=False),
            nullable=False,
        )
    )
    judge_reasoning: str = Field(default="")

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
    )
