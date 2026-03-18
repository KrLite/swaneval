"""In-process task runner for MVP. Runs eval tasks as asyncio background tasks."""

import json
import logging
import random
import time
import uuid
from datetime import datetime
from pathlib import Path

import httpx
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import engine
from app.models.criterion import Criterion
from app.models.dataset import Dataset
from app.models.eval_result import EvalResult
from app.models.eval_task import EvalSubtask, EvalTask, TaskStatus
from app.models.llm_model import LLMModel
from app.services.evaluators import run_criterion

logger = logging.getLogger(__name__)


def _load_dataset_rows(file_path: str) -> list[dict]:
    """Load JSONL/JSON dataset rows. Each row must have 'prompt' and optionally 'expected'."""
    rows = []
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Dataset file not found: {file_path}")
        return rows

    with open(path) as f:
        if file_path.endswith(".json"):
            data = json.load(f)
            rows = data if isinstance(data, list) else [data]
        else:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


async def _call_model(
    client: httpx.AsyncClient,
    model: LLMModel,
    prompt: str,
    params: dict,
) -> tuple[str, float, float, int]:
    """Call an OpenAI-compatible API endpoint.

    Returns (output, latency_ms, first_token_ms, tokens).
    """
    headers = {}
    if model.api_key:
        headers["Authorization"] = f"Bearer {model.api_key}"

    body = {
        "model": model.name,
        "messages": [{"role": "user", "content": prompt}],
        **{k: v for k, v in params.items() if k in ("temperature", "max_tokens", "top_p", "seed")},
    }

    t0 = time.perf_counter()
    first_token_ms = 0.0
    try:
        resp = await client.post(
            model.endpoint_url,
            json=body,
            headers=headers,
            timeout=120.0,
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        resp.raise_for_status()
        data = resp.json()

        # OpenAI-compatible response
        content = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("completion_tokens", 0)
        first_token_ms = latency_ms  # non-streaming, approximate
        return content, latency_ms, first_token_ms, tokens

    except Exception as e:
        latency_ms = (time.perf_counter() - t0) * 1000
        logger.error(f"Model call failed: {e}")
        return f"[ERROR] {e}", latency_ms, 0.0, 0


async def run_task(task_id: uuid.UUID):
    """Execute an evaluation task end-to-end."""
    async with AsyncSession(engine) as session:
        task = await session.get(EvalTask, task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        # Mark running
        task.status = TaskStatus.running
        task.started_at = datetime.utcnow()
        session.add(task)
        await session.commit()

        try:
            model = await session.get(LLMModel, task.model_id)
            if not model:
                raise ValueError(f"Model {task.model_id} not found")

            # Parse IDs
            dataset_ids = [uuid.UUID(d) for d in task.dataset_ids.split(",") if d]
            criteria_ids = [uuid.UUID(c) for c in task.criteria_ids.split(",") if c]
            params = json.loads(task.params_json)

            # Load datasets
            all_rows: list[tuple[uuid.UUID, dict]] = []
            for ds_id in dataset_ids:
                ds = await session.get(Dataset, ds_id)
                if not ds:
                    continue
                rows = _load_dataset_rows(ds.source_uri)
                for row in rows:
                    all_rows.append((ds_id, row))

            # Load criteria
            criteria: list[Criterion] = []
            for c_id in criteria_ids:
                c = await session.get(Criterion, c_id)
                if c:
                    criteria.append(c)

            if not criteria:
                raise ValueError("No valid criteria found")

            # Create subtasks
            subtasks: list[EvalSubtask] = []
            for run_idx in range(task.repeat_count):
                st = EvalSubtask(
                    task_id=task.id,
                    run_index=run_idx,
                    status=TaskStatus.running,
                )
                session.add(st)
                subtasks.append(st)
            await session.commit()
            # Refresh to get IDs
            for st in subtasks:
                await session.refresh(st)

            # Run evaluation
            completed = 0
            async with httpx.AsyncClient() as client:
                for run_idx, subtask in enumerate(subtasks):
                    run_params = dict(params)
                    if task.seed_strategy == "random":
                        run_params["seed"] = random.randint(0, 2**31)
                    elif task.seed_strategy == "fixed":
                        run_params["seed"] = 42 + run_idx

                    for ds_id, row in all_rows:
                        # Check if task was paused/cancelled
                        await session.refresh(task)
                        if task.status in (TaskStatus.paused, TaskStatus.failed):
                            subtask.status = TaskStatus.paused
                            session.add(subtask)
                            await session.commit()
                            return

                        prompt = row.get("prompt", row.get("input", row.get("question", "")))
                        expected = row.get("expected", row.get("output", row.get("answer", "")))

                        output, latency, first_token, tokens = await _call_model(
                            client, model, prompt, run_params
                        )

                        for criterion in criteria:
                            score = run_criterion(
                                criterion.type, criterion.config_json, expected, output
                            )

                            result = EvalResult(
                                task_id=task.id,
                                subtask_id=subtask.id,
                                dataset_id=ds_id,
                                criterion_id=criterion.id,
                                prompt_text=prompt,
                                expected_output=expected,
                                model_output=output,
                                score=score,
                                latency_ms=latency,
                                tokens_generated=tokens,
                                first_token_ms=first_token,
                            )
                            session.add(result)
                            completed += 1

                        subtask.last_completed_index += 1
                        subtask.progress_pct = (
                            subtask.last_completed_index / len(all_rows) * 100
                        )
                        session.add(subtask)
                        await session.commit()

                    subtask.status = TaskStatus.completed
                    subtask.progress_pct = 100.0
                    session.add(subtask)
                    await session.commit()

            task.status = TaskStatus.completed
            task.finished_at = datetime.utcnow()

        except Exception as e:
            logger.exception(f"Task {task_id} failed: {e}")
            task.status = TaskStatus.failed
            # Mark all pending subtasks as failed
            stmt = select(EvalSubtask).where(
                EvalSubtask.task_id == task_id,
                EvalSubtask.status != TaskStatus.completed,
            )
            result = await session.exec(stmt)
            for st in result.all():
                st.status = TaskStatus.failed
                st.error_log = str(e)
                session.add(st)

        session.add(task)
        await session.commit()
