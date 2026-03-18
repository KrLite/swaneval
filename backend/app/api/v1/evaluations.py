import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models import Dataset, Evaluation, EvaluationDatasetLink, MLModel, TaskStatus
from app.db.session import get_session

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


# ---------- Schemas ----------


class EvaluationCreate(BaseModel):
    name: str
    model_id: uuid.UUID
    dataset_ids: list[uuid.UUID]
    temperature: float = 0.0
    max_tokens: int = 2048
    few_shot: int = 0
    batch_size: int = 1
    extra_params: dict | None = None


class EvaluationRead(BaseModel):
    id: uuid.UUID
    name: str
    model_id: uuid.UUID
    status: TaskStatus
    celery_task_id: str | None
    temperature: float
    max_tokens: int
    few_shot: int
    batch_size: int
    extra_params: dict | None
    progress: float
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime
    dataset_ids: list[uuid.UUID] = []

    model_config = {"from_attributes": True}


# ---------- Helpers ----------


def _eval_to_read(evaluation: Evaluation) -> EvaluationRead:
    return EvaluationRead(
        **evaluation.model_dump(),
        dataset_ids=[d.id for d in evaluation.datasets],
    )


# ---------- Endpoints ----------


@router.post("", response_model=EvaluationRead, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    payload: EvaluationCreate,
    session: AsyncSession = Depends(get_session),
):
    # Validate model exists
    model = await session.get(MLModel, payload.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Validate datasets exist
    datasets: list[Dataset] = []
    for ds_id in payload.dataset_ids:
        ds = await session.get(Dataset, ds_id)
        if not ds:
            raise HTTPException(status_code=404, detail=f"Dataset {ds_id} not found")
        datasets.append(ds)

    evaluation = Evaluation(
        name=payload.name,
        model_id=payload.model_id,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        few_shot=payload.few_shot,
        batch_size=payload.batch_size,
        extra_params=payload.extra_params,
    )
    session.add(evaluation)
    await session.flush()

    # Create link records
    for ds in datasets:
        link = EvaluationDatasetLink(evaluation_id=evaluation.id, dataset_id=ds.id)
        session.add(link)

    await session.commit()
    await session.refresh(evaluation)

    # TODO: dispatch Celery task when task queue is integrated
    return _eval_to_read(evaluation)


@router.get("", response_model=list[EvaluationRead])
async def list_evaluations(
    skip: int = 0,
    limit: int = 50,
    status_filter: TaskStatus | None = None,
    session: AsyncSession = Depends(get_session),
):
    query = select(Evaluation).order_by(Evaluation.created_at.desc())  # type: ignore[attr-defined]
    if status_filter:
        query = query.where(Evaluation.status == status_filter)
    query = query.offset(skip).limit(limit)
    result = await session.exec(query)
    evaluations = result.all()
    return [_eval_to_read(e) for e in evaluations]


@router.get("/{evaluation_id}", response_model=EvaluationRead)
async def get_evaluation(
    evaluation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    evaluation = await session.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return _eval_to_read(evaluation)
