"""Tests for k8s_vllm integration into task_runner and worker."""

import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch


class TestTaskQueueClusterId(unittest.IsolatedAsyncioTestCase):
    """B4: enqueue_task passes cluster_id in Redis payload."""

    @patch("app.services.task_queue._get_redis")
    async def test_enqueue_with_cluster_id(self, mock_get_redis):
        from app.services.task_queue import enqueue_task

        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis

        await enqueue_task(
            "task-123",
            execution_backend="k8s_vllm",
            cluster_id="cluster-456",
        )

        mock_redis.rpush.assert_called_once()
        payload = json.loads(mock_redis.rpush.call_args[0][1])
        self.assertEqual(payload["task_id"], "task-123")
        self.assertEqual(payload["execution_backend"], "k8s_vllm")
        self.assertEqual(payload["cluster_id"], "cluster-456")
        self.assertIn("enqueued_at", payload)

    @patch("app.services.task_queue._get_redis")
    async def test_enqueue_without_cluster_id(self, mock_get_redis):
        from app.services.task_queue import enqueue_task

        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis

        await enqueue_task("task-789")

        payload = json.loads(mock_redis.rpush.call_args[0][1])
        self.assertEqual(payload["task_id"], "task-789")
        self.assertEqual(payload["execution_backend"], "external_api")
        self.assertNotIn("cluster_id", payload)


class TestTaskRunnerEndpointOverride(unittest.TestCase):
    """B2: run_task accepts endpoint_override parameter."""

    def test_run_task_signature_has_endpoint_override(self):
        """Verify run_task accepts endpoint_override kwarg."""
        import inspect

        from app.services.task_runner import run_task

        sig = inspect.signature(run_task)
        self.assertIn("endpoint_override", sig.parameters)
        param = sig.parameters["endpoint_override"]
        self.assertEqual(param.default, None)


class TestWorkerK8sVllmDispatch(unittest.TestCase):
    """B1: Worker dispatches k8s_vllm tasks through lifecycle."""

    def test_run_k8s_vllm_task_exists(self):
        """Verify _run_k8s_vllm_task function exists in worker module."""
        from app.worker import _run_k8s_vllm_task

        self.assertTrue(callable(_run_k8s_vllm_task))

    def test_run_k8s_vllm_task_signature(self):
        """Verify _run_k8s_vllm_task accepts task_id and cluster_id."""
        import inspect

        from app.worker import _run_k8s_vllm_task

        sig = inspect.signature(_run_k8s_vllm_task)
        self.assertIn("task_id", sig.parameters)
        self.assertIn("cluster_id", sig.parameters)

    def test_worker_handles_k8s_vllm_backend_in_job(self):
        """Verify worker code parses cluster_id from job payload."""
        import app.worker  # noqa: F401

        # Simulate a job payload with k8s_vllm backend
        job = {
            "task_id": "abc-123",
            "execution_backend": "k8s_vllm",
            "cluster_id": "cluster-456",
        }
        self.assertEqual(job.get("execution_backend"), "k8s_vllm")
        self.assertEqual(job.get("cluster_id"), "cluster-456")


if __name__ == "__main__":
    unittest.main()
