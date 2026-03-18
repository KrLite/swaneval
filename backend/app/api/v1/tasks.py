import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models import Evaluation, TaskStatus
from app.db.session import get_session
from app.scheduler.celery_app import celery_app

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

    # Revoke Celery task
    if evaluation.celery_task_id:
        celery_app.control.revoke(evaluation.celery_task_id, terminate=True)

    evaluation.status = TaskStatus.CANCELLED
    evaluation.finished_at = datetime.now(timezone.utc)
    session.add(evaluation)
    await session.commit()
    await session.refresh(evaluation)
    return evaluation


# ---------- WebSocket ----------


@router.websocket("/ws/{task_id}/progress")
async def task_progress_ws(websocket: WebSocket, task_id: uuid.UUID):
    await websocket.accept()
    try:
        while True:
            # Wait for a message from client (acts as a poll trigger)
            await websocket.receive_text()

            async with get_session().__anext__() as session:  # type: ignore[union-attr]
                evaluation = await session.get(Evaluation, task_id)
                if not evaluation:
                    await websocket.send_json({"error": "Task not found"})
                    break

                await websocket.send_json(
                    {
                        "id": str(evaluation.id),
                        "status": evaluation.status,
                        "progress": evaluation.progress,
                        "error_message": evaluation.error_message,
                    }
                )

                if evaluation.status in (
                    TaskStatus.COMPLETED,
                    TaskStatus.FAILED,
                    TaskStatus.CANCELLED,
                ):
                    break
    except WebSocketDisconnect:
        pass
