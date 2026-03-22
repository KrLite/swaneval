"""Independent task worker process.

Usage: uv run python -m app.worker

Connects to Redis queue, dequeues tasks, and executes them.
Does NOT run in the API process.
"""

import asyncio
import logging
import os
import signal
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] worker: %(message)s",
)
logger = logging.getLogger(__name__)

WORKER_ID = f"worker-{os.getpid()}-{uuid.uuid4().hex[:8]}"
_shutdown = False


def _handle_signal(sig, frame):
    global _shutdown
    logger.info("Received signal %s, shutting down gracefully...", sig)
    _shutdown = True


async def _run_k8s_vllm_task(task_id: str, cluster_id: str | None) -> None:
    """Deploy vLLM on K8s, run the task against it, then clean up."""
    from sqlmodel.ext.asyncio.session import AsyncSession

    from app.database import engine
    from app.models.compute_cluster import ComputeCluster
    from app.models.eval_task import EvalTask
    from app.models.llm_model import LLMModel
    from app.services.k8s_vllm import cleanup_vllm, full_vllm_lifecycle
    from app.services.task_runner import run_task

    async with AsyncSession(engine) as session:
        task = await session.get(EvalTask, uuid.UUID(task_id))
        if not task:
            raise ValueError(f"Task {task_id} not found")

        # Resolve cluster
        cid = cluster_id or (str(task.cluster_id) if task.cluster_id else None)
        if not cid:
            raise ValueError(
                f"Task {task_id} uses k8s_vllm backend but has no cluster_id"
            )
        cluster = await session.get(ComputeCluster, uuid.UUID(cid))
        if not cluster:
            raise ValueError(f"Cluster {cid} not found")

        model = await session.get(LLMModel, task.model_id)
        if not model:
            raise ValueError(f"Model {task.model_id} not found")

        # Parse resource config
        import json
        resource_cfg = json.loads(task.resource_config) if task.resource_config else {}
        gpu_count = resource_cfg.get("gpu_count", cluster.gpu_count or 1)
        gpu_type = resource_cfg.get("gpu_type", cluster.gpu_type or "")
        memory_gb = resource_cfg.get("memory_gb", 40)
        hf_model_id = resource_cfg.get("hf_model_id", model.model_name or model.name)

    # Deploy vLLM and get endpoint
    endpoint, dep_name = await full_vllm_lifecycle(
        kubeconfig_encrypted=cluster.kubeconfig_encrypted,
        namespace=cluster.namespace,
        model_name=model.name,
        hf_model_id=hf_model_id,
        gpu_count=gpu_count,
        gpu_type=gpu_type,
        memory_gb=memory_gb,
    )
    logger.info(
        "Task %s: vLLM deployed as %s, endpoint=%s",
        task_id, dep_name, endpoint,
    )

    try:
        await run_task(uuid.UUID(task_id), endpoint_override=endpoint)
    finally:
        logger.info("Task %s: cleaning up vLLM deployment %s", task_id, dep_name)
        await cleanup_vllm(
            kubeconfig_encrypted=cluster.kubeconfig_encrypted,
            namespace=cluster.namespace,
            deployment_name=dep_name,
        )


async def run_worker():
    """Main worker loop: dequeue tasks and execute them."""
    from app.services.task_queue import (
        dequeue_task,
        mark_done,
        mark_running,
        register_worker,
        unregister_worker,
        update_worker_status,
    )
    from app.services.task_runner import run_task

    await register_worker(WORKER_ID)
    logger.info("Worker %s started, waiting for tasks...", WORKER_ID)

    try:
        while not _shutdown:
            await update_worker_status(WORKER_ID, "idle")
            job = await dequeue_task(timeout=5)
            if job is None:
                continue

            task_id = job["task_id"]
            backend = job.get("execution_backend", "external_api")
            cluster_id = job.get("cluster_id")
            logger.info(
                "Worker %s picked up task %s (backend=%s, cluster=%s)",
                WORKER_ID, task_id, backend, cluster_id,
            )

            await update_worker_status(WORKER_ID, "busy")
            await mark_running(task_id, WORKER_ID)

            try:
                if backend == "k8s_vllm":
                    await _run_k8s_vllm_task(task_id, cluster_id)
                else:
                    await run_task(uuid.UUID(task_id))
                logger.info("Task %s completed", task_id)
            except Exception:
                logger.exception("Task %s failed with exception", task_id)
            finally:
                await mark_done(task_id)

    finally:
        await update_worker_status(WORKER_ID, "stopping")
        await unregister_worker(WORKER_ID)
        logger.info("Worker %s stopped", WORKER_ID)


def main():
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
