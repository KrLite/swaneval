import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.models import Evaluation, EvaluationResult, MLModel, TaskStatus
from app.db.session import get_session

router = APIRouter(prefix="/results", tags=["results"])


# ---------- Schemas ----------


class ResultRead(BaseModel):
    id: uuid.UUID
    evaluation_id: uuid.UUID
    dataset_name: str
    metric_name: str
    metric_value: float
    details: dict | None

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    model_name: str
    model_id: uuid.UUID
    scores: dict[str, float]
    average: float


class ChartDataPoint(BaseModel):
    label: str
    values: dict[str, float]


# ---------- Endpoints ----------


@router.get("/{evaluation_id}", response_model=list[ResultRead])
async def get_results(
    evaluation_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    evaluation = await session.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    result = await session.exec(
        select(EvaluationResult).where(EvaluationResult.evaluation_id == evaluation_id)
    )
    return result.all()


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    metric: str = Query(default="accuracy"),
    session: AsyncSession = Depends(get_session),
):
    evals_result = await session.exec(
        select(Evaluation).where(Evaluation.status == TaskStatus.COMPLETED)
    )
    evaluations = evals_result.all()

    entries: dict[uuid.UUID, dict[str, float]] = defaultdict(dict)
    model_names: dict[uuid.UUID, str] = {}

    for ev in evaluations:
        model = await session.get(MLModel, ev.model_id)
        if not model:
            continue
        model_names[model.id] = model.name

        results = await session.exec(
            select(EvaluationResult).where(
                EvaluationResult.evaluation_id == ev.id,
                EvaluationResult.metric_name == metric,
            )
        )
        for r in results.all():
            entries[model.id][r.dataset_name] = r.metric_value

    leaderboard = []
    for model_id, scores in entries.items():
        avg = sum(scores.values()) / len(scores) if scores else 0.0
        leaderboard.append(
            LeaderboardEntry(
                model_name=model_names[model_id],
                model_id=model_id,
                scores=scores,
                average=avg,
            )
        )

    leaderboard.sort(key=lambda x: x.average, reverse=True)
    return leaderboard


@router.get("/charts", response_model=list[ChartDataPoint])
async def get_chart_data(
    evaluation_ids: list[uuid.UUID] = Query(default=[]),
    metric: str = Query(default="accuracy"),
    session: AsyncSession = Depends(get_session),
):
    if not evaluation_ids:
        return []

    data_by_dataset: dict[str, dict[str, float]] = defaultdict(dict)

    for eval_id in evaluation_ids:
        ev = await session.get(Evaluation, eval_id)
        if not ev:
            continue
        model = await session.get(MLModel, ev.model_id)
        if not model:
            continue

        results = await session.exec(
            select(EvaluationResult).where(
                EvaluationResult.evaluation_id == eval_id,
                EvaluationResult.metric_name == metric,
            )
        )
        for r in results.all():
            data_by_dataset[r.dataset_name][model.name] = r.metric_value

    return [
        ChartDataPoint(label=ds_name, values=values)
        for ds_name, values in data_by_dataset.items()
    ]
