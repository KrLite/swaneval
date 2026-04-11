"""Tests for _collect_gpu_metrics — the k8s path of report_generator.

Covers the four branches we care about for fail-soft GPU metric collection:
no cluster link, no Prometheus URL configured, successful query, query
returns all Nones.
"""

import unittest
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.services.report_generator import _collect_gpu_metrics


class _FakeSession:
    """Async session stub. `_collect_gpu_metrics` only calls `get(ComputeCluster, id)`,
    so we key only by the cluster id since the test passes a single cluster."""

    def __init__(self, cluster=None):
        self._cluster = cluster

    async def get(self, _cls, key):
        if self._cluster is not None and self._cluster.id == key:
            return self._cluster
        return None


def _make_task(cluster_id=None, gpu_ids="0,1", has_window=True):
    task = SimpleNamespace()
    task.id = uuid.uuid4()
    task.cluster_id = cluster_id
    task.gpu_ids = gpu_ids
    if has_window:
        task.started_at = datetime(2026, 4, 11, 12, 0, 0, tzinfo=timezone.utc)
        task.finished_at = task.started_at + timedelta(minutes=10)
    else:
        task.started_at = None
        task.finished_at = None
    return task


def _make_cluster(prometheus_url=""):
    cluster = SimpleNamespace()
    cluster.id = uuid.uuid4()
    cluster.prometheus_url = prometheus_url
    cluster.dcgm_namespace = "gpu-operator"
    return cluster


class TestCollectGpuMetrics(unittest.IsolatedAsyncioTestCase):
    async def test_no_cluster_id_returns_note(self):
        task = _make_task(cluster_id=None)
        session = _FakeSession()
        result = await _collect_gpu_metrics(task, session)
        self.assertIsNone(result["gpu_utilization_pct"])
        self.assertIn("未关联计算集群", result["metrics_note"])

    async def test_cluster_missing_returns_note(self):
        task = _make_task(cluster_id=uuid.uuid4())
        session = _FakeSession()
        result = await _collect_gpu_metrics(task, session)
        self.assertIsNone(result["gpu_utilization_pct"])
        self.assertIn("集群记录缺失", result["metrics_note"])

    async def test_prometheus_url_not_configured(self):
        cluster = _make_cluster(prometheus_url="")
        task = _make_task(cluster_id=cluster.id)
        session = _FakeSession(cluster)
        result = await _collect_gpu_metrics(task, session)
        self.assertIsNone(result["gpu_utilization_pct"])
        self.assertIsNone(result["gpu_memory_peak_mb"])
        self.assertIsNone(result["gpu_power_watts"])
        self.assertIn("未配置 Prometheus URL", result["metrics_note"])

    async def test_missing_time_window(self):
        cluster = _make_cluster(prometheus_url="http://prom:9090")
        task = _make_task(cluster_id=cluster.id, has_window=False)
        session = _FakeSession(cluster)
        result = await _collect_gpu_metrics(task, session)
        self.assertIsNone(result["gpu_utilization_pct"])
        self.assertIn("时间窗", result["metrics_note"])

    async def test_successful_query_fills_all_three(self):
        cluster = _make_cluster(prometheus_url="http://prom:9090")
        task = _make_task(cluster_id=cluster.id)
        session = _FakeSession(cluster)

        mock_client = AsyncMock()
        mock_client.aggregate_over_window = AsyncMock(
            side_effect=[85.3, 18432.5, 245.7]
        )
        with patch(
            "app.services.report_generator.PrometheusClient",
            return_value=mock_client,
        ):
            result = await _collect_gpu_metrics(task, session)

        self.assertAlmostEqual(result["gpu_utilization_pct"], 85.3)
        self.assertAlmostEqual(result["gpu_memory_peak_mb"], 18432.5)
        self.assertAlmostEqual(result["gpu_power_watts"], 245.7)
        self.assertIn("DCGM", result["metrics_note"])

    async def test_query_all_none_returns_failure_note(self):
        cluster = _make_cluster(prometheus_url="http://prom:9090")
        task = _make_task(cluster_id=cluster.id)
        session = _FakeSession(cluster)

        mock_client = AsyncMock()
        mock_client.aggregate_over_window = AsyncMock(
            side_effect=[None, None, None]
        )
        with patch(
            "app.services.report_generator.PrometheusClient",
            return_value=mock_client,
        ):
            result = await _collect_gpu_metrics(task, session)

        self.assertIsNone(result["gpu_utilization_pct"])
        self.assertIsNone(result["gpu_memory_peak_mb"])
        self.assertIsNone(result["gpu_power_watts"])
        self.assertIn("未返回数据", result["metrics_note"])

    async def test_query_partial_success(self):
        cluster = _make_cluster(prometheus_url="http://prom:9090")
        task = _make_task(cluster_id=cluster.id)
        session = _FakeSession(cluster)

        mock_client = AsyncMock()
        mock_client.aggregate_over_window = AsyncMock(
            side_effect=[85.0, None, 240.0]
        )
        with patch(
            "app.services.report_generator.PrometheusClient",
            return_value=mock_client,
        ):
            result = await _collect_gpu_metrics(task, session)

        self.assertAlmostEqual(result["gpu_utilization_pct"], 85.0)
        self.assertIsNone(result["gpu_memory_peak_mb"])
        self.assertAlmostEqual(result["gpu_power_watts"], 240.0)
        self.assertIn("DCGM", result["metrics_note"])


if __name__ == "__main__":
    unittest.main()
