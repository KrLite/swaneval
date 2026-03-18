import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models import Evaluation, TaskStatus
from app.db.session import get_session

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ---------- Schemas ----------


class TaskRead(BaseModel):
    id: uuid.UUID
    name: str
    status: TaskStatus
    celery_task_id: str | None
    progress: float
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- Endpoints ----------


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    result = await session.exec(
        select(Evaluation).order_by(Evaluation.created_at.desc()).offset(skip).limit(limit)  # type: ignore[attr-defined]
    )
    return result.all()


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    evaluation = await session.get(Evaluation, task_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Task not found")
    return evaluation


@router.post("/{task_id}/cancel", response_model=TaskRead)
async def cancel_task(task_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    evaluation = await session.get(Evaluation, task_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Task not found")

    if evaluation.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
        raise HTTPException(status_code=400, detail="Task cannot be cancelled in current state")

    # TODO: revoke Celery task when task queue is integrated
    evaluation.status = TaskStatus.CANCELLED
    evaluation.finished_at = datetime.now(timezone.utc)
    session.add(evaluation)
    await session.commit()
    await session.refresh(evaluation)
    return evaluation
