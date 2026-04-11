"""Tests for the /results/throughput endpoint's aggregation logic."""

import unittest
import uuid
from types import SimpleNamespace


class _FakeExec:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return list(self._rows)


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    async def exec(self, _stmt):
        return _FakeExec(self._rows)


def _row(
    task_id,
    task_name,
    model_id,
    model_name,
    concurrency,
    backend,
    avg_latency_ms,
    avg_first_token_ms,
    avg_tokens_generated,
    sample_count,
):
    return SimpleNamespace(
        task_id=task_id,
        task_name=task_name,
        model_id=model_id,
        model_name=model_name,
        concurrency=concurrency,
        execution_backend=backend,
        avg_latency_ms=avg_latency_ms,
        avg_first_token_ms=avg_first_token_ms,
        avg_tokens_generated=avg_tokens_generated,
        sample_count=sample_count,
    )


class TestThroughputEndpoint(unittest.IsolatedAsyncioTestCase):
    async def test_empty_ids_returns_empty_list(self):
        from app.api.v1.results import throughput_comparison

        session = _FakeSession([])
        result = await throughput_comparison(
            task_ids=[], session=session, current_user=None
        )
        self.assertEqual(result, [])

    async def test_single_task_throughput_computation(self):
        from app.api.v1.results import throughput_comparison

        task_id = uuid.uuid4()
        model_id = uuid.uuid4()
        rows = [
            _row(
                task_id=task_id,
                task_name="benchmark-a",
                model_id=model_id,
                model_name="gpt-mock",
                concurrency=4,
                backend="k8s_vllm",
                avg_latency_ms=2000.0,
                avg_first_token_ms=100.0,
                avg_tokens_generated=200.0,
                sample_count=50,
            )
        ]
        session = _FakeSession(rows)
        result = await throughput_comparison(
            task_ids=[task_id], session=session, current_user=None
        )
        self.assertEqual(len(result), 1)
        row = result[0]
        # tokens_per_sec = 200 tokens / 2 seconds = 100
        self.assertAlmostEqual(row["avg_tokens_per_sec"], 100.0)
        self.assertEqual(row["concurrency"], 4)
        self.assertEqual(row["model_name"], "gpt-mock")
        self.assertEqual(row["sample_count"], 50)

    async def test_zero_latency_does_not_divide_by_zero(self):
        from app.api.v1.results import throughput_comparison

        rows = [
            _row(
                task_id=uuid.uuid4(),
                task_name="x",
                model_id=uuid.uuid4(),
                model_name="m",
                concurrency=1,
                backend="external_api",
                avg_latency_ms=0.0,
                avg_first_token_ms=0.0,
                avg_tokens_generated=100.0,
                sample_count=1,
            )
        ]
        session = _FakeSession(rows)
        result = await throughput_comparison(
            task_ids=[uuid.uuid4()], session=session, current_user=None
        )
        self.assertEqual(result[0]["avg_tokens_per_sec"], 0.0)

    async def test_sort_order_by_model_then_concurrency(self):
        from app.api.v1.results import throughput_comparison

        rows = [
            _row(
                task_id=uuid.uuid4(),
                task_name="t1",
                model_id=uuid.uuid4(),
                model_name="B",
                concurrency=8,
                backend="k8s_vllm",
                avg_latency_ms=1000.0,
                avg_first_token_ms=50.0,
                avg_tokens_generated=100.0,
                sample_count=10,
            ),
            _row(
                task_id=uuid.uuid4(),
                task_name="t2",
                model_id=uuid.uuid4(),
                model_name="A",
                concurrency=4,
                backend="k8s_vllm",
                avg_latency_ms=1000.0,
                avg_first_token_ms=50.0,
                avg_tokens_generated=100.0,
                sample_count=10,
            ),
            _row(
                task_id=uuid.uuid4(),
                task_name="t3",
                model_id=uuid.uuid4(),
                model_name="A",
                concurrency=8,
                backend="k8s_vllm",
                avg_latency_ms=1000.0,
                avg_first_token_ms=50.0,
                avg_tokens_generated=100.0,
                sample_count=10,
            ),
        ]
        session = _FakeSession(rows)
        result = await throughput_comparison(
            task_ids=[uuid.uuid4()], session=session, current_user=None
        )
        ordered = [(r["model_name"], r["concurrency"]) for r in result]
        self.assertEqual(ordered, [("A", 4), ("A", 8), ("B", 8)])


if __name__ == "__main__":
    unittest.main()
