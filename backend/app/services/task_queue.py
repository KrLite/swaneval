"""Redis-based persistent task queue.

API process enqueues tasks; independent worker processes dequeue and execute.
"""

import json
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

QUEUE_KEY = "swaneval:task_queue"
RUNNING_KEY = "swaneval:running_tasks"
WORKER_KEY = "swaneval:workers"


_pool: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.REDIS_URL, decode_responses=True,
            max_connections=10,
        )
    return _pool


async def close_pool() -> None:
    """Close the connection pool (call on shutdown)."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


async def enqueue_task(task_id: str, execution_backend: str = "external_api") -> None:
    """Push a task onto the persistent queue."""
    r = _get_redis()
    payload = json.dumps({
        "task_id": task_id,
        "execution_backend": execution_backend,
        "enqueued_at": datetime.now(timezone.utc).isoformat(),
    })
    await r.rpush(QUEUE_KEY, payload)
    logger.info("Task %s enqueued (backend=%s)", task_id, execution_backend)


async def dequeue_task(timeout: int = 5) -> dict | None:
    """Blocking pop from the task queue. Returns None on timeout."""
    r = _get_redis()
    result = await r.blpop(QUEUE_KEY, timeout=timeout)
    if result is None:
        return None
    _, payload = result
    return json.loads(payload)


async def mark_running(task_id: str, worker_id: str) -> None:
    """Track that a task is being executed by a worker."""
    r = _get_redis()
    await r.hset(RUNNING_KEY, task_id, json.dumps({
        "worker_id": worker_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }))


async def mark_done(task_id: str) -> None:
    """Remove task from the running set."""
    r = _get_redis()
    await r.hdel(RUNNING_KEY, task_id)


async def get_queue_status() -> dict:
    """Return queue metrics: pending, running, workers."""
    r = _get_redis()
    pending = await r.llen(QUEUE_KEY)
    running = await r.hlen(RUNNING_KEY)
    workers = await r.hlen(WORKER_KEY)
    return {"pending": pending, "running": running, "workers": workers}


async def register_worker(worker_id: str) -> None:
    """Register a worker as alive."""
    r = _get_redis()
    await r.hset(WORKER_KEY, worker_id, json.dumps({
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "status": "idle",
    }))


async def update_worker_status(worker_id: str, status: str) -> None:
    """Update worker status (idle, busy, stopping)."""
    r = _get_redis()
    await r.hset(WORKER_KEY, worker_id, json.dumps({
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }))


async def unregister_worker(worker_id: str) -> None:
    """Remove worker from the registry."""
    r = _get_redis()
    await r.hdel(WORKER_KEY, worker_id)


async def _safe_update_worker_status(worker_id: str, status: str) -> None:
    """update_worker_status wrapper that tolerates Redis failures."""
    try:
        await update_worker_status(worker_id, status)
    except Exception:
        logger.debug(
            "Could not update worker %s status to '%s' (Redis unavailable)",
            worker_id, status,
        )


async def embedded_worker_loop() -> None:
    """In-process worker loop for development / single-server deployments.

    Runs as an asyncio task inside the API process. Dequeues tasks from
    Redis and executes them without needing a separate worker process.
    """
    import asyncio
    import uuid as _uuid

    from app.services.task_runner import run_task

    worker_id = f"embedded-{_uuid.uuid4().hex[:8]}"
    await register_worker(worker_id)
    logger.info("Embedded worker %s started", worker_id)

    redis_fail_count = 0
    _MAX_REDIS_FAILURES = 10

    try:
        while True:
            await _safe_update_worker_status(worker_id, "idle")
            try:
                job = await dequeue_task(timeout=3)
                redis_fail_count = 0  # Reset on success
            except Exception:
                redis_fail_count += 1
                if redis_fail_count >= _MAX_REDIS_FAILURES:
                    logger.error(
                        "Embedded worker %s: Redis unreachable for %d consecutive attempts",
                        worker_id, redis_fail_count,
                    )
                    await _safe_update_worker_status(worker_id, "redis_unhealthy")
                else:
                    logger.warning(
                        "Embedded worker %s: Redis connection error (attempt %d)",
                        worker_id, redis_fail_count,
                    )
                await asyncio.sleep(5)
                continue

            if job is None:
                continue

            task_id = job["task_id"]
            logger.info("Embedded worker picked up task %s", task_id)
            await _safe_update_worker_status(worker_id, "busy")
            await mark_running(task_id, worker_id)

            try:
                await run_task(_uuid.UUID(task_id))
            except Exception:
                logger.exception("Embedded worker: task %s failed", task_id)
                await ensure_task_failed_in_db(task_id)
            finally:
                await mark_done(task_id)
    except asyncio.CancelledError:
        pass  # Normal shutdown
    finally:
        await unregister_worker(worker_id)
        logger.info("Embedded worker %s stopped", worker_id)


async def ensure_task_failed_in_db(task_id: str) -> None:
    """Defensive: ensure task status is 'failed' in DB if not already terminal.

    Shared by embedded_worker_loop and the standalone worker process.
    """
    try:
        import uuid as _uuid

        from sqlmodel.ext.asyncio.session import AsyncSession

        from app.database import engine
        from app.models.eval_task import EvalTask, TaskStatus

        async with AsyncSession(engine) as session:
            task = await session.get(EvalTask, _uuid.UUID(task_id))
            if task and task.status not in (TaskStatus.failed, TaskStatus.completed):
                task.status = TaskStatus.failed
                task.finished_at = datetime.now(timezone.utc)
                session.add(task)
                await session.commit()
                logger.info("Task %s defensively marked as FAILED in DB", task_id)
    except Exception:
        logger.exception("Failed to defensively update task %s status", task_id)
