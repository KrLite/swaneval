"""Tests for PrometheusClient — covers success, HTTP errors, timeouts, empty."""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import httpx

from app.services.prometheus_client import (
    PrometheusClient,
    _extract_range_series,
    _extract_single_scalar,
)


class TestPrometheusClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = PrometheusClient("http://prom:9090", timeout=1.0)
        self.now = datetime(2026, 4, 11, 12, 0, 0, tzinfo=timezone.utc)

    async def _patch_get(self, mock_response):
        """Helper to patch httpx.AsyncClient.get with a Mock response."""
        async_client_mock = AsyncMock()
        async_client_mock.__aenter__.return_value = async_client_mock
        async_client_mock.__aexit__.return_value = None
        async_client_mock.get = AsyncMock(return_value=mock_response)
        return patch("httpx.AsyncClient", return_value=async_client_mock)

    async def test_query_instant_success(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [{"metric": {}, "value": [1712822400, "87.5"]}],
            },
        }
        with await self._patch_get(mock_resp):
            val = await self.client.query_instant("DCGM_FI_DEV_GPU_UTIL", self.now)
        self.assertAlmostEqual(val, 87.5)

    async def test_query_instant_http_500(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        with await self._patch_get(mock_resp):
            val = await self.client.query_instant("bad_query", self.now)
        self.assertIsNone(val)

    async def test_query_instant_timeout(self):
        async_client_mock = AsyncMock()
        async_client_mock.__aenter__.return_value = async_client_mock
        async_client_mock.__aexit__.return_value = None
        async_client_mock.get = AsyncMock(
            side_effect=httpx.TimeoutException("timed out")
        )
        with patch("httpx.AsyncClient", return_value=async_client_mock):
            val = await self.client.query_instant("slow_query", self.now)
        self.assertIsNone(val)

    async def test_query_instant_non_json_body(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200

        def _bad_json():
            raise ValueError("not json")

        mock_resp.json = _bad_json
        with await self._patch_get(mock_resp):
            val = await self.client.query_instant("q", self.now)
        self.assertIsNone(val)

    async def test_query_instant_empty_result(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {
            "status": "success",
            "data": {"resultType": "vector", "result": []},
        }
        with await self._patch_get(mock_resp):
            val = await self.client.query_instant("q", self.now)
        self.assertIsNone(val)

    async def test_aggregate_over_window_avg(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {"gpu": "0"},
                        "values": [
                            [1712822400, "80"],
                            [1712822430, "90"],
                            [1712822460, "100"],
                        ],
                    }
                ],
            },
        }
        with await self._patch_get(mock_resp):
            val = await self.client.aggregate_over_window(
                "q", self.now, self.now + timedelta(minutes=1), "avg"
            )
        self.assertAlmostEqual(val, 90.0)

    async def test_aggregate_over_window_max(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {},
                        "values": [[1712822400, "1024"], [1712822430, "2048"]],
                    }
                ],
            },
        }
        with await self._patch_get(mock_resp):
            val = await self.client.aggregate_over_window(
                "q", self.now, self.now + timedelta(minutes=1), "max"
            )
        self.assertAlmostEqual(val, 2048.0)

    async def test_aggregate_over_window_no_samples(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {
            "status": "success",
            "data": {"resultType": "matrix", "result": []},
        }
        with await self._patch_get(mock_resp):
            val = await self.client.aggregate_over_window(
                "q", self.now, self.now + timedelta(minutes=1), "avg"
            )
        self.assertIsNone(val)

    async def test_prometheus_query_error_status(self):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json = lambda: {"status": "error", "error": "bad query"}
        with await self._patch_get(mock_resp):
            val = await self.client.query_instant("q", self.now)
        self.assertIsNone(val)


class TestExtractHelpers(unittest.TestCase):
    def test_extract_single_scalar_vector(self):
        data = {
            "resultType": "vector",
            "result": [{"value": [1712822400, "42.5"]}],
        }
        self.assertAlmostEqual(_extract_single_scalar(data), 42.5)

    def test_extract_single_scalar_empty(self):
        self.assertIsNone(_extract_single_scalar({"resultType": "vector", "result": []}))

    def test_extract_single_scalar_malformed_value(self):
        data = {
            "resultType": "vector",
            "result": [{"value": [1712822400, "NaNish"]}],
        }
        self.assertIsNone(_extract_single_scalar(data))

    def test_extract_range_series_flattens(self):
        data = {
            "resultType": "matrix",
            "result": [
                {"values": [[1712822400, "1"], [1712822430, "2"]]},
                {"values": [[1712822400, "3"]]},
            ],
        }
        series = _extract_range_series(data)
        self.assertEqual(len(series), 3)
        self.assertEqual([v for _, v in series], [1.0, 2.0, 3.0])

    def test_extract_range_series_skips_malformed(self):
        data = {
            "resultType": "matrix",
            "result": [{"values": [[1712822400, "not-a-number"], [1712822430, "5"]]}],
        }
        series = _extract_range_series(data)
        self.assertEqual(len(series), 1)
        self.assertAlmostEqual(series[0][1], 5.0)


if __name__ == "__main__":
    unittest.main()
