"""Report generator service for SwanEVAL."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.criterion import Criterion
from app.models.eval_result import EvalResult
from app.models.eval_task import EvalTask
from app.models.llm_model import LLMModel


async def generate_performance_report(task_id: uuid.UUID, session: AsyncSession) -> dict:
    """性能报告: scores per criterion, strengths/weaknesses."""
    task = await session.get(EvalTask, task_id)
    if not task:
        raise ValueError("Task not found")
    model = await session.get(LLMModel, task.model_id)

    # Aggregate per criterion
    stmt = (
        select(
            Criterion.name.label("criterion_name"),
            sa_func.avg(EvalResult.score).label("avg_score"),
            sa_func.min(EvalResult.score).label("min_score"),
            sa_func.max(EvalResult.score).label("max_score"),
            sa_func.count(EvalResult.id).label("count"),
            sa_func.avg(EvalResult.latency_ms).label("avg_latency_ms"),
        )
        .join(Criterion, EvalResult.criterion_id == Criterion.id)
        .where(EvalResult.task_id == task_id)
        .group_by(Criterion.name)
    )
    result = await session.exec(stmt)
    criteria_stats = [
        {
            "criterion": r.criterion_name,
            "avg_score": round(r.avg_score, 4),
            "min_score": round(r.min_score, 4),
            "max_score": round(r.max_score, 4),
            "sample_count": r.count,
            "avg_latency_ms": round(r.avg_latency_ms, 2),
        }
        for r in result.all()
    ]

    # Overall stats
    overall_stmt = select(
        sa_func.avg(EvalResult.score),
        sa_func.count(EvalResult.id),
    ).where(EvalResult.task_id == task_id)
    overall = (await session.exec(overall_stmt)).one()

    return {
        "type": "performance",
        "title": f"性能评测报告 — {task.name}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_name": task.name,
        "model_name": model.name if model else "Unknown",
        "overall_score": (round(overall[0], 4) if overall[0] else 0),
        "total_samples": overall[1],
        "criteria_breakdown": sorted(
            criteria_stats,
            key=lambda x: x["avg_score"],
            reverse=True,
        ),
    }


async def generate_safety_report(task_id: uuid.UUID, session: AsyncSession) -> dict:
    """安全报告: error cases, risk ratings."""
    task = await session.get(EvalTask, task_id)
    if not task:
        raise ValueError("Task not found")
    model = await session.get(LLMModel, task.model_id)

    # Count total
    total_stmt = select(sa_func.count(EvalResult.id)).where(EvalResult.task_id == task_id)
    total = (await session.exec(total_stmt)).one()

    # Count model wrong answers (is_valid=True, score < 1.0)
    wrong_stmt = select(sa_func.count(EvalResult.id)).where(
        EvalResult.task_id == task_id,
        EvalResult.score < 1.0,
        EvalResult.is_valid == True,  # noqa: E712
    )
    wrong_count = (await session.exec(wrong_stmt)).one()

    # Count execution errors (is_valid=False)
    exec_error_stmt = select(sa_func.count(EvalResult.id)).where(
        EvalResult.task_id == task_id,
        EvalResult.is_valid == False,  # noqa: E712
    )
    exec_error_count = (await session.exec(exec_error_stmt)).one()

    error_count = wrong_count

    # Get worst error cases — only model wrong answers (not execution errors)
    cases_stmt = (
        select(EvalResult)
        .where(
            EvalResult.task_id == task_id,
            EvalResult.score < 1.0,
            EvalResult.is_valid == True,  # noqa: E712
        )
        .order_by(EvalResult.score.asc())
        .limit(20)
    )
    cases = (await session.exec(cases_stmt)).all()

    error_rate = error_count / max(total, 1)
    if error_rate < 0.1:
        risk_level = "低风险"
    elif error_rate < 0.3:
        risk_level = "中风险"
    else:
        risk_level = "高风险"

    return {
        "type": "safety",
        "title": f"安全评测报告 — {task.name}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_name": task.name,
        "model_name": model.name if model else "Unknown",
        "total_samples": total,
        "wrong_answer_count": wrong_count,
        "execution_error_count": exec_error_count,
        "error_count": error_count,  # backward compat
        "error_rate": round(error_rate, 4),
        "risk_level": risk_level,
        "error_cases": [
            {
                "prompt": c.prompt_text,
                "expected": c.expected_output,
                "actual": c.model_output,
                "score": round(c.score, 4),
            }
            for c in cases
        ],
    }


async def generate_cost_report(task_id: uuid.UUID, session: AsyncSession) -> dict:
    """成本报告: latency, throughput, token stats."""
    task = await session.get(EvalTask, task_id)
    if not task:
        raise ValueError("Task not found")
    model = await session.get(LLMModel, task.model_id)

    stmt = select(
        sa_func.avg(EvalResult.latency_ms).label("avg_latency"),
        sa_func.min(EvalResult.latency_ms).label("min_latency"),
        sa_func.max(EvalResult.latency_ms).label("max_latency"),
        sa_func.avg(EvalResult.first_token_ms).label("avg_first_token"),
        sa_func.avg(EvalResult.tokens_generated).label("avg_tokens"),
        sa_func.sum(EvalResult.tokens_generated).label("total_tokens"),
        sa_func.count(EvalResult.id).label("total_samples"),
    ).where(EvalResult.task_id == task_id)
    r = (await session.exec(stmt)).one()

    # Duration
    duration_sec = 0.0
    if task.started_at and task.finished_at:
        duration_sec = (task.finished_at - task.started_at).total_seconds()

    throughput = (r.total_tokens or 0) / max(duration_sec, 1)

    # Determine execution backend for cost metrics split
    execution_backend = (
        task.execution_backend if hasattr(task, "execution_backend") else "external_api"
    )

    base_report = {
        "type": "cost",
        "title": f"成本评测报告 — {task.name}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_name": task.name,
        "model_name": model.name if model else "Unknown",
        "execution_backend": execution_backend,
        "total_samples": r.total_samples,
        "avg_latency_ms": round(r.avg_latency or 0, 2),
        "min_latency_ms": round(r.min_latency or 0, 2),
        "max_latency_ms": round(r.max_latency or 0, 2),
        "avg_first_token_ms": round(r.avg_first_token or 0, 2),
        "avg_tokens_per_response": round(r.avg_tokens or 0, 1),
        "total_tokens": r.total_tokens or 0,
        "duration_seconds": round(duration_sec, 1),
        "throughput_tokens_per_sec": round(throughput, 1),
    }

    if execution_backend == "k8s_vllm":
        # K8s/vLLM: add GPU-specific fields (populated from DCGM exporter)
        base_report.update(
            {
                "gpu_ids": task.gpu_ids or "",
                "gpu_utilization_pct": None,
                "gpu_memory_peak_mb": None,
                "gpu_power_watts": None,
                "metrics_note": "GPU 指标需通过 Prometheus + DCGM Exporter 采集",
            }
        )
    else:
        # API model: no GPU metrics
        base_report.update(
            {
                "gpu_ids": task.gpu_ids if task.gpu_ids else "N/A (API 模型)",
                "estimated_cost_usd": None,
            }
        )

    return base_report


async def generate_value_report(task_id: uuid.UUID, session: AsyncSession) -> dict:
    """性价比报告: combines performance + cost data."""
    perf = await generate_performance_report(task_id, session)
    cost = await generate_cost_report(task_id, session)

    # Value score: performance per unit of latency
    avg_score = perf["overall_score"]
    avg_latency = cost["avg_latency_ms"]
    value_index = round(avg_score / max(avg_latency / 1000, 0.001), 4)

    return {
        "type": "value",
        "title": f"性价比评测报告 — {perf['task_name']}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_name": perf["task_name"],
        "model_name": perf["model_name"],
        "overall_score": avg_score,
        "avg_latency_ms": avg_latency,
        "throughput_tokens_per_sec": cost["throughput_tokens_per_sec"],
        "total_tokens": cost["total_tokens"],
        "value_index": value_index,
        "criteria_breakdown": perf["criteria_breakdown"],
        "gpu_ids": cost["gpu_ids"],
    }
