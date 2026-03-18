"""Results endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.db.models import Evaluation, EvaluationResult, TaskStatus
from app.security import get_current_user

router = APIRouter()


# Pydantic models
class MetricResult(BaseModel):
    """Metric result."""
    metric: str
    value: float


class ChartDataPoint(BaseModel):
    """Chart data point."""
    name: str
    value: float


class EvaluationResultsResponse(BaseModel):
    """Evaluation results response."""
    evaluation_id: int
    total_samples: int
    metrics: List[MetricResult]
    results: List[dict]


class LeaderboardEntry(BaseModel):
    """Leaderboard entry."""
    model_id: int
    model_name: str
    dataset: str
    metric: str
    value: float
    rank: int


class ColumnChartData(BaseModel):
    """Column chart data."""
    metrics: List[str]
    series: List[dict]  # [{"name": "model1", "data": [0.8, 0.7, ...]}]


class RadarChartData(BaseModel):
    """Radar chart data."""
    metrics: List[str]
    values: List[float]


class LineChartData(BaseModel):
    """Line chart data."""
    x_axis: str
    series: List[dict]


@router.get("/{evaluation_id}/results", response_model=EvaluationResultsResponse)
async def get_evaluation_results(
    evaluation_id: int,
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get evaluation results."""
    # Get evaluation
    result = await db.execute(
        select(Evaluation).where(
            Evaluation.id == evaluation_id,
            Evaluation.user_id == current_user["id"]
        )
    )
    evaluation = result.scalar_one_or_none()

    if not evaluation:
        raise HTTPException(
            status_code=404,
            detail="Evaluation not found"
        )

    # Get results
    results_result = await db.execute(
        select(EvaluationResult).where(
            EvaluationResult.evaluation_id == evaluation_id
        ).limit(limit)
    )
    results = results_result.scalars().all()

    # Calculate metrics
    metrics = []
    if evaluation.metrics:
        for key, value in evaluation.metrics.items():
            metrics.append(MetricResult(metric=key, value=value))
    elif results:
        # Calculate from results
        correct_count = sum(1 for r in results if r.is_correct)
        if correct_count > 0:
            accuracy = correct_count / len(results)
            metrics.append(MetricResult(metric="accuracy", value=accuracy))

    return EvaluationResultsResponse(
        evaluation_id=evaluation_id,
        total_samples=len(results),
        metrics=metrics,
        results=[{
            "id": r.id,
            "prompt": r.prompt[:100] + "..." if len(r.prompt) > 100 else r.prompt,
            "expected_output": r.expected_output,
            "actual_output": r.actual_output,
            "is_correct": r.is_correct,
            "score": r.score,
            "latency_ms": r.latency_ms
        } for r in results]
    )


@router.get("/leaderboard")
async def get_leaderboard(
    dataset: Optional[str] = None,
    metric: str = "accuracy",
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get model leaderboard."""
    # Get all evaluations with results
    query = select(Evaluation).where(
        Evaluation.user_id == current_user["id"],
        Evaluation.status == TaskStatus.COMPLETED
    )
    if dataset:
        query = query.where(Evaluation.dataset_id == int(dataset))

    result = await db.execute(query)
    evaluations = result.scalars().all()

    # Build leaderboard
    leaderboard = []
    for e in evaluations:
        if e.metrics and metric in e.metrics:
            leaderboard.append(LeaderboardEntry(
                model_id=e.model_config_id,
                model_name=f"Model {e.model_config_id}",
                dataset=f"Dataset {e.dataset_id}",
                metric=metric,
                value=e.metrics[metric],
                rank=0
            ))

    # Sort by value and assign ranks
    leaderboard.sort(key=lambda x: x.value, reverse=True)
    for i, entry in enumerate(leaderboard):
        entry.rank = i + 1

    return leaderboard[:limit]


@router.get("/charts/column")
async def get_column_chart(
    model_ids: str,  # comma-separated
    metric_ids: str,  # comma-separated
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get column chart data for multi-model comparison."""
    model_id_list = [int(m) for m in model_ids.split(",")]
    metric_id_list = [m for m in metric_ids.split(",")]

    series = []
    for model_id in model_id_list:
        result = await db.execute(
            select(Evaluation).where(
                Evaluation.model_config_id == model_id,
                Evaluation.dataset_id == dataset_id,
                Evaluation.status == TaskStatus.COMPLETED
            ).order_by(Evaluation.created_at.desc()).limit(1)
        )
        eval_obj = result.scalar_one_or_none()

        data = []
        if eval_obj and eval_obj.metrics:
            for m in metric_id_list:
                value = eval_obj.metrics.get(m, 0)
                data.append(round(value, 4))

        series.append({
            "name": f"Model {model_id}",
            "data": data
        })

    return ColumnChartData(
        metrics=metric_id_list,
        series=series
    )


@router.get("/charts/radar/{model_id}")
async def get_radar_chart(
    model_id: int,
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get radar chart data for single model."""
    # Get latest evaluation for this model-dataset combination
    result = await db.execute(
        select(Evaluation).where(
            Evaluation.model_config_id == model_id,
            Evaluation.dataset_id == dataset_id,
            Evaluation.status == TaskStatus.COMPLETED
        ).order_by(Evaluation.created_at.desc()).limit(1)
    )
    eval_obj = result.scalar_one_or_none()

    if not eval_obj or not eval_obj.metrics:
        return RadarChartData(
            metrics=["accuracy", "precision", "recall", "f1"],
            values=[0.5, 0.5, 0.5, 0.5]
        )

    metrics = list(eval_obj.metrics.keys())[:6]  # Max 6 metrics for radar
    values = [round(eval_obj.metrics.get(m, 0), 4) for m in metrics]

    return RadarChartData(
        metrics=metrics,
        values=values
    )


@router.get("/charts/line/{metric}")
async def get_line_chart(
    metric: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get line chart data for cross-version comparison."""
    # Get all completed evaluations for this metric
    result = await db.execute(
        select(Evaluation).where(
            Evaluation.user_id == current_user["id"],
            Evaluation.status == TaskStatus.COMPLETED
        ).order_by(Evaluation.created_at.asc())
    )
    evaluations = result.scalars().all()

    x_axis = []
    series = {}

    for e in evaluations:
        if e.metrics and metric in e.metrics:
            date = e.created_at.strftime("%Y-%m-%d")
            model_key = f"Model {e.model_config_id}"

            if date not in x_axis:
                x_axis.append(date)

            if model_key not in series:
                series[model_key] = []

            series[model_key].append(round(e.metrics[metric], 4))

    return LineChartData(
        x_axis=metric,
        series=[{"name": k, "data": v} for k, v in series.items()]
    )